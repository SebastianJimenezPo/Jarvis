"""Measure external Ollama process tree during one local CPU request and release."""
import json,sys,time,threading
import argparse
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import psutil
    from jarvis.intelligence.ollama_client import OllamaClient
    from jarvis.intelligence.settings import IntelligenceConfig
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpu-threads',type=int,default=2)
    parser.add_argument('--output',type=Path,default=Path('docs/reports/llm-resource-sample.json'))
    args=parser.parse_args()
    def sample():
        rows={};selected={}
        for p in psutil.process_iter(['pid','name']):
            if (p.info['name'] or '').lower().startswith('ollama'):
                selected[p.pid]=p
                try:selected.update({child.pid:child for child in p.children(recursive=True)})
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        for p in selected.values():
                try:
                    cpu=p.cpu_times();rows[p.pid]={'cpu':cpu.user+cpu.system,'rss':p.memory_info().rss}
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        return rows
    client=OllamaClient(replace(IntelligenceConfig(),cpu_threads=args.cpu_threads));before=sample();snapshots=[];stop=threading.Event()
    def monitor():
        while not stop.wait(.1):snapshots.append(sample())
    thread=threading.Thread(target=monitor);thread.start();start=time.perf_counter()
    try:
        answer=client.chat([{'role':'system','content':'Responde en español con una frase.'},{'role':'user','content':'¿Qué es una variable?'}])
        elapsed=time.perf_counter()-start;after=sample();running=client.running();metrics=client.last_metrics.copy()
    finally:
        stop.set();thread.join();client.unload()
    delta=sum(max(0,row['cpu']-before.get(pid,{}).get('cpu',0)) for pid,row in after.items())
    report={'scenario':'Isolated Ollama CPU conversation, no voice or mic processing','model':client.config.model,'answer':answer,
        'elapsed_seconds':elapsed,'cpu_threads':args.cpu_threads,'cpu_machine_percent':100*delta/elapsed/(psutil.cpu_count() or 1),
        'ollama_rss_peak_sampled_bytes':max(sum(r['rss'] for r in s.values()) for s in snapshots+[after]),
        'running_model_snapshot':running,'models_after_release':client.running(),'metrics':metrics,
        'method':'100-ms process samples, Ollama server AND all descendants (including differently named inference runners). CPU user+kernel delta for surviving/new PIDs / wall / logical CPUs; shared pages may be double counted. No sustained GPU utilization measurement.'}
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
