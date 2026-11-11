"""Isolated real voice-model memory: old eager embedding load versus current chat gate.

No microphone, playback, user audio or live LLM. The controlled comparison uses
the same current libraries/CPU policy in both children; it isolates the former
unnecessary embedding load rather than reproducing every old runtime setting.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def child(scenario):
    import psutil
    from jarvis.core.config import data_dir
    from jarvis.speech.settings import VoiceConfig
    from jarvis.system.voice_resources import configure_voice_process
    from jarvis.speech.recognition import make_engine
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.audio.vad import SpeechActivityDetector
    from jarvis.intelligence.dialogue_manager import DialogueManager
    from jarvis.intelligence.settings import IntelligenceConfig
    root=data_dir();config=VoiceConfig();configure_voice_process(config.cpu_threads)
    process=psutil.Process();stt=make_engine(root,config,lambda text:None)
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):return 'La RAM conserva datos temporales; el almacenamiento guarda archivos.'
        def unload(self):pass
    manager=DialogueManager(root,IntelligenceConfig(),client=Client())
    tts=PiperAdapter(root,config.voice,config.cpu_threads,config.volume)
    try:
        stt.load();vad=SpeechActivityDetector(root);tts.load()
        for _ in tts.synthesize('Estoy listo para ayudarte con el computador.'):pass
        voice_rss=process.memory_info().rss
        question='Dime la diferencia entre RAM y almacenamiento'
        if scenario=='former_eager_embedding':manager.semantic.candidate(question)
        start=time.perf_counter();decision,_=manager.interpret(question)
        # Keep the measured state alive long enough for the parent sampler.
        time.sleep(.3)
        print(json.dumps({'scenario':scenario,'voice_rss_bytes':voice_rss,'after_question_rss_bytes':process.memory_info().rss,
            'embedding_loaded':manager.semantic.provider is not None,'interpretation_plus_sampling_hold_seconds':time.perf_counter()-start,
            'route':decision.route,'affinity':process.cpu_affinity(),'cpu_threads':config.cpu_threads,
            'note':'Real Moonshine, Silero, Piper and optional E5; mocked LLM reply; no mic/playback; two fresh processes.'}),flush=True)
    finally:stt.unload();tts.unload();manager.close()


def main():
    import psutil
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--child',choices=['former_eager_embedding','gated_chat'])
    p.add_argument('--output',type=Path,default=Path('docs/reports/phase3-feedback-memory.json'))
    args=p.parse_args()
    if args.child:return child(args.child)
    rows=[]
    for scenario in ('former_eager_embedding','gated_chat'):
        process=subprocess.Popen([sys.executable,__file__,'--child',scenario],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        peak=0;cpu_peak=0;sampled=psutil.Process(process.pid);previous={};last=time.perf_counter()
        while process.poll() is None:
            try:
                # Python on this Windows installation has a launcher process;
                # models live in its descendant, not necessarily Popen.pid.
                process_rows={}
                for item in [sampled,*sampled.children(recursive=True)]:
                    try:
                        cpu=item.cpu_times();process_rows[item.pid]=(cpu.user+cpu.system,item.memory_info().rss)
                    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                now=time.perf_counter()
                delta=sum(max(0,cpu-previous.get(pid,cpu)) for pid,(cpu,_) in process_rows.items())
                cpu_peak=max(cpu_peak,100*delta/max(now-last,.001)/(psutil.cpu_count() or 1))
                previous={pid:cpu for pid,(cpu,_) in process_rows.items()};last=now
                peak=max(peak,sum(rss for _,rss in process_rows.values()))
            except psutil.NoSuchProcess:break
            time.sleep(.1)
        stdout,stderr=process.communicate(timeout=10)
        if process.returncode:raise RuntimeError(stderr)
        row=json.loads(stdout.strip().splitlines()[-1]);row.update(sampled_peak_rss_bytes=peak,sampled_cpu_machine_peak_percent=cpu_peak)
        rows.append(row)
    args.output.write_text(json.dumps({'method':__doc__,'results':rows},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
