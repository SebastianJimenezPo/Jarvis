"""Synthetic microphone + real voice engines + phase-3 context + actual Piper output."""
import json,sys,time,threading,tempfile,queue
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--short-correction',action='store_true')
    args=parser.parse_args()
    import numpy as np
    from jarvis.core.config import Config,data_dir,load
    from jarvis.speech.settings import VoiceConfig,save_voice
    from jarvis.speech.models import registry
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.audio.buffers import AudioQueue
    from jarvis.audio.converter import Converter
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.intelligence.settings import IntelligenceConfig,save_intelligence
    voice=PiperAdapter(data_dir(),'es_MX-ald-medium');voice.load()
    signals=[]
    utterances=['Pon las luces rojas' if args.short_correction else 'Por favor pon la luz principal de color rojo',
                'Mejor azules' if args.short_correction else 'No, mejor cambia las luces a color azul']
    for text in utterances:
        chunks=list(voice.synthesize(text));rate=chunks[0].sample_rate
        samples=np.concatenate([c.audio_float_array for c in chunks]+[np.zeros(rate*2,dtype=np.float32)])
        pcm=Converter(rate).convert(samples)
        signals.append(np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768)
    voice.unload();source=queue.Queue()
    class Capture:
        def __init__(self,device,capacity):
            self.device={'name':'SYNTHETIC PHASE3 INPUT'};self.rate=16000;self.blocks=AudioQueue(capacity)
            self.overflows=0;self.last_audio=time.monotonic();self.stop=threading.Event();self.thread=threading.Thread(target=self.run)
        def start(self):self.thread.start()
        def run(self):
            current=np.zeros(0,dtype=np.float32);offset=0
            while not self.stop.wait(0.02):
                if offset>=len(current):
                    try:current=source.get_nowait();offset=0
                    except queue.Empty:pass
                samples=np.zeros(320,dtype=np.float32)
                if offset<len(current):
                    chunk=current[offset:offset+320];samples[:len(chunk)]=chunk;offset+=len(chunk)
                self.last_audio=time.monotonic();self.blocks.put((self.last_audio,samples))
        def close(self):self.stop.set();self.thread.join(timeout=2)
    with tempfile.TemporaryDirectory(prefix='jarvis phase3 integration ') as directory:
        root=Path(directory);(root/'models').mkdir()
        entries=registry(data_dir())
        for entry in entries.values():
            entry['path']=str(data_dir()/'models'/entry['path'])
            entry['sha256']={str(data_dir()/'models'/k):v for k,v in entry['sha256'].items()}
        (root/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
        save_voice(root,replace(VoiceConfig(),enabled=True,first_wait_seconds=6,followup_seconds=2,retain_seconds=0,log_transcripts=True))
        save_intelligence(root,replace(IntelligenceConfig(),enabled=True,semantic_enabled=False,llm_enabled=False))
        config=replace(Config(),reference=str(load(data_dir()).reference_path(data_dir())),confirmation=False)
        manager=LifecycleManager(config,root,Capture);manager.start();deadline=time.monotonic()+55;decisions=[]
        try:
            while manager.snapshot()['state']!='DORMANT' and time.monotonic()<deadline:time.sleep(.02)
            manager.command('wake');time.sleep(.1);source.put(signals[0]);next_index=1;last_turn=None
            while time.monotonic()<deadline:
                snapshot=manager.snapshot();v=snapshot.get('voice',{});decision=v.get('intelligence')
                if decision and decision['turn_id']!=last_turn:
                    decisions.append({**decision,'synthetic_recognized_text':v.get('last_transcript')});last_turn=decision['turn_id']
                if next_index==1 and v.get('state')=='WAITING_FOR_FOLLOWUP' and v['metrics']['turns']==1:
                    # Honor echo guard; the production user must wait until response ends too.
                    time.sleep(.5);source.put(signals[1]);next_index=2
                if next_index==2 and snapshot['state']=='DORMANT':break
                time.sleep(.03)
            before_stop=manager.snapshot()
            failure=None
            if len(decisions)!=2 or before_stop['state']!='DORMANT':failure='Voice cycle did not complete'
            colors=[d['interpretation']['actions'][0]['parameters'].get('color') if d['interpretation']['actions'] else None for d in decisions]
            if colors!=['red','blue']:failure='Synthetic speech was not correctly interpreted as red -> blue'
        finally:manager.stop()
        report={'scenario':'Synthetic mic, real Rustpotter loaded, diagnostic activation, Moonshine+VAD+phase3 context+Piper/default output. No physical light actions, no real-user audio, no physical echo test.',
                'utterances':utterances,'decisions':decisions,'snapshot':manager.snapshot(),'passed':failure is None,'failure':failure}
        Path('docs/reports/phase3-voice-integration.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
