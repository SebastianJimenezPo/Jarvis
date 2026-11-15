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
