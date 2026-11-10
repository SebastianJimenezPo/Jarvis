import queue
import threading
import time
from dataclasses import replace
import numpy as np
import pytest
from jarvis.speech.settings import VoiceConfig


@pytest.mark.parametrize('activation,continues,expected_plays',[(False,False,1),(True,False,0),(True,True,1)])
def test_half_duplex_discards_queued_echo_and_cancels(monkeypatch,tmp_path,activation,continues,expected_plays):
    from jarvis.speech.worker import voice_worker
    from jarvis.speech import recognition,piper_adapter
    from jarvis.audio import vad,playback
    inbox=queue.Queue();outbox=queue.Queue();cancel=threading.Event()
    calls=[]
    class Engine:
        def load(self): pass
        def start_turn(self,turn): calls.append(('turn',turn))
        def feed_audio(self,samples,sample_rate=16000): pass
        def finish_turn(self): return '¿Me escuchas?'
        def cancel_turn(self): pass
        def unload(self): pass
    class VAD:
        def __init__(self,root): pass
        def reset(self): pass
        def probability(self,samples): return float(np.mean(abs(samples))>0.1)
    class TTS:
        def __init__(self,*args): pass
        def load(self): pass
        def synthesize(self,text): return [text]
        def unload(self): pass
    echo=(np.ones(512*40,dtype=np.float32)*10000).astype('<i2').tobytes()
    class Playback:
        def __init__(self,*args): pass
        def play(self,chunks,cancel,emit):
            calls.append(('play',list(chunks)))
            emit('playback_started')
            # This captured voice belongs to the output window, even if queued for later.
            inbox.put(('audio','s',time.monotonic(),echo))
            cancel.set()
    monkeypatch.setattr(recognition,'make_engine',lambda *args:Engine())
    monkeypatch.setattr(vad,'SpeechActivityDetector',VAD)
    monkeypatch.setattr(piper_adapter,'PiperAdapter',TTS)
    monkeypatch.setattr(playback,'SpeechPlaybackManager',Playback)
    speech=(np.ones(512*12)*10000).astype('<i2').tobytes()+bytes(512*25*2)
    config=replace(VoiceConfig(),first_wait_seconds=1,followup_seconds=1,echo_guard_seconds=0.1)
    thread=threading.Thread(target=voice_worker,args=(inbox,outbox,cancel,str(tmp_path),config))
    thread.start()
    inbox.put(('session','s',speech if not continues else speech[:512*12*2],activation))
    if continues:
        inbox.put(('audio','s',time.monotonic(),speech))
    events=[]
    deadline=time.monotonic()+5
    try:
        while time.monotonic()<deadline:
            event=outbox.get(timeout=3)
            events.append(event)
            if event['kind']=='session_end': break
        assert not any(e['kind']=='voice_error' for e in events),events
        assert len([c for c in calls if c[0]=='turn'])==1
        assert len([c for c in calls if c[0]=='play'])==expected_plays
        assert any(e['kind']=='playback_ended' and e['cancelled'] for e in events)==bool(expected_plays)
    finally:
        inbox.put(('stop',));thread.join(timeout=3)
    assert not thread.is_alive()


def test_old_session_results_are_ignored(tmp_path):
    from jarvis.core.voice_session import VoiceSessionManager
    received=[]
    manager=VoiceSessionManager(tmp_path,received.append)
    assert manager.process is None
    manager.active=True;manager.session_id='new';manager.state='WAITING_FOR_SPEECH'
    class Process:
        def is_alive(self): return True
    manager.process=Process();manager.outbox=queue.Queue()
    manager.outbox.put({'kind':'session_end','session_id':'old','reason':'stale'})
    manager.outbox.put({'kind':'transcript','session_id':'new','text':'private','final':True})
    manager.poll()
    assert manager.active
    assert len(received)==1 and received[0]['session_id']=='new'
    assert 'text' not in received[0]  # privacy defaults are enforced before observers/logs
    manager.process=None


def test_resident_launcher_safe_for_windows_spawn(monkeypatch):
    import runpy
    from pathlib import Path
    import jarvis.__main__
    def forbidden():
        raise AssertionError('Worker import must not start another resident')
    monkeypatch.setattr(jarvis.__main__,'main',forbidden)
    launcher=Path(__file__).resolve().parents[1]/'scripts'/'run_resident.pyw'
    runpy.run_path(str(launcher),run_name='__mp_main__')
