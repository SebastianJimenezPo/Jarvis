"""Real lifecycle + Rustpotter + STT + VAD + Piper/output, synthetic mic input."""
import json
import sys
import time
import wave
import threading
import tempfile
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import numpy as np
    from jarvis.core.config import Config,data_dir,load
    from jarvis.speech.settings import VoiceConfig,save_voice
    from jarvis.speech.models import registry
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.audio.buffers import AudioQueue
    from jarvis.audio.converter import Converter
    with wave.open('build/synthetic-speech/01.wav','rb') as source:
        rate=source.getframerate()
        raw=np.frombuffer(source.readframes(source.getnframes()),dtype='<i2').astype(np.float32)/32768
    pcm=Converter(rate).convert(np.concatenate([raw,np.zeros(rate,dtype=np.float32)]))
    signal=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
    play=threading.Event()
    class Capture:
        def __init__(self,device,capacity):
            self.device={'name':'SYNTHETIC INPUT'};self.rate=16000
            self.blocks=AudioQueue(capacity);self.overflows=0;self.last_audio=time.monotonic()
            self.stop=threading.Event();self.thread=threading.Thread(target=self.run)
        def start(self): self.thread.start()
        def run(self):
            offset=0
            while not self.stop.wait(0.02):
                samples=np.zeros(320,dtype=np.float32)
                if play.is_set() and offset<len(signal):
                    chunk=signal[offset:offset+320];samples[:len(chunk)]=chunk;offset+=len(chunk)
                self.last_audio=time.monotonic();self.blocks.put((self.last_audio,samples))
        def close(self): self.stop.set();self.thread.join(timeout=2)
    events=[]
    with tempfile.TemporaryDirectory(prefix='jarvis phase2 integration ') as directory:
        root=Path(directory);(root/'models').mkdir()
        entries=registry(data_dir())
        for item in entries.values():
            item['path']=str(data_dir()/'models'/item['path'])
            item['sha256']={str(data_dir()/'models'/k):v for k,v in item['sha256'].items()}
        (root/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
        save_voice(root,replace(VoiceConfig(),enabled=True,first_wait_seconds=3,followup_seconds=1,retain_seconds=0))
        config=replace(Config(),reference=str(load(data_dir()).reference_path(data_dir())),confirmation=False)
        manager=LifecycleManager(config,root,Capture)
        manager.bus.subscribe(events.append)
        manager.start();deadline=time.monotonic()+35
        try:
            while manager.snapshot()['state']!='DORMANT' and time.monotonic()<deadline:time.sleep(0.02)
            manager.command('wake');time.sleep(0.1);play.set()
            awake=False
            while time.monotonic()<deadline:
                snapshot=manager.snapshot();awake=awake or snapshot['state']=='AWAKE'
                if awake and snapshot['state']=='DORMANT':break
                time.sleep(0.05)
            snapshot=manager.snapshot()
            if not awake or snapshot['state']!='DORMANT' or snapshot['voice']['metrics']['turns']!=1 or snapshot['voice']['last_error']:
                raise RuntimeError(snapshot)
        finally:manager.stop()
        report={'scenario':'Manual diagnostic activation, synthetic microphone audio, real Rustpotter/VAD/STT/Piper and default output. Physical echo not tested.',
                'snapshot':manager.snapshot(),'global_events':[{'kind':e.kind.value,**e.detail} for e in events]}
        Path('docs/reports/voice-lifecycle-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))


if __name__=='__main__': main()
