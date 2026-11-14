"""Real synthetic Rustpotter→VAD→Moonshine→dialogue→Piper, fixed A–F stimuli.

This trains a TEMPORARY synthetic wake reference; it never changes the personal
reference or microphone. Synthetic Capture supplies PCM; playback is physical.
No real-user audio or acoustic echo test. Failed original phrases stay failed.
"""
import argparse
import json
import queue
import statistics
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
 'A_lights':[
  ('Pon las luces rojas','action_proposal','set_light_color',{'color':'red'}),
  ('No, mejor azules','action_proposal','set_light_color',{'color':'blue'}),
  ('Y bájales el brillo','action_proposal','set_light_brightness',{'delta':-10}),
  ('Mejor al treinta por ciento','action_proposal','set_light_brightness',{'value':30})],
 'B_clarification':[
  ('Abre una aplicación','clarification',None,None),('Steam','action_proposal','open_application',{}),
  ('No, mejor Chrome','action_proposal','open_application',{})],
 'C_polarity':[
  ('No abras Steam','negated',None,None),('Cuando termine de jugar, abre Steam','deferred_request',None,None),
  ('Abre Steam','action_proposal','open_application',{})],
 'D_cancel':[
  ('Pon las luces azules','action_proposal','set_light_color',{'color':'blue'}),('Cancela','cancel',None,None),
  ('No canceles la siguiente solicitud','negated',None,None)],
 'E_conversation':[
  ('¿Qué es la memoria RAM?','conversation',None,None),('Explícamelo más fácil','conversation',None,None),
  ('Dame un ejemplo','conversation',None,None)],
 'F_historical_stt':[
  ('Por favor pon la luz principal de color rojo','action_proposal','set_light_color',{'color':'red'}),
  ('Mejor azules','action_proposal','set_light_color',{'color':'blue'})]}


def summarize(report):
    rows=[row for case in report['cases'] for row in case['rows']]
    values=[row['voice_end_to_playback_seconds'] for row in rows if row.get('voice_end_to_playback_seconds') is not None]
    return {'cases':len(report['cases']),'cases_passed':sum(case['passed'] for case in report['cases']),
        'turns':len(rows),'turns_passed':sum(row['passed'] for row in rows),
        'turns_failed':sum(not row['passed'] for row in rows),
        'criterion':'Expected interpretation kind and exact action intent/target/parameters where requested. Does not score conversational answer correctness or exact STT.',
        'voice_end_to_playback_seconds':{'count':len(values),'min':min(values) if values else None,
            'median':statistics.median(values) if values else None,'max':max(values) if values else None}}


def main():
    import numpy as np
    from jarvis.core.config import data_dir,load
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.core.single_instance import SingleInstance
    from jarvis.audio.buffers import AudioQueue
    from jarvis.audio.converter import Converter
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.speech.settings import load_voice,save_voice
    from jarvis.speech.models import registry
    from jarvis.intelligence.settings import load_intelligence,save_intelligence
    from jarvis.intelligence.language import normalize
    from jarvis.wakeword.rustpotter_adapter import engine_path
    from jarvis.wakeword.calibration import trim_voice
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=[*CASES,'all'],default='all')
    parser.add_argument('--recovery',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('docs/reports/phase31-voice-integration.json'))
    args=parser.parse_args();root=data_dir();config=load(root);report={'method':__doc__,'harness_revision':3,'cases':[]}
    if args.output.exists():raise RuntimeError('Preserve the first integration result; choose a new output for another run')
    selected=CASES if args.case=='all' else {args.case:CASES[args.case]}
    voice=PiperAdapter(root,'es_MX-ald-medium');voice.load();signals={}
    try:
        for text in ['Jarvis',*[row[0] for rows in selected.values() for row in rows]]:
            chunks=list(voice.synthesize(text));rate=chunks[0].sample_rate
            samples=np.concatenate([np.zeros(rate//5,dtype=np.float32),*[c.audio_float_array for c in chunks],np.zeros(rate*2,dtype=np.float32)])
            signals[text]=np.frombuffer(Converter(rate).convert(samples),dtype='<i2').astype(np.float32)/32768
    finally:voice.unload()
    source=queue.Queue()
    class Capture:
        def __init__(self,device,capacity):
            self.device={'name':'SYNTHETIC PHASE31 PCM'};self.rate=16000;self.blocks=AudioQueue(capacity)
            self.overflows=0;self.last_audio=time.monotonic();self.stop=threading.Event();self.thread=threading.Thread(target=self.run)
        def start(self):self.thread.start()
        def run(self):
            current=np.zeros(0,dtype=np.float32);offset=0
            while not self.stop.wait(.02):
                if offset>=len(current):
                    try:current=source.get_nowait();offset=0
                    except queue.Empty:pass
                frame=np.zeros(320,dtype=np.float32)
                if offset<len(current):
                    chunk=current[offset:offset+320];frame[:len(chunk)]=chunk;offset+=len(chunk)
                self.last_audio=time.monotonic();self.blocks.put((self.last_audio,frame))
        def close(self):self.stop.set();self.thread.join(2)
    with SingleInstance(),tempfile.TemporaryDirectory(prefix='jarvis-phase31-full-') as directory:
        temporary=Path(directory);(temporary/'models').mkdir();entries=registry(root)
        for row in entries.values():
            row['path']=str(root/'models'/row['path']);row['sha256']={str(root/'models'/k):v for k,v in row['sha256'].items()}
        (temporary/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
        sample=temporary/'synthetic-wake.wav'
        pcm=trim_voice((signals['Jarvis']*32767).astype('<i2').tobytes())
        with wave.open(str(sample),'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(pcm)
        reference=temporary/'synthetic.rpw'
        subprocess.run([str(engine_path()),'calibrate',str(reference),*[str(sample)]*6],check=True,capture_output=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        save_voice(temporary,replace(load_voice(root),enabled=True,log_transcripts=True,first_wait_seconds=8.0,
            followup_seconds=4.0,retain_seconds=0.0,stt_recovery_enabled=args.recovery))
        save_intelligence(temporary,replace(load_intelligence(root),enabled=True,semantic_enabled=False,log_text=True))
        for name,phrases in selected.items():
            while not source.empty():source.get_nowait()
            manager=LifecycleManager(replace(config,reference=str(reference),confirmation=False),temporary,Capture)
            events=[];notify=manager.voice.notify
            def observed(event):events.append(dict(event));notify(event)
            manager.voice.notify=observed;manager.start();rows=[];wake_events=[]
            from jarvis.core.events import Kind
            manager.bus.subscribe(lambda event:wake_events.append(dict(event.detail)) if event.kind==Kind.WAKEWORD_DETECTED else None)
            def wake():
                until=time.monotonic()+12
                while manager.snapshot()['state']!='DORMANT' or time.monotonic()<manager.machine.next_wake:
                    if time.monotonic()>until:return False
                    time.sleep(.03)
                count=len(wake_events);event_start=len(events);source.put(signals['Jarvis'])
                until=time.monotonic()+8
                while len(wake_events)==count:
                    if time.monotonic()>until:return False
                    time.sleep(.03)
                # Cold STT preparation can exceed a fixed two-second sleep. Wait
                # for the wake-only turn to be consumed, or its transcript could
                # be wrongly attributed to the next command by the harness.
                until=time.monotonic()+20
                while time.monotonic()<until:
                    consumed=[e for e in events[event_start:] if e['kind']=='activation_only_or_ambiguous']
                    if consumed and manager.voice.state=='WAITING_FOR_SPEECH':
                        time.sleep(.5)
                        return True
                    # The wake observer runs BEFORE Lifecycle handles the event;
                    # IDLE here can mean the worker has not been started yet.
                    if manager.snapshot()['state']=='DEGRADED':return False
                    time.sleep(.03)
                return False
            end=None
            try:
                for text,expected_kind,intent,parameters in phrases:
                    if manager.snapshot()['state']!='AWAKE' and not wake():
                        rows.append({'expected_text':text,'passed':False,'failure_stage':'wake_or_preparation'});break
                    existing={(e.get('session_id'),e.get('turn_id')) for e in events if e['kind']=='transcript' and e.get('final')}
                    time.sleep(.5);source.put(signals[text]);until=time.monotonic()+50;final=None
                    while time.monotonic()<until:
                        finals=[e for e in events if e['kind']=='transcript' and e.get('final') and (e.get('session_id'),e.get('turn_id')) not in existing]
                        if finals:final=finals[-1]
                        if final and manager.voice.state in ('WAITING_FOR_SPEECH','WAITING_FOR_FOLLOWUP','IDLE'):break
                        time.sleep(.03)
                    decision_events=[e for e in events if final and e['kind']=='intelligence_decision' and e.get('session_id')==final.get('session_id') and e.get('turn_id')==final.get('turn_id')]
                    decision=decision_events[-1]['decision'] if decision_events else None
                    actual=decision['interpretation'] if decision else {}
                    passed=actual.get('kind')==expected_kind
                    target=('steam' if text in ('Steam','Abre Steam') else 'chrome' if text=='No, mejor Chrome' else 'main_light' if intent and intent.startswith('set_light_') else None)
                    if intent:passed=passed and len(actual.get('actions',[]))==1 and any(a['intent']==intent and a['parameters']==parameters and (target is None or a['target']==target) for a in actual.get('actions',[]))
                    else:passed=passed and not actual.get('actions')
                    turn_events=[e for e in events if final and e.get('session_id')==final.get('session_id') and e.get('turn_id')==final.get('turn_id')]
                    row={'expected_text':text,'expected_kind':expected_kind,'expected_intent':intent,'expected_parameters':parameters,
                        'primary_transcript':final.get('text') if final else None,'decision':decision,'passed':bool(passed),
                        'failure_stage':None if passed else 'stt_or_normalization' if final and normalize(final.get('text',''))!=normalize(text) else 'interpretation_or_session',
                        'timing_events':[e for e in turn_events if e['kind'] in ('speech_started','speech_ended','transcription_timing','dialogue_timing','synthesis_first_chunk','playback_started')]}
                    endings=[e for e in turn_events if e['kind']=='speech_ended']
                    starts=[e for e in turn_events if e['kind']=='playback_started']
                    row['voice_end_to_playback_seconds']=(starts[0]['monotonic']-endings[-1]['estimated_voice_end_monotonic']) if starts and endings else None
                    rows.append(row);print(name,text,'PASS' if passed else 'FAIL',flush=True)
                end=manager.snapshot()
            finally:manager.stop()
            report['cases'].append({'name':name,'wake_events':wake_events,'rows':rows,'snapshot_before_stop':end,
                'wake_only_events':[e for e in events if e['kind']=='activation_only_or_ambiguous'],
                'voice_events':events,
                'passed':len(rows)==len(phrases) and all(row['passed'] for row in rows)})
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    report['passed']=all(case['passed'] for case in report['cases'])
    report['summary']=summarize(report)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
