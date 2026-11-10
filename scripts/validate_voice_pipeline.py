"""20 process-backed sessions from synthetic audio, TTS disabled: control-flow test only."""
import json
import sys
import time
import wave
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import numpy as np
    from jarvis.core.config import data_dir
    from jarvis.core.voice_session import VoiceSessionManager
    from jarvis.speech.settings import VoiceConfig
    from jarvis.audio.converter import Converter
    path=Path('build/synthetic-speech/01.wav')
    with wave.open(str(path),'rb') as source:
        rate=source.getframerate()
        raw=np.frombuffer(source.readframes(source.getnframes()),dtype='<i2').astype(np.float32)/32768
    pcm=Converter(rate).convert(np.concatenate([raw,np.zeros(rate,dtype=np.float32)]))
    results=[]
    manager=VoiceSessionManager(data_dir(),results.append,replace(VoiceConfig(),enabled=True,
                    engine='moonshine-small',tts_enabled=False,log_transcripts=True,first_wait_seconds=1,followup_seconds=1))
    try:
        for session in range(20):
            print('Synthetic session',session+1,flush=True)
            # First part is supplied as pre-roll, rest through the ordinary live queue.
            manager.start(str(session),pcm[:16000])
            for offset in range(16000,len(pcm),640):
                manager.feed(pcm[offset:offset+640],time.monotonic())
            deadline=time.monotonic()+30
            while manager.active and time.monotonic()<deadline:
                manager.poll()
                time.sleep(0.01)
            if manager.active or manager.error:
                raise RuntimeError(manager.snapshot())
            finals=[e for e in results if e.get('session_id')==str(session) and e.get('kind')=='transcript' and e.get('final')]
            if not finals or not finals[0].get('text'):
                raise RuntimeError(f'No final transcript in synthetic session {session}')
        output={'origin':'Synthetic Piper audio, no physical microphone, no playback','sessions':20,
                'supervisor':manager.snapshot(),'events':results}
        Path('docs/reports/voice-pipeline-synthetic.json').write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding='utf-8')
    finally:
        manager.close()


if __name__=='__main__':
    main()
