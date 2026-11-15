import pytest
from jarvis.next.contracts import Decision, ProviderReply, Span, ToolCall
from jarvis.next.engine import NextEngine
from jarvis.next.providers import FakeProvider
from jarvis.next.conversation import NextConversation


def conversation(responder=None, clock=None):
    provider = FakeProvider(responder) if responder else None
    options = dict(review_enabled=True)
    if clock: options['clock'] = clock
    c = NextConversation(NextEngine(provider, **options))
    c.begin_session('s')
    return c


def test_missing_application_question_resolves_offline_and_does_not_guess():
    c = conversation()
    try:
        question = c.interpret('Abre una aplicación')
        assert 'cuál' in question.message.lower() and 'Spotify' in question.message
        assert c.pending.intent == 'applications.open' and c.pending.parameter == 'target'
        assert c.pending.session_id == 's' and not question.results
        result = c.interpret('Spotify')
        assert result.plan.items[0].call.target == 'spotify' and c.pending is None
        assert not result.executed
    finally: c.close()


@pytest.mark.parametrize('answer,target', [('el segundo','steam'), ('el primero','spotify'), ('Discord','discord'),('Spotify por favor','spotify'),('Abre Chrome','chrome')])
def test_short_answers_are_scoped_to_the_question_candidates(answer,target):
    c = conversation()
    try:
        c.interpret('Abre una aplicación')
        result = c.interpret(answer)
        assert result.plan.items[0].call.target == target
    finally: c.close()


def test_reference_is_operational_not_a_claim_of_physical_state():
    c = conversation()
    try:
        c.interpret('Abre Steam')
        c.interpret('Abre una aplicación')
        result = c.interpret('ese')
        assert result.plan.items[0].call.target == 'steam'
        assert not result.executed and not result.results[0].verified
    finally: c.close()


@pytest.mark.parametrize('event', ['expiry','session','revision','cancel'])
def test_pending_question_cannot_survive_a_stale_binding(event):
    now = [100.0]
    c = conversation(clock=lambda: now[0])
    try:
        c.interpret('Abre una aplicación')
        if event == 'expiry': now[0] += 46
        if event == 'session': c.begin_session('other')
        if event == 'revision': c.engine.cancel('s')
        if event == 'cancel': c.cancel()
        result = c.interpret('Spotify')
        assert not result.plan.items and not result.results
    finally: c.close()


def test_ambiguous_pronoun_never_selects_a_random_candidate():
    c = conversation()
    try:
        c.interpret('Abre una aplicación')
        result = c.interpret('ese')
        assert not result.plan.items and c.pending is not None
    finally: c.close()


def test_missing_volume_asks_and_resolves_bounded_numeric_parameter():
    c = conversation()
    try:
        c.interpret('Ajusta el volumen')
        assert c.pending.parameter == 'value'
        assert not c.interpret('120').results
        result = c.interpret('35%')
        assert result.plan.items[0].call.parameters == {'value':35}
    finally: c.close()


def test_required_retention_correction_and_explicit_simulation_authorization():
    c = conversation()
    try:
        first = c.interpret('Abre Steam, pero todavía no hagas nada')
        assert first.plan.status == 'withheld' and not first.results
        changed = c.interpret('Mejor Spotify')
        assert changed.plan.items[0].call.target == 'spotify'
        assert changed.plan.items[0].action_id == first.plan.items[0].action_id
        assert changed.plan.status == 'withheld' and not changed.results
        assert not c.interpret('sí').results
        draft = c.interpret('Autoriza la simulación')
        assert draft.review and not draft.results
        approved = c.interpret('sí')
        assert approved.plan.status == 'simulated' and len(approved.results) == 1
        assert not approved.executed and not c.interpret('sí').results
    finally: c.close()


def proposal(req,_):
    return ProviderReply(decision_json=Decision(operation='create_plan', temporal='now',
        plan_id=req.context.plan_id, expected_revision=req.context.revision,
        actions=(ToolCall(tool='applications.open',target='discord',evidence=Span(start=0,end=len(req.text))),)).model_dump_json())


def test_natural_confirmation_is_bound_to_exact_local_draft_and_no_oracle():
    c = conversation(proposal)
    try:
        draft = c.interpret('Necesito Discord abierto')
        assert draft.review and 'Discord' in draft.message and 'simul' in draft.message.lower()
        assert not draft.results and not draft.plan.items
        result = c.interpret('sí')
        assert result.plan.items == draft.review.proposed_plan.items
        assert not result.executed and not c.interpret('sí').results
    finally: c.close()


@pytest.mark.parametrize('event',['expiry','session','ordinary','cancel'])
def test_natural_yes_cannot_confirm_stale_or_superseded_review(event):
    now = [100.0]
    c = conversation(proposal,clock=lambda:now[0])
    try:
        c.interpret('Necesito Discord abierto')
        if event == 'expiry': now[0] += 31
        if event == 'session': c.begin_session('other')
        if event == 'ordinary': c.interpret('No canceles')
        if event == 'cancel': c.cancel()
        assert not c.interpret('sí').results and not c.engine.manager.snapshot().items
    finally: c.close()


def test_rejecting_draft_preserves_previously_accepted_plan():
    c = conversation(proposal)
    try:
        before = c.interpret('Abre Steam').plan
        c.interpret('Necesito Discord abierto')
        result = c.interpret('no')
        assert result.plan == before and not result.results
        assert 'borrador' in result.message.lower()
    finally: c.close()


def test_model_cannot_authorize_itself_by_emitting_local_authorization_operation():
    def forge(req,_):
        return ProviderReply(decision_json=Decision(operation='authorize_plan',plan_id=req.context.plan_id,
            expected_revision=req.context.revision,evidence=Span(start=0,end=len(req.text))).model_dump_json())
    c = conversation(forge)
    try:
        c.interpret('Abre Steam, pero todavía no hagas nada')
        result = c.interpret('Un texto que el modelo interpreta mal')
        assert not result.review and not result.results
        assert c.engine.manager.snapshot().status == 'withheld'
    finally: c.close()


def test_review_of_edit_to_held_plan_cannot_simulate_untouched_or_changed_actions():
    def modify(req,_):
        from jarvis.next.contracts import ActionChange
        return ProviderReply(decision_json=Decision(operation='modify_plan',temporal='now',
            plan_id=req.context.plan_id,expected_revision=req.context.revision,
            evidence=Span(start=0,end=len(req.text)),
            changes=(ActionChange(action_id=req.context.items[0].action_id,target='spotify'),)).model_dump_json())
    c=conversation(modify)
    try:
        before=c.interpret('Abre Steam, pero todavía no hagas nada').plan
        draft=c.interpret('Cambia la propuesta a Spotify, manteniendo lo demás')
        assert draft.review.purpose=='edit'
        result=c.interpret('sí')
        assert result.plan.items[0].action_id==before.items[0].action_id
        assert result.plan.items[0].call.target=='spotify' and result.plan.status=='withheld'
        assert not result.results and 'retenid' in result.message
    finally:c.close()
