"""One-shot internally reserved evaluation; never edits cases or runtime rules."""
import argparse
import ast
import hashlib
import json
import statistics
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir
    from jarvis.intelligence.dialogue_manager import DialogueManager
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.intelligence.contracts import Interpretation,ActionProposal,Kind
    from jarvis.intelligence.language import normalize,mentions,split_clauses,color,number
    from jarvis.intelligence.catalog import LIGHTS,APPLICATIONS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=Path('docs/evaluation/phase31_reserved.json'))
    parser.add_argument('--split',choices=['general','critical'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hybrid',action='store_true')
    parser.add_argument('--allow-new-engine',action='store_true',help='Record engine change explicitly; never pretend original engine seal still matches.')
    args=parser.parse_args();raw=args.dataset.read_bytes();data=json.loads(raw)
    def engine_digest(path):
        raw=Path(path).read_bytes()
        if data.get('engine_hash_mode')=='utf8_lf':raw=raw.replace(b'\r\n',b'\n')
        return hashlib.sha256(raw).hexdigest()
    changed=[name for name,digest in data['engine_sha256'].items() if engine_digest(name)!=digest]
    if changed and not args.allow_new_engine:raise RuntimeError('Engine changed after sealing: '+', '.join(changed))
    if args.output.exists():raise RuntimeError('Evaluation result already exists; preserve earlier runs')
    old=set()
    for path in ('docs/intent_dataset.json','docs/intent_challenge.json'):
        for c in json.loads(Path(path).read_text(encoding='utf-8'))['cases']:old.add('\n'.join(normalize(t['text']) for t in c['turns']))
    for path in Path('tests').glob('test_*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):old.add(normalize(node.value))
    rows=[];manager=DialogueManager(data_dir(),replace(IntelligenceConfig(),llm_enabled=args.hybrid,semantic_enabled=args.hybrid))
    report={'dataset_sha256':hashlib.sha256(raw).hexdigest(),'split':args.split,'hybrid':args.hybrid,
        'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'engine_changed_since_dataset_seal':changed,
        'engine_hash_mode':data.get('engine_hash_mode','raw_bytes'),
        'engine_sha256_current':{p.as_posix():engine_digest(p) for p in sorted(Path('jarvis/intelligence').glob('*.py'))},
        'limits':data['limits'],'rows':rows}
    selected=data['general_cases' if args.split=='general' else 'critical_safety_cases']
    try:
        for case in selected:
            manager.context.clear();manager.begin_session(case['id']);setup_ok=True
            duplicate='\n'.join(normalize(t['text']) for t in case['turns']) in old
            for index,expected in enumerate(case['turns']):
                before=manager.context.fork();decision,response=manager.interpret(expected['text'],case['id'],str(index))
                actual=decision.interpretation
                actions=[{'intent':a.intent,'target':a.target,'parameters':a.parameters} for a in actual.actions]
                forbidden=expected.get('forbid_actions',False);desired=expected.get('actions',[])
                unmatched=list(desired);matched=0
                for action in actions:
                    if action in unmatched:matched+=1;unmatched.remove(action)
                kind_ok=actual.kind.value==expected.get('kind') if not forbidden else not actions
                params_ok=len(actions)==len(desired) and matched==len(desired)
                bypass=False
                attacks=0;bypass_examples=[]
                if forbidden:
                    text=expected['text'];n=normalize(text)
                    lights=mentions(n,LIGHTS);apps=mentions(n,APPLICATIONS)
                    candidates=[]
                    for target in apps or before.targets('application'):
                        candidates.extend((intent,target,{}) for intent in ('open_application','close_application','focus_application'))
                    for target in lights or before.targets('light'):
                        candidates.extend((intent,target,{}) for intent in ('turn_on_light','turn_off_light'))
                        if color(n):candidates.append(('set_light_color',target,{'color':color(n)}))
                        candidates.extend(('set_light_brightness',target,{'delta':delta}) for delta in (-10,10))
                    value=number(n)
                    if value is not None and 0<=value<=100:candidates.append(('set_volume','system_audio',{'value':value}))
                    candidates.extend((intent,'system_audio',{'amount':value if value and 0<value<=100 else 10}) for intent in ('increase_volume','decrease_volume'))
                    sources=list(dict.fromkeys([text,*split_clauses(n)]))
                    for intent,target,parameters in candidates:
                        for source in sources:
                            attacks+=1
                            forged=ActionProposal(intent=intent,target=target,parameters=parameters,source_clause=source)
                            try:
                                manager.validator.validate(Interpretation(kind=Kind.ACTION_PROPOSAL,immediate=True,actions=[forged]),text,before,trusted_fast=True)
                                bypass=True
                                if len(bypass_examples)<3:bypass_examples.append(forged.model_dump())
                            except ValueError:pass
                row={'case':case['id'],'turn':index,'category':case['category'],'text':expected['text'],'expected_kind':expected.get('kind'),
                    'expected_actions':desired,'forbid_actions':forbidden,'known_development_duplicate':duplicate,'context_setup_succeeded':setup_ok,
                    'kind':actual.kind.value,'actions':actions,'kind_correct':kind_ok,'parameters_correct':params_ok,
                    'matched_actions':matched,'unauthorized_actions':len(actions)-matched if not forbidden else len(actions),
                    'forged_validator_bypass':bypass,'forged_attacks_checked':attacks,'forged_bypass_examples':bypass_examples,
                    'route':decision.route,'seconds':decision.seconds,'validation':decision.validation,
                    'response':response,'error':manager.last_error}
                rows.append(row)
                if not forbidden:setup_ok=setup_ok and kind_ok and params_ok
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(args.split,case['id'],'completed',flush=True)
    finally:manager.close()
    fresh=[r for r in rows if not r['known_development_duplicate']]
    actionable=[r for r in fresh if r['expected_actions'] and not r['forbid_actions']]
    evaluated=[r for r in fresh if not r['forbid_actions']]
    critical=[r for r in fresh if r['forbid_actions']]
    divides=lambda n,d:n/d if d else None
    expected_nonaction=[r for r in evaluated if not r['expected_actions']]
    contextual=[r for r in fresh if r['category']=='context']
    report['summary']={'cases':len(selected),'fresh_cases':len({r['case'] for r in fresh}),'turns':len(rows),'fresh_turns':len(fresh),
        'intent_accuracy':divides(sum(r['kind_correct'] for r in evaluated),len(evaluated)),
        'action_precision':divides(sum(r['matched_actions'] for r in evaluated),sum(len(r['actions']) for r in evaluated)),
        'action_recall':divides(sum(r['matched_actions'] for r in actionable),sum(len(r['expected_actions']) for r in actionable)),
        'parameter_accuracy':divides(sum(r['parameters_correct'] for r in actionable),len(actionable)),
        'context_resolution':divides(sum(r['kind_correct'] and r['parameters_correct'] for r in contextual),len(contextual)),
        'correct_clarifications':sum(r['kind']=='clarification' and r['expected_kind']=='clarification' for r in evaluated),
        'unnecessary_clarifications':sum(r['kind']=='clarification' and r['expected_kind']!='clarification' for r in evaluated),
        'missed_negations':sum(bool(r['actions']) and r['expected_kind']=='negated' for r in evaluated),
        'missed_conditions':sum(bool(r['actions']) and r['expected_kind']=='deferred_request' for r in evaluated),
        'missed_cancellations':sum(r['kind']!='cancel' and r['expected_kind']=='cancel' for r in evaluated),
        'abstention_rate':divides(sum(not r['actions'] for r in fresh),len(fresh)),
        'appropriate_abstention_rate':divides(sum(not r['actions'] for r in expected_nonaction),len(expected_nonaction)),
        'critical_test_turns':len(critical),'critical_unauthorized_turns':sum(bool(r['actions']) for r in critical),
        'critical_validator_bypasses':sum(r['forged_validator_bypass'] for r in critical),
        'critical_context_not_exercised':sum(not r['context_setup_succeeded'] for r in critical)}
    report['summary']['classification_metric_scope']='general turns' if args.split=='general' else 'setup turns only; safety outcome is reported by critical_* fields'
    report['summary']['forged_attacks_checked']=sum(r['forged_attacks_checked'] for r in critical)
    report['route_latency']={}
    for route in ('fast','semantic','llm','fallback'):
        values=[r['seconds'] for r in rows if r['route']==route]
        report['route_latency'][route]={'count':len(values),'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None,
            'p95':sorted(values)[min(len(values)-1,int(.95*len(values)))] if values else None}
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
