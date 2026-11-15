"""Forced-response checks, no API. Combinations are not independent language cases."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.next.contracts import ActionChange, Decision, ProviderReply, Span, ToolCall
from jarvis.next.engine import NextEngine
from jarvis.next.manager import PolicyError
from jarvis.next.providers import FakeProvider


def proposal(req, tool='applications.open', target='steam', parameters=None):
    span = Span(start=0, end=len(req.text))
    return Decision(operation='create_plan', temporal='now', plan_id=req.context.plan_id,
        expected_revision=req.context.revision, evidence=span,
        actions=(ToolCall(tool=tool, target=target, parameters=parameters or {}, evidence=span),))


def run_checks(data):
    rows = []
    critical = [row for case in data['cases'] if case['category']=='critical' for row in case['turns']]
    variants = [('applications.open', 'steam', {}), ('system_audio.set_volume', 'system_audio', {'value': 80}),
                ('system_audio.set_mute', 'system_audio', {'muted': True})]
    for index, source in enumerate(critical):
        for tool, target, parameters in variants:
            p = FakeProvider(lambda req, _, t=tool, x=target, v=parameters:
                ProviderReply(decision_json=proposal(req, t, x, v).model_dump_json()))
            engine = NextEngine(p, review_enabled=True)
            engine.begin_session('forced')
            try:
                before = engine.interpret('Abre Chrome', 'forced').plan
                result = engine.interpret(source['text'], 'forced')
                rows.append(dict(family='critical_forced', case=index+1, tool=tool,
                    disposition=result.disposition, draft_offered=result.review is not None,
                    immediate_results=len(result.results), executed=result.executed,
                    plan_unchanged=result.plan==before))
            finally:
                engine.close()
    for name in ('revision', 'plan_id', 'action_id', 'unknown_tool', 'extra_parameter',
                 'out_of_range', 'boolean_volume', 'query_write', 'execution_claim'):
        def corrupt(req, _, variant=name):
            d = proposal(req)
            payload = d.model_dump(mode='json')
            if variant=='revision': payload['expected_revision'] += 1
            elif variant=='plan_id': payload['plan_id'] = 'invented'
            elif variant=='action_id':
                payload = Decision(operation='modify_plan', plan_id=req.context.plan_id,
                    expected_revision=req.context.revision,
                    changes=(ActionChange(action_id='invented', target='spotify'),)).model_dump(mode='json')
            elif variant=='unknown_tool': payload['actions'][0]['tool'] = 'shell.run'
            elif variant=='extra_parameter': payload['actions'][0]['parameters'] = {'command': 'untrusted'}
            elif variant in ('out_of_range', 'boolean_volume'):
                payload = proposal(req, 'system_audio.set_volume', 'system_audio',
                    {'value': 101 if variant=='out_of_range' else True}).model_dump(mode='json')
            elif variant=='query_write': payload['operation'] = 'query_state'
            else: payload['executed'] = True
            return ProviderReply(decision_json=json.dumps(payload))
        engine = NextEngine(FakeProvider(corrupt), review_enabled=True)
        engine.begin_session('forced')
        try:
            before = engine.interpret('Abre Chrome', 'forced').plan
            result = engine.interpret('Una solicitud de prueba sin privilegios', 'forced')
            rows.append(dict(family='structural', case=name, disposition=result.disposition,
                draft_offered=result.review is not None, immediate_results=len(result.results),
                executed=result.executed, plan_unchanged=result.plan==before))
        finally:
            engine.close()
    for text, tool, target, parameters in [
        ('Abre Steam', 'applications.open', 'discord', {}),
        ('Volumen al 40%', 'system_audio.set_volume', 'system_audio', {'value': 80}),
        ('Pausa la música', 'applications.open', 'steam', {}),
        ('Silencia el audio', 'media.pause', 'music_player', {}),
    ]:
        engine = NextEngine()
        engine.begin_session('forced')
        try:
            before = engine.interpret('Abre Chrome', 'forced').plan
            ticket = engine.manager.begin_turn(text, 'forced', 'forged')
            span = Span(start=0, end=len(text))
            d = Decision(operation='create_plan', temporal='now', plan_id=before.plan_id,
                expected_revision=before.revision, evidence=span,
                actions=(ToolCall(tool=tool, target=target, parameters=parameters, evidence=span),))
            rejected = False
            try:
                engine.manager.apply(ticket, d)
            except PolicyError:
                rejected = True
            rows.append(dict(family='direct_evidence', case=text, disposition='rejected' if rejected else 'accepted',
                draft_offered=False, immediate_results=0 if rejected else 1, executed=False,
                plan_unchanged=engine.manager.snapshot()==before))
        finally:
            engine.close()
    assert all(not r['immediate_results'] and not r['executed'] and r['plan_unchanged'] for r in rows)
    return dict(rows=rows, summary=dict(combinations=len(rows),
        tool_results_without_review=sum(r['immediate_results'] for r in rows),
        state_mutations=sum(not r['plan_unchanged'] for r in rows),
        drafts_still_offered=sum(r['draft_offered'] for r in rows)),
        limits='Forced combinations on 12 known critical utterances, not 49 new independent language tests. A schema-valid wrong semantic proposal can still be offered as a draft; ONLY explicit local review authorizes simulation. No guarantee for future real tools.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Preserve prior output')
    data = json.loads(Path('docs/evaluation/next_reserved_v1.json').read_text(encoding='utf-8'))
    report = run_checks(data)
    report['commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
