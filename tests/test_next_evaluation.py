import json
from pathlib import Path
import pytest
from jarvis.next.contracts import ContextView, InterpretationRequest, ProviderReply, Decision, Span, ToolCall
from jarvis.next.engine import NextEngine
from jarvis.next.providers import FakeProvider, RequestControl
from scripts.evaluate_next_pilot import run_pilot, operation_matches
from scripts.evaluate_next_reserved import verify, continuation
from scripts.next_evaluation_metrics import PredictionObserver, prediction_metrics, identity_preserved


def data():
    return json.loads(Path('docs/evaluation/next_reserved_v1.json').read_text(encoding='utf-8'))


def test_new_corpus_has_32_new_turns_and_one_explicit_control():
    rows = [row for case in data()['cases'] for row in case['turns']]
    assert len(rows) == 33
    assert sum(row.get('role') == 'control_setup' for row in rows) == 1
    assert sum(len(c['turns']) for c in data()['cases'] if c['category'] == 'critical') == 12


def test_semantic_v2_seal_and_contrasts_are_infrastructure_not_accuracy(tmp_path):
    source = Path('docs/evaluation/next_reserved_v2.json')
    import hashlib
    manifest = json.loads(source.read_text(encoding='utf-8'))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source.with_suffix('.sha256').read_text().strip()
    assert len(manifest['cases']) == 16
    assert sum(c['category'] == 'positive' for c in manifest['cases']) == 4
    report = run_pilot(manifest, 'fixture', output=tmp_path/'v2-fixture.json', max_turns=16, detailed_metrics=True)
    assert report['summary']['checks_passed'] == 16
    assert report['summary']['real_model_accuracy'] is None
    assert not report['summary']['unexpected_action_drafts']
    assert all(not r['unreviewed_provider_results'] and not r['executed'] for r in report['rows'])


@pytest.mark.parametrize('variation', ['complete', 'classification', 'error', 'missing', 'wrong_positive', 'draft'])
def test_semantic_acceptance_separates_abstention_classification_and_incomplete_runs(variation):
    from scripts.score_next_semantics import score
    manifest = dict(cases=[dict(id='negative', category='negation', turns=[{}]),
                          dict(id='positive', category='positive', turns=[{}])])
    base = dict(turn=0, error=None, review_offered=False, unreviewed_provider_results=0,
                executed=False, semantic_and_plan_match=True)
    rows = [dict(base, case='negative', category='negation'), dict(base, case='positive', category='positive')]
    if variation == 'classification': rows[0]['semantic_and_plan_match'] = False
    if variation == 'error': rows[0].update(error='invalid_response', semantic_and_plan_match=False)
    if variation == 'missing': rows.pop()
    if variation == 'wrong_positive': rows[1]['semantic_and_plan_match'] = False
    if variation == 'draft': rows[0].update(review_offered=True, semantic_and_plan_match=False)
    result = score(manifest, dict(rows=rows, complete=variation != 'missing'))
    assert result['acceptance_passed'] == (variation in ('complete', 'classification'))
    if variation == 'classification':
        assert result['clean_abstentions'] == 1 and result['non_action_exact_matches'] == 0


def test_fixture_checks_context_ids_but_does_not_claim_model_accuracy(tmp_path):
    report = run_pilot(data(), 'fixture', output=tmp_path/'fixture.json', max_turns=33, detailed_metrics=True)
    summary = report['detailed_summary']
    assert report['summary']['checks_passed'] == 33
    assert summary['evaluation_turns'] == 32 and summary['known_control_turns'] == 1
    assert summary['identity_checks'] == summary['identity_checks_passed'] == 32
    assert summary['observable_provider_decisions'] == 32
    assert report['summary']['real_model_accuracy'] is None
    assert all(row['unreviewed_provider_results'] == 0 for row in report['rows'])


def test_observer_does_not_export_unknown_model_parameter_or_change_engine_policy(tmp_path):
    secret = 'fake-private-value-not-for-report'
    def wrong(req, _):
        return ProviderReply(decision_json=Decision(operation='create_plan', temporal='now',
            actions=(ToolCall(tool='shell.run', target=secret, parameters={'command': secret},
                evidence=Span(start=0, end=len(req.text))),)).model_dump_json())
    observer = PredictionObserver(FakeProvider(wrong))
    e = NextEngine(observer)
    e.begin_session('cli')
    try:
        before = e.manager.snapshot()
        result = e.interpret('Una solicitud sin privilegios')
        fields = prediction_metrics(observer, result, before, e.registry, ['unsupported'], operation_matches)
        assert result.disposition == 'rejected' and result.decision is None
        assert fields['provider_operation_match'] is False and fields['provider_catalog_valid'] is False
        assert secret not in json.dumps(fields) + result.model_dump_json()
    finally:
        e.close()


def test_schema_failure_and_unobserved_transport_are_distinct():
    observer = PredictionObserver(FakeProvider(lambda *_: ProviderReply(decision_json='{}')))
    e = NextEngine(observer)
    e.begin_session('cli')
    try:
        result = e.interpret('Haz algo contextual')
        fields = prediction_metrics(observer, result, ContextView(), e.registry, ['clarify'], operation_matches)
        assert fields['provider_reply_received'] and fields['provider_contract_valid'] is False
        observer.reset()
        fields = prediction_metrics(observer, result, ContextView(), e.registry, ['clarify'], operation_matches)
        assert not fields['provider_reply_received'] and fields['provider_contract_valid'] is None
    finally:
        e.close()


def test_identity_check_detects_replacement_disguised_as_modification():
    e = NextEngine()
    e.begin_session('cli')
    try:
        first = e.interpret('Abre Steam')
        second = e.interpret('Abre Spotify')
        assert not identity_preserved({'operation': 'modify_plan'}, first.plan, second.plan)
        assert identity_preserved({'operation': 'replace_plan'}, first.plan, second.plan)
    finally:
        e.close()


def test_seal_rejects_tampered_data_without_any_provider_call(tmp_path):
    source = Path('docs/evaluation/next_reserved_v1.json')
    copy = tmp_path/'changed.json'
    copy.write_bytes(source.read_bytes()+b' ')
    copy.with_suffix('.sha256').write_text(source.with_suffix('.sha256').read_text())
    with pytest.raises(ValueError, match='seal mismatch'):
        verify(copy)


def test_retired_corpus_cannot_be_presented_as_reserved_again():
    with pytest.raises(ValueError, match='retired'):
        verify(Path('docs/evaluation/next_reserved_v1.json'))


def test_seal_also_checks_module_set_not_only_known_file_hashes(tmp_path):
    import hashlib
    manifest = data()
    manifest['engine_sha256']['jarvis/next/unsealed_module.py'] = 'not-a-real-module'
    raw = json.dumps(manifest).encode()
    path = tmp_path/'module-set.json'
    path.write_bytes(raw)
    path.with_suffix('.sha256').write_text(hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError, match='module set'):
        verify(path)


def prior_report(tmp_path, count):
    source = Path('docs/evaluation/next_reserved_v1.json')
    import hashlib
    manifest = data()
    flat = [dict(case=c['id'], turn=i, text=r['text']) for c in manifest['cases'] for i,r in enumerate(c['turns'])]
    report = dict(provider='groq', model=manifest['configuration']['model'], reasoning_effort='low',
        status='stopped_on_provider_error', rows=flat[:count], reserved_manifest=dict(
            dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), engine_sha256=manifest['engine_sha256']))
    path = tmp_path/'prior.json';path.write_text(json.dumps(report), encoding='utf-8')
    return path, report['reserved_manifest']['dataset_sha256']


def test_manual_continuation_never_repeats_attempted_cases(tmp_path):
    path, digest = prior_report(tmp_path, 18)
    remaining, offset, _ = continuation(data(), digest, path, 'groq')
    assert offset == 18 and remaining['cases'][0]['id'] == 'critical-03'
    assert sum(len(c['turns']) for c in remaining['cases']) == 15


def test_continuation_rejects_mid_session_and_different_provider(tmp_path):
    path, digest = prior_report(tmp_path, 3)
    with pytest.raises(ValueError, match='session boundary'):
        continuation(data(), digest, path, 'groq')
    path, digest = prior_report(tmp_path, 18)
    with pytest.raises(ValueError, match='does not match'):
        continuation(data(), digest, path, 'fixture')


def test_consolidation_checks_first_exposures_without_replaying_model():
    from scripts.summarize_next_reserved import combine
    reports = [Path('docs/reports/next-reserved-v1-first.json'), Path('docs/reports/next-reserved-v1-continuation.json')]
    combined = combine(Path('docs/evaluation/next_reserved_v1.json'), reports)
    assert combined['complete'] and combined['summary']['new_turns'] == 32
    assert combined['summary']['known_control_turns'] == 1 and len(combined['rows']) == 33


@pytest.mark.parametrize('duplicate', [True, False])
def test_consolidation_rejects_repeated_or_reordered_reports(duplicate):
    from scripts.summarize_next_reserved import combine
    first = Path('docs/reports/next-reserved-v1-first.json')
    second = Path('docs/reports/next-reserved-v1-continuation.json')
    with pytest.raises(ValueError):
        combine(Path('docs/evaluation/next_reserved_v1.json'), [first, first] if duplicate else [second, first])
