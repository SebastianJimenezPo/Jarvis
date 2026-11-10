"""Repeated real worker load/unload with silence; no capture or playback."""
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import psutil
    from jarvis.core.config import data_dir
    from jarvis.core.voice_session import VoiceSessionManager
    from jarvis.speech.settings import VoiceConfig
    def memory():
        p=psutil.Process()
        return sum(x.memory_info().rss for x in [p,*p.children(recursive=True)] if x.is_running())
    samples=[];events=[]
    manager=VoiceSessionManager(data_dir(),events.append,replace(VoiceConfig(),enabled=True,
                  engine='moonshine-small',tts_enabled=False,first_wait_seconds=1,retain_seconds=0))
    try:
        for i in range(5):
            before=memory();peak=before;t=time.monotonic()
            manager.start(str(i),bytes(32000))
            deadline=time.monotonic()+20
            while (manager.active or manager.process) and time.monotonic()<deadline:
                manager.poll();peak=max(peak,memory());time.sleep(0.02)
            if manager.active or manager.error:
                raise RuntimeError(manager.snapshot())
            samples.append({'cycle':i,'before_rss_tree':before,'loaded_peak_rss_tree':peak,
                            'after_release_rss_tree':memory(),'seconds':time.monotonic()-t})
    finally:
        manager.close()
    Path('docs/reports/voice-resource-cycles.json').write_text(json.dumps({'scenario':'5 real model worker load/unload cycles, silence only, no hardware audio','cycles':samples,'events':events},indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
