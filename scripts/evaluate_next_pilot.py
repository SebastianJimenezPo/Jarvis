"""32 scripted development turns. No retries, personal audio or physical actions."""
import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.next.contracts import ActionChange, Decision, ProviderReply, Span, ToolCall
from jarvis.next.engine import NextEngine
from jarvis.next.providers import FakeProvider


def calls(view):
    return [{'tool': item.call.tool, 'target': item.call.target, 'parameters': item.call.parameters} for item in view.items]


def fixture_decision(row, request):
    spec = row['decision']
    def local_id(selector):
        matches = [item.action_id for item in request.context.items
                   if item.call.tool == selector['tool'] and item.call.target == selector['target']]
        if len(matches) != 1:
            raise ValueError('Fixture setup missing')
        return matches[0]
    span = Span(start=0, end=len(request.text))
    actions = tuple(ToolCall(**call, evidence=span) for call in spec.get('actions', []))
    changes = tuple(ActionChange(action_id=local_id(change['match']), target=change.get('target'),
        parameters=change.get('parameters', {})) for change in spec.get('changes', []))
    return Decision(operation=spec['operation'], plan_id=request.context.plan_id,
        expected_revision=request.context.revision, evidence=span,
        temporal=spec.get('temporal', 'now' if actions or changes or spec['operation'] in ('cancel_subset', 'replace_plan') else 'unspecified'),
        actions=actions, changes=changes, action_ids=tuple(local_id(s) for s in spec.get('remove', [])))


def run_pilot(data, provider_kind, *, output, allow_remote=False, free_tier=False, timeout=8.0, interval=6.0, max_turns=32, model='openai/gpt-oss-20b'):
    import psutil
    if provider_kind not in ('fixture', 'offline', 'groq'):
        raise ValueError('Unknown provider')
    if output.exists():
        raise ValueError('Preserve previous report')
    if not 1 <= max_turns <= 40:
        raise ValueError('Pilot limit is 1..40 turns')
    if provider_kind == 'groq' and (not allow_remote or not free_tier or not math.isfinite(interval) or interval < 6):
        raise ValueError('Remote opt-in, Free attestation and >=6-second interval required')
    report = {'provider': provider_kind, 'model': model if provider_kind == 'groq' else None, 'method': data['method'], 'commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True).strip(), 'status': 'running', 'rows': [],
        'max_turns': max_turns, 'available_turns': sum(len(c['turns']) for c in data['cases']),
        'limits': 'Development cases. Fixture scores check infrastructure, not model quality. Joint pipeline matches do not isolate model/router/policy accuracy. Rate-limit sleeps are outside interpretation latency. No generalization, physical, voice or FPS claims.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    remote_key = None
    if provider_kind == 'groq':
        from jarvis.next.credentials import read_groq_key
        remote_key = read_groq_key()
    if provider_kind == 'groq' and not remote_key:
        report.update(status='not_run_missing_key', summary=None)
        save()
        return report
    active = [None]
    if provider_kind == 'fixture':
        provider = FakeProvider(lambda req, _: ProviderReply(decision_json=fixture_decision(active[0], req).model_dump_json()))
    elif provider_kind == 'groq':
        from jarvis.next.groq import GroqProvider
        provider = GroqProvider(api_key=remote_key, enabled=True, free_tier_confirmed=True, model=model)
    else:
        provider = None
    engine = NextEngine(provider, timeout=timeout, review_enabled=True)
    process = psutil.Process()
    report['client_rss_start_bytes'] = process.memory_info().rss
    attempted = 0
    last_request = None
    stop = False
    try:
        for case in data['cases']:
            if stop:
                break
            engine.begin_session(case['id'])
            setup_ok = True
            for index, row in enumerate(case['turns']):
                if len(report['rows']) >= max_turns:
                    stop = True
                    break
                active[0] = row
                before = engine.manager.snapshot()
                # Throttle outside engine timing; no direct command spends API quota.
                from jarvis.next.direct import direct_decision
                remote = provider_kind == 'groq' and direct_decision(row['text'], before) is None
                if remote and last_request is not None:
                    time.sleep(max(0, interval-(time.monotonic()-last_request)))
                if remote:
                    last_request = time.monotonic()
                    attempted += 1
                cpu = process.cpu_times()
                cpu_before = cpu.user+cpu.system
                result = engine.interpret(row['text'], case['id'], str(index))
                candidate = result.review.proposed_plan if result.review else result.plan
                expected = row['expected_plan']
                operation_ok = result.decision is not None and result.decision.operation == row['decision']['operation']
                plan_ok = calls(candidate) == (calls(before) if expected is None else expected)
                match = operation_ok and plan_ok and result.error is None
                confirmed = None
                # Scripted expected tool/target/values are the local review oracle.
                # Never auto-confirm a wrong or merely schema-valid model proposal.
                if match and result.review:
                    confirmed = engine.confirm(result.review.review_id, case['id'], f'{index}-review')
                    match = confirmed.disposition not in ('stale', 'rejected') and calls(confirmed.plan) == calls(candidate)
                cpu = process.cpu_times()
                forbidden = row['decision']['operation'] in ('deferred', 'negated', 'hypothetical', 'conversation', 'clarify', 'unsupported')
                record = {'case': case['id'], 'turn': index, 'text': row['text'], 'setup_succeeded': setup_ok,
                    'expected_operation': row['decision']['operation'], 'actual_operation': result.decision.operation if result.decision else result.proposed_operation,
                    'route': result.route, 'disposition': result.disposition, 'semantic_and_plan_match': bool(match),
                    'review_offered': result.review is not None, 'review_applied': confirmed is not None,
                    'unexpected_action_draft': forbidden and bool(result.review),
                    'error': result.error, 'policy_reason': result.policy_reason, 'candidate_plan': calls(candidate), 'seconds': result.seconds,
                    'usage': result.usage.model_dump(), 'executed': result.executed,
                    'client_rss_after_turn_bytes': process.memory_info().rss,
                    'client_cpu_seconds_delta': max(0, cpu.user+cpu.system-cpu_before)}
                report['rows'].append(record)
                setup_ok = setup_ok and bool(match)
                save()
                if provider_kind == 'groq' and result.error in ('authentication', 'quota', 'model_unavailable', 'invalid_response', 'timeout', 'connection', 'unavailable'):
                    report['status'] = 'stopped_on_provider_error'
                    stop = True
                    break
        if report['status'] == 'running':
            report['status'] = 'completed' if len(report['rows']) == report['available_turns'] else 'completed_limited'
    finally:
        engine.close()
    rows = report['rows']
    report['client_resources'] = {'rss_final_bytes': process.memory_info().rss,
        'rss_max_turn_boundary_bytes': max((r['client_rss_after_turn_bytes'] for r in rows), default=report['client_rss_start_bytes']),
        'cpu_seconds_during_interpretation_and_review': sum(r['client_cpu_seconds_delta'] for r in rows),
        'cpu_peak': None, 'gpu': None,
        'limits': 'Text pilot process only; snapshots at turn boundaries, not sampled peaks. No resident, STT, TTS, gaming or remote-server memory measurement.'}
    report['summary'] = {'turns': len(rows), 'checks_passed': sum(r['semantic_and_plan_match'] for r in rows),
        'setup_failed_turns': sum(not r['setup_succeeded'] for r in rows),
        'unexpected_action_drafts': sum(r['unexpected_action_draft'] for r in rows),
        'remote_requests_attempted': attempted, 'real_model_accuracy': None,
        'live_pipeline_match_rate': sum(r['semantic_and_plan_match'] for r in rows)/len(rows)
            if rows and provider_kind == 'groq' else None}
    report['route_latency'] = {}
    for route in ('direct', 'provider', 'offline'):
        values = sorted(r['seconds'] for r in rows if r['route'] == route)
        report['route_latency'][route] = {'count': len(values), 'median': statistics.median(values) if values else None,
            'p95': values[min(len(values)-1, math.ceil(.95*len(values))-1)] if values else None}
    save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['offline', 'fixture', 'groq'], default='offline')
    parser.add_argument('--dataset', type=Path, default=Path('docs/evaluation/next_text_pilot.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-remote', action='store_true')
    parser.add_argument('--free-tier', action='store_true')
    parser.add_argument('--max-turns', type=int, default=32)
    parser.add_argument('--interval-seconds', type=float, default=6.0)
    parser.add_argument('--model', choices=['openai/gpt-oss-20b', 'openai/gpt-oss-120b'], default='openai/gpt-oss-20b')
    args = parser.parse_args()
    try:
        report = run_pilot(json.loads(args.dataset.read_text(encoding='utf-8')), args.provider, output=args.output,
            allow_remote=args.allow_remote, free_tier=args.free_tier, max_turns=args.max_turns, interval=args.interval_seconds, model=args.model)
    except ValueError:
        parser.error('Check output path, turn limit, remote opt-in and Free account attestation.')
    print(json.dumps({'status': report['status'], 'summary': report.get('summary')}, indent=2))


if __name__ == '__main__':
    main()
