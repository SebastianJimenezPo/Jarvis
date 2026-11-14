import io
import json
from pathlib import Path
import pytest
from scripts.evaluate_next_pilot import run_pilot


def data():
    return json.loads(Path('docs/evaluation/next_text_pilot.json').read_text(encoding='utf-8'))


def test_fixture_proves_32_turn_orchestration_not_model_accuracy(tmp_path):
    report = run_pilot(data(), 'fixture', output=tmp_path/'fixture.json')
    assert report['status'] == 'completed'
    assert report['summary']['turns'] == report['summary']['checks_passed'] == 32
    assert report['summary']['remote_requests_attempted'] == 0
    assert report['summary']['real_model_accuracy'] is None
    assert all(not row['executed'] for row in report['rows'])


def test_offline_keeps_local_commands_without_claiming_natural_understanding(tmp_path):
    report = run_pilot(data(), 'offline', output=tmp_path/'offline.json')
    assert report['summary']['checks_passed'] == 9
    assert report['summary']['remote_requests_attempted'] == 0
    assert report['summary']['setup_failed_turns'] > 0


def test_missing_key_skips_remote_instead_of_inventing_results(tmp_path, monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    report = run_pilot(data(), 'groq', output=tmp_path/'missing.json', allow_remote=True, free_tier=True)
    assert report['status'] == 'not_run_missing_key' and report['summary'] is None and not report['rows']


def test_no_remote_without_both_opt_ins_and_no_overwriting_results(tmp_path):
    with pytest.raises(ValueError):
        run_pilot(data(), 'groq', output=tmp_path/'bad.json')
    path = tmp_path/'prior.json'
    path.write_text('prior result')
    with pytest.raises(ValueError):
        run_pilot(data(), 'fixture', output=path)
    assert path.read_text() == 'prior result'


def test_mismatched_model_action_is_never_auto_confirmed_by_evaluator(tmp_path, monkeypatch):
    import scripts.evaluate_next_pilot as pilot
    from jarvis.next.contracts import Decision, Span, ToolCall
    single = {'method': 'Manipulated mock; not model accuracy', 'cases': [data()['cases'][3]]}
    def wrong(row, req):
        span = Span(start=0, end=len(req.text))
        return Decision(operation='create_plan', plan_id=req.context.plan_id, expected_revision=req.context.revision,
            temporal='now', evidence=span, actions=(ToolCall(tool='applications.open', target='steam', evidence=span),))
    monkeypatch.setattr(pilot, 'fixture_decision', wrong)
    report = pilot.run_pilot(single, 'fixture', output=tmp_path/'wrong.json')
    assert report['summary']['checks_passed'] == 0 and report['summary']['unexpected_action_drafts'] == 1
    assert not report['rows'][0]['review_applied'] and not report['rows'][0]['executed']


def test_quota_error_stops_pilot_without_retry_or_waiting_for_other_cases(tmp_path, monkeypatch):
    from jarvis.next.providers import FakeProvider, ProviderError
    from jarvis.next import groq
    calls = []
    def quota(*_):
        calls.append(1)
        raise ProviderError('quota')
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key-not-used-on-network')
    monkeypatch.setattr(groq, 'GroqProvider', lambda **_: FakeProvider(quota))
    report = run_pilot(data(), 'groq', output=tmp_path/'quota.json', allow_remote=True, free_tier=True)
    assert report['status'] == 'stopped_on_provider_error' and len(calls) == 1
    assert report['summary']['remote_requests_attempted'] == 1


def test_turn_budget_is_explicit_and_does_not_claim_full_completion(tmp_path):
    report = run_pilot(data(), 'fixture', output=tmp_path/'limited.json', max_turns=2)
    assert report['status'] == 'completed_limited' and report['summary']['turns'] == 2


def test_cli_interactive_is_offline_by_default_and_invalid_review_is_safe(monkeypatch, capsys):
    from jarvis.next.__main__ import main
    monkeypatch.setattr('sys.argv', ['jarvis.next', '--interactive', '--review'])
    monkeypatch.setattr('sys.stdin', io.StringIO('Abre Steam\n:confirm invented\n:quit\n'))
    assert main() == 0
    first, second = map(json.loads, capsys.readouterr().out.splitlines())
    assert first['disposition'] == 'simulated' and second['disposition'] == 'rejected'
    assert first['plan'] == second['plan']


def test_cli_rejects_implicit_remote_use_before_creating_provider(monkeypatch):
    from jarvis.next.__main__ import main
    monkeypatch.setattr('sys.argv', ['jarvis.next', '--provider', 'groq', 'Arranca Steam'])
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
