from dataclasses import replace
import json
import subprocess
import sys
import threading
import time
from jarvis.speech.settings import VoiceConfig
from jarvis.dialogue.bridge import UserUtterance


def utterance(text,turn='1',session='s'):
    return UserUtterance(session,turn,text,'es',time.monotonic())


def test_next_profile_factory_never_imports_legacy_or_local_intelligence_models():
    code = '''
import sys, threading
from dataclasses import replace
from jarvis.speech.settings import VoiceConfig
from jarvis.dialogue.factory import make_provider
p=make_provider(None,replace(VoiceConfig(),dialogue_profile='next'),threading.Event())
assert not any(n.startswith('jarvis.intelligence') for n in sys.modules)
assert not any(n in sys.modules for n in ('onnxruntime','tokenizers','torch','moonshine_voice'))
p.close()
'''
    r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=10)
    assert r.returncode==0,r.stderr


def test_voice_bridge_uses_pending_context_and_drops_superseded_reply():
    from jarvis.dialogue.next_bridge import NextVoiceBridge
    p=NextVoiceBridge(replace(VoiceConfig(),dialogue_profile='next'),threading.Event())
    p.begin_session('s')
    try:
        first=p.respond(utterance('Abre una aplicación'))
        assert 'cuál' in first.text.lower() and p.can_publish(first)
        second=p.respond(utterance('Spotify','2'))
        assert 'simul' in second.text.lower() and 'Spotify' in second.text
        assert not p.can_publish(first) and p.can_publish(second)
        assert 'Spotify' not in json.dumps(p.diagnostic())
        p.end_session()
        assert not p.can_publish(second)
    finally:p.close()


def test_cancelled_provider_work_does_not_reach_synthesis():
    from jarvis.next.engine import NextEngine
    from jarvis.next.conversation import NextConversation
    from jarvis.next.providers import FakeProvider,ProviderError
    from jarvis.dialogue.next_bridge import NextVoiceBridge
    cancel=threading.Event();entered=threading.Event();release=threading.Event()
    def blocked(req,control):
        entered.set();release.wait(2);control.checkpoint();raise ProviderError('unavailable')
    engine=NextEngine(FakeProvider(blocked),review_enabled=True,cancelled=cancel.is_set)
    p=NextVoiceBridge(replace(VoiceConfig(),dialogue_profile='next'),cancel,conversation=NextConversation(engine))
    p.begin_session('s');result=[]
    worker=threading.Thread(target=lambda:result.append(p.respond(utterance('Una orden compleja'))))
    try:
        worker.start();assert entered.wait(1)
        cancel.set();worker.join(1)
        assert not worker.is_alive() and not p.can_publish(result[0])
        assert not result[0].text
    finally:release.set();worker.join(3);p.close()


def test_next_profile_does_not_replace_personal_voice_configuration(tmp_path):
    from jarvis.speech.settings import save_voice,load_voice
    original=replace(VoiceConfig(),engine='moonshine-small',end_silence_ms=1200,output_device='personal output')
    save_voice(tmp_path,original);raw=(tmp_path/'voice.json').read_bytes()
    selected=replace(load_voice(tmp_path),dialogue_profile='next',next_remote=False)
    assert selected.end_silence_ms==1200 and selected.output_device=='personal output'
    assert (tmp_path/'voice.json').read_bytes()==raw


def test_expired_review_is_not_publishable_after_cold_tts_preparation():
    from jarvis.next.engine import NextEngine
    from jarvis.next.conversation import NextConversation
    from jarvis.next.contracts import Decision,ProviderReply,ToolCall,Span
    from jarvis.next.providers import FakeProvider
    from jarvis.dialogue.next_bridge import NextVoiceBridge
    now=[100.0]
    def proposal(req,_):
        return ProviderReply(decision_json=Decision(operation='create_plan',temporal='now',
            actions=(ToolCall(tool='applications.open',target='steam',evidence=Span(start=0,end=len(req.text))),)).model_dump_json())
    c=NextConversation(NextEngine(FakeProvider(proposal),clock=lambda:now[0],review_enabled=True))
    p=NextVoiceBridge(VoiceConfig(),threading.Event(),conversation=c);p.begin_session('s')
    try:
        reply=p.respond(utterance('Por favor inicia Steam'))
        assert p.can_publish(reply)
        now[0]+=31
        assert not p.can_publish(reply)
    finally:p.close()


import pytest
@pytest.mark.parametrize('presented',[False,True])
def test_voice_yes_requires_a_proposal_that_was_presented_locally(presented):
    from jarvis.next.engine import NextEngine
    from jarvis.next.conversation import NextConversation
    from jarvis.next.providers import FakeProvider
    from jarvis.next.contracts import Decision,ProviderReply,ToolCall,Span
    from jarvis.dialogue.next_bridge import NextVoiceBridge
    def proposal(req,_):
        return ProviderReply(decision_json=Decision(operation='create_plan',temporal='now',
            actions=(ToolCall(tool='applications.open',target='steam',evidence=Span(start=0,end=len(req.text))),)).model_dump_json())
    c=NextConversation(NextEngine(FakeProvider(proposal),review_enabled=True))
    p=NextVoiceBridge(VoiceConfig(),threading.Event(),conversation=c);p.begin_session('s')
    try:
        reply=p.respond(utterance('Inicia Steam, por favor'))
        if presented:p.mark_presented(reply)
        p.respond(utterance('sí','2'))
        assert bool(c.engine.manager.snapshot().items)==presented
        assert not p.diagnostic()['executed']
    finally:p.close()


def test_worker_presents_a_review_then_accepts_one_spoken_confirmation(monkeypatch,tmp_path):
    import queue
    import numpy as np
    from jarvis.speech.worker import voice_worker
    from jarvis.speech import recognition,piper_adapter
    from jarvis.audio import vad,playback
    from jarvis.dialogue import factory
    from jarvis.dialogue.next_bridge import NextVoiceBridge
    from jarvis.next.engine import NextEngine
    from jarvis.next.conversation import NextConversation
    from jarvis.next.providers import FakeProvider
    from jarvis.next.contracts import Decision,ProviderReply,ToolCall,Span
    inbox=queue.Queue();outbox=queue.Queue();cancel=threading.Event()
    def proposal(req,_):
        return ProviderReply(decision_json=Decision(operation='create_plan',temporal='now',
            actions=(ToolCall(tool='applications.open',target='steam',evidence=Span(start=0,end=len(req.text))),)).model_dump_json())
    c=NextConversation(NextEngine(FakeProvider(proposal),review_enabled=True))
    provider=NextVoiceBridge(VoiceConfig(),cancel,conversation=c)
    class STT:
        count=0
        def load(self):pass
        def start_turn(self,*_):pass
        def feed_audio(self,*_):pass
        def finish_turn(self):
            self.count+=1
            return 'Por favor inicia Steam' if self.count==1 else 'sí'
        def cancel_turn(self):pass
        def unload(self):pass
    class VAD:
        def __init__(self,*_):pass
        def reset(self):pass
        def probability(self,frame):return float(np.mean(abs(frame))>.1)
    class TTS:
        def __init__(self,*_):pass
        def load(self):pass
        def synthesize(self,text):return [text]
        def unload(self):pass
    class Playback:
        def __init__(self,*_):pass
        def play(self,chunks,cancel,emit):
            for _ in chunks:emit('playback_started')
    monkeypatch.setattr(factory,'make_provider',lambda *_:provider)
    monkeypatch.setattr(recognition,'make_engine',lambda *_:STT())
    monkeypatch.setattr(vad,'SpeechActivityDetector',VAD)
    monkeypatch.setattr(piper_adapter,'PiperAdapter',TTS)
    monkeypatch.setattr(playback,'SpeechPlaybackManager',Playback)
    pcm=(np.ones(512*12)*10000).astype('<i2').tobytes()+bytes(512*25*2)
    config=replace(VoiceConfig(),dialogue_profile='next',end_silence_ms=650,echo_guard_seconds=.1,followup_seconds=2)
    worker=threading.Thread(target=voice_worker,args=(inbox,outbox,cancel,str(tmp_path),config));worker.start()
    inbox.put(('session','s',pcm,False))
    try:
        completed=0;deadline=time.monotonic()+5
        while completed<2 and time.monotonic()<deadline:
            event=outbox.get(timeout=2)
            assert event['kind']!='voice_error',event
            if event['kind']=='turn_completed':
                completed+=1
                if completed==1:
                    assert not c.engine.manager.snapshot().items
                    time.sleep(.2);inbox.put(('audio','s',time.monotonic(),pcm))
        assert completed==2 and c.engine.manager.snapshot().items[0].call.target=='steam'
    finally:
        inbox.put(('stop',));worker.join(3)
    assert not worker.is_alive()
