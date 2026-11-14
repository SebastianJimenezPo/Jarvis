"""Repeated, sequential CPU-only Qwen benchmark. No microphone, actions or background inference."""
import argparse
import json
import sys
import time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_sampling import OllamaMeasurement


def main():
    from jarvis.intelligence.ollama_client import OllamaClient
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.intelligence.contracts import ModelInterpretation
    from jarvis.intelligence.dialogue_manager import INTERPRET_PROMPT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions',type=int,default=3)
    parser.add_argument('--output',type=Path,default=Path('docs/reports/phase31-performance.json'))
    args=parser.parse_args()
    if not 2<=args.repetitions<=5:parser.error('2–5 repetitions required')
    brief=[{'role':'system','content':'Eres Jarvis. Responde en español con una sola frase breve.'},{'role':'user','content':'¿Qué es la memoria RAM?'}]
    contextual=[*brief,{'role':'assistant','content':'La RAM guarda temporalmente datos que el computador está utilizando.'},
                {'role':'user','content':'Dame un ejemplo sencillo.'}]
    structured=[{'role':'system','content':INTERPRET_PROMPT},
        {'role':'user','content':json.dumps({'request':'Baja el volumen al treinta por ciento','catalog':{'set_volume':{'value':'int:0..100'}}},ensure_ascii=False)}]
    rows=[]
    if OllamaClient(IntelligenceConfig()).running():raise RuntimeError('Shared service has a loaded model; close other sessions before this isolated comparison')
    try:
        for threads in (2,3,4):
            for repetition in range(args.repetitions):
                for workload,messages,schema in [('brief',brief,None),('context',contextual,None),('structured',structured,ModelInterpretation.model_json_schema())]:
                    cfg=replace(IntelligenceConfig(),cpu_threads=threads,timeout_seconds=45.0)
                    client=OllamaClient(cfg)
                    try:
                        for state in ('cold','warm'):
                            row={'cpu_threads':threads,'repetition':repetition,'workload':workload,'state':state}
                            try:
                                with OllamaMeasurement() as measurement:answer=client.chat(messages,schema)
                                row.update(measurement.report,metrics=dict(client.last_metrics),answer=answer)
                                metrics=client.last_metrics
                                row['tokens_per_second']=(metrics.get('eval_count') or 0)/max((metrics.get('eval_duration') or 0)/1e9,1e-9)
                                row['vram_bytes']=sum(item.get('size_vram',0) for item in client.running())
                                if schema:
                                    try:row['valid_schema']=bool(ModelInterpretation.model_validate_json(answer))
                                    except ValueError:row['valid_schema']=False
                            except Exception as exc:row['error']=type(exc).__name__
                            rows.append(row)
                            args.output.write_text(json.dumps({'method':__doc__,'note':'Same prompts and seed, 3 workload types, 2/3/4 threads, cold after explicit unload and warm second request. Disk cache/thermal/order effects remain. CPU/RSS include Ollama server and all descendants; RSS may double-count shared pages. Deadline 45 s for measurement versus 12 s runtime. Not end-to-end voice latency.','rows':rows},indent=2,ensure_ascii=False),encoding='utf-8')
                            print(threads,repetition,workload,state,round(row.get('elapsed_seconds',0),3),row.get('error','ok'),flush=True)
                    finally:client.unload()
    finally:
        print('Completed rows:',len(rows),flush=True)


if __name__=='__main__':main()
