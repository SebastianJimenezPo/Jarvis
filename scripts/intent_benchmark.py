"""Structured interpretation benchmark; never executes proposed actions."""
import argparse
import json
import sys
import time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import numpy as np
    import psutil
    from jarvis.core.config import data_dir
    from jarvis.intelligence.dialogue_manager import DialogueManager
    from jarvis.intelligence.settings import IntelligenceConfig
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=Path('docs/intent_dataset.json'))
    p.add_argument('--output',type=Path,default=Path('docs/reports/intent-benchmark.json'))
    p.add_argument('--split',choices=['all','development','holdout'],default='all')
    p.add_argument('--llm',action='store_true');p.add_argument('--semantic',action='store_true')
    args=p.parse_args();cases=json.loads(args.dataset.read_text(encoding='utf-8'))['cases'];rows=[]
    cfg=replace(IntelligenceConfig(),llm_enabled=args.llm,semantic_enabled=args.semantic)
    model=DialogueManager(data_dir(),cfg)
    start=time.perf_counter();before=psutil.Process().cpu_times();rss=psutil.Process().memory_info().rss
    try:
        for case in cases:
            if args.split!='all' and case['split']!=args.split:continue
            model.context.clear();model.begin_session(case['id'])
            for index,turn in enumerate(case['turns']):
                decision,response=model.interpret(turn['text'],case['id'],str(index))
                result=decision.interpretation
                actual=[{'intent':a.intent,'target':a.target,'parameters':a.parameters} for a in result.actions]
                expected=turn['actions'];kind_ok=result.kind.value==turn['kind'];params_ok=actual==expected
                unmatched=list(expected);matched=0;unexpected=[]
                for item in actual:
                    if item in unmatched:unmatched.remove(item);matched+=1
                    else:unexpected.append(item)
                rows.append({'case':case['id'],'split':case['split'],'category':case['category'],'critical':case['critical'],
                    'turn':index,'text':turn['text'],'expected_kind':turn['kind'],'kind':result.kind.value,
                    'expected_actions':expected,'actions':actual,'kind_correct':kind_ok,'parameters_correct':params_ok,
                    'unauthorized_proposal':bool(unexpected),'matched_proposals':matched,'unexpected_proposals':unexpected,
                    'route':decision.route,'seconds':decision.seconds,
                    'reason':result.reason_code,'error':model.last_error})
                rss=max(rss,psutil.Process().memory_info().rss)
    finally:model.close()
    elapsed=time.perf_counter()-start;after=psutil.Process().cpu_times()
    summary={}
    for split in ('development','holdout'):
        selected=[r for r in rows if r['split']==split];actions=[r for r in selected if r['expected_actions']]
        contextual=[r for r in selected if r['category'] in ('context','clarification')]
        emitted=[r for r in selected if r['actions']]
        summary[split]={'turns':len(selected),'kind_accuracy':sum(r['kind_correct'] for r in selected)/len(selected) if selected else None,
            'parameter_accuracy':sum(r['parameters_correct'] for r in actions)/len(actions) if actions else None,
            'action_precision':sum(r['matched_proposals'] for r in emitted)/sum(len(r['actions']) for r in emitted) if emitted else None,
            'action_recall':sum(r['matched_proposals'] for r in actions)/sum(len(r['expected_actions']) for r in actions) if actions else None,
            'context_accuracy':sum(r['kind_correct'] and r['parameters_correct'] for r in contextual)/len(contextual) if contextual else None,
            'critical_unauthorized_turns':sum(r['critical'] and r['unauthorized_proposal'] for r in selected),
            'unnecessary_clarifications':sum(r['kind']=='clarification' and r['expected_kind']!='clarification' for r in selected)}
    routes={}
    for route in ('fast','semantic','llm','fallback'):
        values=[r['seconds'] for r in rows if r['route']==route]
        routes[route]={'count':len(values),'mean_seconds':float(np.mean(values)) if values else None,
            'median_seconds':float(np.median(values)) if values else None,'p95_seconds':float(np.percentile(values,95)) if values else None}
    report={'summary':summary,'routes':routes,'rss_peak_sampled_bytes':rss,'cpu_machine_percent':100*((after.user+after.system)-(before.user+before.system))/elapsed/(psutil.cpu_count() or 1),
            'note':'Template-heavy text corpus; heldout variants are not an independent real-world voice evaluation. Metrics include guarded fallback when LLM disabled.',
            'failures':[r for r in rows if not r['kind_correct'] or not r['parameters_correct']],'rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'summary':summary,'routes':routes,'failures':len(report['failures'])},indent=2))


if __name__=='__main__':main()
