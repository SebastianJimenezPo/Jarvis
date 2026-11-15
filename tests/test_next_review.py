import pytest
from jarvis.next.contracts import ActionChange, Decision, ProviderReply, Span, ToolCall
from jarvis.next.engine import NextEngine
from jarvis.next.providers import FakeProvider


def decision(req, op='create_plan', **fields):
    return Decision(operation=op, plan_id=req.context.plan_id, expected_revision=req.context.revision,
        evidence=Span(start=0, end=len(req.text)), temporal='now', **fields)


def app(req, target='steam'):
    return ToolCall(tool='applications.open', target=target, evidence=Span(start=0, end=len(req.text)))


def make(responder, **options):
    provider = FakeProvider(lambda req, _: ProviderReply(decision_json=responder(req).model_dump_json()))
    engine = NextEngine(provider, review_enabled=True, **options)
    engine.begin_session('cli')
    return engine, provider


def confirm(engine, result):
    assert result.review is not None and result.disposition == 'withheld'
    assert not result.results
    return engine.confirm(result.review.review_id)


@pytest.mark.parametrize('text,reason', [
    ('Esta tarde deja el audio en silencio.', 'deferred_time'),
    ('Cuando termine la partida, inicia Steam.', 'deferred_time'),
    ('En cuanto termine, inicia Steam.', 'deferred_time'),
    ('Inicia Steam en 20 minutos.', 'deferred_time'),
    ('El ejemplo es «Pausa la música».', 'quoted_command'),
    ('Te leo "Abre Chrome".', 'quoted_command'),
    ("La etiqueta dice 'Silencia el audio'.", 'quoted_command'),
])
def test_review_refuses_explicit_future_and_quoted_commands_even_if_provider_claims_now(text, reason):
    e, _ = make(lambda req: decision(req, actions=(app(req),)))
    try:
        before = e.manager.snapshot()
        result = e.interpret(text)
        assert result.policy_reason == reason
        assert result.review is None and not result.results
        assert e.manager.snapshot() == before
    finally:
        e.close()


@pytest.mark.parametrize('text', [
    'Te agradecería que iniciaras Steam, porfa.',
    'Abre la aplicación "Steam" para mi lista.',
    'Abre Steam que utilicé ayer.',
    'Abre Steam que uso cuando estudio.',
])
def test_scope_guards_do_not_become_global_vocabulary_allowlist(text):
    e, _ = make(lambda req: decision(req, actions=(app(req),)))
    try:
        result = e.interpret(text)
        assert result.review is not None and not result.results
        assert not e.manager.snapshot().items
    finally:
        e.close()


def test_context_bound_hold_can_omit_top_level_quote_without_losing_local_review():
    e, _ = make(lambda req: Decision(operation='hold', plan_id=req.context.plan_id,
        expected_revision=req.context.revision))
    try:
        before = e.interpret('Abre Discord').plan
        result = e.interpret('Deja pendiente la autorización del plan actual')
        assert result.review is not None and result.review.source_text == 'Deja pendiente la autorización del plan actual'
        assert e.manager.snapshot() == before
        after = confirm(e, result)
        assert after.plan.status == 'withheld' and after.plan.items == before.items
        assert after.plan.plan_id == before.plan_id and not after.results
    finally:
        e.close()


def test_complex_create_requires_exact_local_review_and_never_executes():
    e, p = make(lambda req: decision(req, actions=(app(req),)))
    try:
        pending = e.interpret('Arranca Steam que voy a jugar')
        assert not pending.plan.items
        assert pending.review.proposed_plan.status == 'withheld'
        result = confirm(e, pending)
        assert result.disposition == 'simulated' and result.plan.status == 'simulated'
        assert result.plan.items == pending.review.proposed_plan.items
        assert not result.executed and all(not r.executed and not r.verified for r in result.results)
        assert p.calls == 1 and e.manager.can_publish(result)
        assert not e.manager.can_publish(pending)
    finally:
        e.close()


def test_app_correction_preserves_id_and_unrelated_volume_then_selective_cancel():
    def respond(req):
        if req.text == 'Añade volumen treinta':
            return decision(req, 'append_plan', actions=(ToolCall(tool='system_audio.set_volume', target='system_audio',
                parameters={'value': 30}, evidence=Span(start=0, end=len(req.text))),))
        if req.text == 'No, mejor Spotify':
            action_id = req.context.items[0].action_id
            return decision(req, 'modify_plan', changes=(ActionChange(action_id=action_id, target='spotify'),))
        return decision(req, 'cancel_subset', action_ids=(req.context.items[0].action_id,))
    e, _ = make(respond)
    try:
        first = e.interpret('Abre Steam')
        second = confirm(e, e.interpret('Añade volumen treinta'))
        assert len(second.plan.items) == 2
        corrected = confirm(e, e.interpret('No, mejor Spotify'))
        assert corrected.plan.items[0].action_id == first.plan.items[0].action_id
        assert corrected.plan.items[0].call.target == 'spotify'
        assert corrected.plan.items[1] == second.plan.items[1]
        assert len(corrected.results) == 1
        cancelled = confirm(e, e.interpret('Quita la aplicación y conserva el audio'))
        assert cancelled.plan.items == (second.plan.items[1],)
        assert not cancelled.results and cancelled.plan.plan_id == second.plan.plan_id
    finally:
        e.close()


def test_combined_change_and_append_is_atomic():
    def respond(req):
        return decision(req, 'modify_plan', changes=(ActionChange(action_id=req.context.items[0].action_id, target='spotify'),),
            actions=(ToolCall(tool='system_audio.set_volume', target='system_audio', parameters={'value': 20},
                              evidence=Span(start=0, end=len(req.text))),))
    e, _ = make(respond)
    try:
        first = e.interpret('Abre Steam')
        draft = e.interpret('Mejor Spotify y volumen veinte')
        assert draft.plan == first.plan
        result = confirm(e, draft)
        assert result.plan.revision == first.plan.revision+1
        assert [i.call.target for i in result.plan.items] == ['spotify', 'system_audio']
        assert result.plan.items[0].action_id == first.plan.items[0].action_id
    finally:
        e.close()


@pytest.mark.parametrize('interruption', ['ordinary_turn', 'cancel', 'session', 'hold', 'expiry', 'close'])
def test_review_is_bound_to_generation_session_revision_and_expiry(interruption):
    now = [100.0]
    e, _ = make(lambda req: decision(req, actions=(app(req),)), clock=lambda: now[0])
    try:
        draft = e.interpret('Arranca Steam')
        token = draft.review.review_id
        if interruption == 'ordinary_turn':
            e.interpret('No canceles')
        elif interruption == 'cancel':
            e.cancel()
        elif interruption == 'session':
            e.begin_session('other')
        elif interruption == 'hold':
            e.interpret('Todavía no hagas nada')
        elif interruption == 'expiry':
            now[0] += 31
        else:
            e.close()
        before = e.manager.snapshot()
        result = e.confirm(token)
        assert result.disposition in ('rejected', 'stale') and not result.results
        assert result.plan == before and not result.plan.items
    finally:
        e.close()


def test_review_token_is_single_use_and_failed_token_does_not_apply():
    e, _ = make(lambda req: decision(req, actions=(app(req),)))
    try:
        draft = e.interpret('Arranca Steam')
        token = draft.review.review_id
        assert e.confirm('invented').disposition == 'rejected'
        assert e.confirm(token).disposition == 'rejected'
        draft = e.interpret('Arranca Steam')
        token = draft.review.review_id
        accepted = e.confirm(token)
        assert accepted.disposition == 'simulated'
        again = e.confirm(token)
        assert again.disposition == 'rejected' and again.plan == accepted.plan
    finally:
        e.close()


@pytest.mark.parametrize('bad', ['contradiction', 'target', 'fake_id', 'query_write'])
def test_invalid_plan_never_creates_review_or_mutates_original(bad):
    def respond(req):
        if bad == 'contradiction':
            return decision(req, 'append_plan', actions=(app(req),))
        if bad == 'target':
            return decision(req, 'modify_plan', changes=(ActionChange(action_id=req.context.items[0].action_id, target='unknown'),))
        if bad == 'fake_id':
            return decision(req, 'cancel_subset', action_ids=('invented',))
        return decision(req, 'query_state', actions=(app(req),))
    e, _ = make(respond)
    try:
        first = e.interpret('Abre Steam')
        result = e.interpret('Haz un cambio de prueba')
        assert result.disposition == 'rejected' and not result.review and not result.results
        assert result.plan == first.plan
    finally:
        e.close()


def test_eight_item_limit_is_checked_before_review_even_for_extended_registry():
    from jarvis.next.contracts import Capability
    from jarvis.next.tools import ToolDefinition, ToolRegistry, NoParameters
    targets = ('steam', *(f'app{i}' for i in range(8)))
    registry = ToolRegistry([ToolDefinition(Capability(tool='applications.open', description='Test apps',
        targets=targets, resource='application', access='write', risk='moderate',
        parameter_schema=NoParameters.model_json_schema()), NoParameters)])
    e, _ = make(lambda req: decision(req, 'append_plan', actions=tuple(app(req, x) for x in targets[1:])), registry=registry)
    try:
        first = e.interpret('Abre Steam')
        result = e.interpret('Añade ocho aplicaciones más')
        assert result.disposition == 'rejected' and not result.review and result.plan == first.plan
    finally:
        e.close()


def test_mutating_returned_review_or_decision_cannot_change_confirmed_content():
    def respond(req):
        return decision(req, actions=(ToolCall(tool='system_audio.set_volume', target='system_audio',
            parameters={'value': 30}, evidence=Span(start=0, end=len(req.text))),))
    e, _ = make(respond)
    try:
        pending = e.interpret('Déjalo en treinta')
        pending.review.proposed_plan.items[0].call.parameters['value'] = 80
        pending.decision.actions[0].parameters['value'] = 90
        result = confirm(e, pending)
        assert result.plan.items[0].call.parameters == {'value': 30}
    finally:
        e.close()


def test_deferred_or_negative_model_output_cannot_offer_confirmation():
    e, _ = make(lambda req: Decision(operation='deferred', temporal='conditional',
        plan_id=req.context.plan_id, expected_revision=req.context.revision))
    try:
        result = e.interpret('Cuando termine, abre Steam')
        assert result.disposition == 'withheld' and not result.review and not result.results
    finally:
        e.close()


def test_cancellation_during_confirmation_validation_prevents_commit():
    e, _ = make(lambda req: decision(req, actions=(app(req),)))
    try:
        draft = e.interpret('Arranca Steam')
        original = e.registry.validate
        def interrupt(call):
            original(call)
            e.begin_session('other')
        e.registry.validate = interrupt
        result = e.confirm(draft.review.review_id)
        assert result.disposition == 'stale' and not result.results and result.message == ''
        assert not result.plan.items
    finally:
        e.close()


def test_review_binds_full_request_even_when_model_cites_only_affected_clause():
    text = 'Conserva los demás, pero quita Steam'
    def respond(req):
        fragment = 'quita Steam'
        return Decision(operation='cancel_subset', plan_id=req.context.plan_id, expected_revision=req.context.revision,
            temporal='now', evidence=Span(start=text.index(fragment), end=len(text)),
            action_ids=(req.context.items[0].action_id,))
    e, _ = make(respond)
    try:
        first = e.interpret('Abre Steam')
        draft = e.interpret(text)
        assert draft.review is not None and draft.plan == first.plan
        assert draft.review.source_text == text
        accepted = confirm(e, draft)
        assert not accepted.plan.items and not accepted.executed
    finally:
        e.close()


def test_action_level_evidence_is_sufficient_for_a_review_not_automatic_authority():
    e, _ = make(lambda req: decision(req, 'append_plan', actions=(app(req, 'discord'),)).model_copy(update={'evidence': None}))
    try:
        first = e.interpret('Abre Steam')
        draft = e.interpret('Y abre Discord')
        assert draft.review is not None and draft.plan == first.plan and not draft.results
        assert draft.review.source_text == 'Y abre Discord'
        result = confirm(e, draft)
        assert [i.call.target for i in result.plan.items] == ['steam', 'discord']
    finally:
        e.close()
