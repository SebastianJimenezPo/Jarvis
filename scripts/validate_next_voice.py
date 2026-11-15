"""Synthetic local Piper input -> real Rustpotter/VAD/STT -> Next -> real Piper/output.

No microphone audio is read or uploaded. A TEMPORARY synthetic wake reference is
trained. Personal models/configuration are only read. No retries or hidden oracle
confirmations: 'sí' is an explicit synthetic user turn. Failures remain failures.
"""
import argparse
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

CASES={
    'question':[('Abre una aplicación','question',None),('Spotify','simulated','spotify'),('Cancela','cancelled',None)],
    'retained':[('Abre Steam, pero todavía no hagas nada','held','steam'),('Mejor Spotify','held','spotify'),
                ('Autoriza la simulación','review','spotify'),('Sí','simulated','spotify')],
    'provider':[('Necesito Discord abierto','review','discord'),('Sí','simulated','discord')],
}


def main():
    import numpy as np
    from jarvis.core.config import data_dir,load
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.core.single_instance import SingleInstance
    from jarvis.core.events import Kind
    from jarvis.audio.buffers import AudioQueue
    from jarvis.audio.converter import Converter
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.speech.settings import load_voice
    from jarvis.speech.models import registry
    from jarvis.wakeword.rustpotter_adapter import engine_path
    from jarvis.wakeword.calibration import trim_voice
    from jarvis.interface.diagnostics import ResourceSampler
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-remote',action='store_true');parser.add_argument('--free-tier',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.allow_remote!=args.free_tier:parser.error('Both remote opt-ins are required')
    if args.output.exists():parser.error('Preserve prior results')
    root=data_dir();personal=load_voice(root);config=load(root)
    signals={};piper=PiperAdapter(root,personal.voice,personal.cpu_threads,personal.volume);piper.load()
    try:
        for text in {'Jarvis',*[t[0] for rows in CASES.values() for t in rows]}:
            chunks=list(piper.synthesize(text));rate=chunks[0].sample_rate
            audio=np.concatenate([np.zeros(rate//5,dtype=np.float32),*[c.audio_float_array for c in chunks],np.zeros(rate*2,dtype=np.float32)])
            signals[text]=np.frombuffer(Converter(rate).convert(audio),dtype='<i2').astype(np.float32)/32768
    finally:piper.unload()
    source=queue.Queue()
    class Capture:
        def __init__(self,device,capacity):
            self.device={'name':'SYNTHETIC NEXT PCM'};self.rate=16000;self.blocks=AudioQueue(capacity)
            self.overflows=0;self.last_audio=time.monotonic();self.stop_event=threading.Event()
            self.thread=threading.Thread(target=self.run)
        def start(self):self.thread.start()
        def run(self):
            current=np.zeros(0,dtype=np.float32);offset=0
            while not self.stop_event.wait(.02):
                if offset>=len(current):
                    try:current=source.get_nowait();offset=0
                    except queue.Empty:pass
                frame=np.zeros(320,dtype=np.float32)
                if offset<len(current):
                    piece=current[offset:offset+320];frame[:len(piece)]=piece;offset+=len(piece)
                self.last_audio=time.monotonic();self.blocks.put((self.last_audio,frame))
        def close(self):self.stop_event.set();self.thread.join(2)
    report=dict(method=__doc__,remote_text_enabled=args.allow_remote,cases=[],
        limits='Synthetic same-voice input/output, no physical user speech or acoustic echo test. Resource tree includes harness, not a resident-only active-session measurement. No voice substitutions or personal config changes.')
    with SingleInstance(),tempfile.TemporaryDirectory(prefix='jarvis-next-voice-') as folder:
        temporary=Path(folder);(temporary/'models').mkdir();entries=registry(root)
        for item in entries.values():
            item['path']=str(root/'models'/item['path'])
            item['sha256']={str(root/'models'/name):digest for name,digest in item['sha256'].items()}
        (temporary/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
        sample=temporary/'synthetic.wav'
        with wave.open(str(sample),'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
            out.writeframes(trim_voice((signals['Jarvis']*32767).astype('<i2').tobytes()))
        reference=temporary/'synthetic.rpw'
        subprocess.run([str(engine_path()),'calibrate',str(reference),*[str(sample)]*6],capture_output=True,check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        for name,phrases in CASES.items():
            if name=='provider' and not args.allow_remote:continue
            while not source.empty():source.get_nowait()
            voice=replace(personal,enabled=True,dialogue_profile='next',next_remote=(name=='provider' and args.allow_remote),
                next_reasoning='medium',next_timeout_seconds=4.0,log_transcripts=True,first_wait_seconds=8.0,followup_seconds=8.0,retain_seconds=0.0)
            manager=LifecycleManager(replace(config,reference=str(reference),confirmation=False),temporary,Capture,voice_config=voice)
            events=[];wakes=[];original_notify=manager.voice.notify
            def observed(event):events.append(dict(event));original_notify(event)
            manager.voice.notify=observed
            manager.bus.subscribe(lambda event:wakes.append(dict(event.detail)) if event.kind==Kind.WAKEWORD_DETECTED else None)
            sampler=ResourceSampler();sampler.sample();manager.start();rows=[]
            try:
                until=time.monotonic()+10
                while manager.snapshot()['state']!='DORMANT' and time.monotonic()<until:time.sleep(.03)
                source.put(signals['Jarvis']);until=time.monotonic()+30
                while time.monotonic()<until:
                    manager_snapshot=manager.snapshot()
                    if wakes and any(e['kind']=='activation_only_or_ambiguous' for e in events) and manager.voice.state=='WAITING_FOR_SPEECH':break
                    time.sleep(.03)
                ready=bool(wakes) and any(e['kind']=='activation_only_or_ambiguous' for e in events) and manager.voice.state=='WAITING_FOR_SPEECH'
                for text,expected,target in phrases:
                    if not ready:
                        rows.append(dict(expected_text=text,passed=False,failure_stage='wake_or_preparation'));break
                    marker=len(events);time.sleep(.5);source.put(signals[text]);until=time.monotonic()+35;final=None
                    while time.monotonic()<until:
                        current=events[marker:]
                        finals=[e for e in current if e['kind']=='transcript' and e.get('final')]
                        if finals:final=finals[-1]
                        if final and any(e['kind']=='turn_completed' for e in current):break
                        if any(e['kind']=='voice_error' for e in current):break
                        time.sleep(.03)
                    current=events[marker:];decisions=[e['decision'] for e in current if e['kind']=='intelligence_decision']
                    decision=decisions[-1] if decisions else {}
                    actual='question' if decision.get('pending_question') else 'review' if decision.get('review_pending') else decision.get('disposition')
                    plan=decision.get('proposed_plan') if expected=='review' else decision.get('plan')
                    passed=actual==expected and (target is None or any(i['target']==target for i in (plan or [])))
                    timings=[e for e in current if e['kind']=='voice_latency']
                    row=dict(expected_text=text,expected=expected,target=target,transcript=final.get('text') if final else None,
                        passed=passed,decision=decision,latencies=timings,
                        failure_stage=None if passed else 'stt_or_context_or_interpretation')
                    rows.append(row);sampler.sample();print(name,text,'PASS' if passed else 'FAIL',flush=True)
                    ready=manager.voice.active
                snapshot=manager.snapshot()
            finally:manager.stop();sampler.sample()
            report['cases'].append(dict(name=name,rows=rows,expected_turns=len(phrases),wake_events=wakes,
                resources=sampler.report(),snapshot=snapshot,passed=len(rows)==len(phrases) and all(r['passed'] for r in rows)))
            args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report['summary']=dict(turns=sum(len(c['rows']) for c in report['cases']),
        turns_passed=sum(r['passed'] for c in report['cases'] for r in c['rows']),
        cases_passed=sum(c['passed'] for c in report['cases']),cases=len(report['cases']))
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['summary']),flush=True)


if __name__=='__main__':main()
