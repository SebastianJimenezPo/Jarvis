from dataclasses import replace
import json
import pytest
from jarvis.dialogue.bridge import UserUtterance
from jarvis.intelligence.provider import IntelligenceResponseProvider
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.contracts import Kind


def provider(root,log=False):
    return IntelligenceResponseProvider(root,config=replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False,log_text=log))


def turn(text,index='2'):return UserUtterance('s',index,text,'es',0)


def test_doubtful_short_transcript_uses_one_alternative_then_validates(tmp_path):
    p=provider(tmp_path);p.begin_session('s');p.respond(turn('Pon las luces rojas','1'))
    calls=[]
    p.respond_audio(turn('Fora Sodes'),lambda:(calls.append(True) or 'Mejor azules'))
    assert calls==[True] and p.manager.context.proposals[0].parameters=={'color':'blue'}


def test_clear_command_does_not_run_second_stt(tmp_path):
    p=provider(tmp_path);p.begin_session('s')
    def forbidden():raise AssertionError('must not load alternative')
    p.respond_audio(turn('Abre Steam'),forbidden)
    assert p.manager.last_decision.interpretation.kind==Kind.ACTION_PROPOSAL


def test_unknown_device_is_clarified_not_invented(tmp_path):
    p=provider(tmp_path);p.begin_session('s')
    p.respond_audio(turn('Por favor, ponla en lo principal de color rojo'),lambda:'Un texto también incoherente')
    assert not p.manager.executor.records
    assert p.manager.context.pending is not None
    p.respond(turn('La luz principal','3'))
    assert p.manager.context.proposals[0].target=='main_light'


def test_alternative_cannot_discard_known_color_from_primary(tmp_path):
    p=provider(tmp_path);p.begin_session('s')
    p.respond_audio(turn('Ponla en lo principal de color rojo'),lambda:'Pon las luces azules')
    assert not p.manager.executor.records
    assert p.manager.last_decision.interpretation.kind==Kind.CLARIFICATION


def test_missing_alternative_degrades_and_preserves_existing_plan(tmp_path):
    p=provider(tmp_path);p.begin_session('s');p.respond(turn('Pon las luces rojas','1'))
    def missing():raise FileNotFoundError('not installed')
    p.respond_audio(turn('Fora Sodes'),missing)
    assert p.manager.context.proposals[0].parameters=={'color':'red'}
    assert p.manager.last_decision.interpretation.kind==Kind.CLARIFICATION


@pytest.mark.parametrize('log',[False,True])
def test_turn_trace_requires_explicit_text_logging(tmp_path,log):
    p=provider(tmp_path,log);p.begin_session('s');p.respond(turn('Abre Steam'))
    data=p.diagnostic()
    assert ('turn_trace' in data)==log
    if log:
        assert data['turn_trace']['original_transcript']=='Abre Steam'
        assert data['turn_trace']['normalized_text']=='abre steam'
        assert data['turn_trace']['response']
    else:assert 'Abre Steam' not in json.dumps(data,ensure_ascii=False)


def test_conversation_followup_is_not_treated_as_stt_garbage(tmp_path):
    p=provider(tmp_path);p.manager.config=replace(p.manager.config,llm_enabled=True)
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):return 'La RAM es memoria temporal.'
    p.manager.client=Client();p.begin_session('s')
    p.respond(turn('Abre Steam','1'));p.respond(turn('¿Qué es la RAM?','2'))
    def forbidden():raise AssertionError('conversation must not run second STT')
    p.respond_audio(turn('Explícamelo más sencillo','3'),forbidden)
    assert p.manager.last_decision.route=='llm' and p.recovery_status=='not_needed'


@pytest.mark.parametrize('mode',['cancel','timeout'])
def test_alternative_process_is_terminated_on_cancel_or_timeout(monkeypatch,tmp_path,mode):
    import threading
    import numpy as np
    from jarvis.speech import recovery
    from jarvis.speech.settings import VoiceConfig
    from jarvis.intelligence.ollama_client import RequestCancelled
    calls=[]
    class Pipe:
        def close(self):pass
        def poll(self,*args):return False
    class Process:
        def start(self):pass
        def is_alive(self):return True
        def join(self,**kwargs):pass
        def terminate(self):calls.append('terminated')
        def close(self):calls.append('closed')
    class Context:
        def Pipe(self,**kwargs):return Pipe(),Pipe()
        def Process(self,**kwargs):return Process()
    monkeypatch.setattr(recovery.mp,'get_context',lambda *args:Context())
    monkeypatch.setattr(recovery,'resolve',lambda *args:None)
    ticks=iter([0,20]);monkeypatch.setattr(recovery.time,'monotonic',lambda:next(ticks))
    cancel=threading.Event()
    if mode=='cancel':cancel.set()
    with pytest.raises(RequestCancelled if mode=='cancel' else TimeoutError):
        recovery.transcribe_alternative(tmp_path,np.zeros(16000,dtype=np.float32),VoiceConfig(),cancel)
    assert calls==['terminated','closed']


def test_late_recovery_cannot_overwrite_a_newer_turn(tmp_path):
    from jarvis.intelligence.ollama_client import RequestCancelled
    p=provider(tmp_path);p.begin_session('s');p.respond(turn('Pon las luces rojas','1'))
    def late():
        p.respond(turn('Abre Chrome','3'))
        return 'Mejor azules'
    with pytest.raises(RequestCancelled):p.respond_audio(turn('Fora Sodes','2'),late)
    assert [a.target for a in p.manager.context.proposals]==['chrome']


def test_cancelled_provider_result_never_reaches_piper(monkeypatch,tmp_path):
    import queue
    import threading
    import numpy as np
    from jarvis.speech.worker import voice_worker
    from jarvis.speech import recognition,piper_adapter
    from jarvis.speech.settings import VoiceConfig
    from jarvis.audio import vad
    from jarvis.intelligence import provider as factory
    from jarvis.intelligence.ollama_client import RequestCancelled
    class Engine:
        def load(self):pass
        def start_turn(self,*args):pass
        def feed_audio(self,*args):pass
        def finish_turn(self):return 'Abre Steam'
        def cancel_turn(self):pass
        def unload(self):pass
    class VAD:
        def __init__(self,*args):pass
        def reset(self):pass
        def probability(self,samples):return float(np.mean(abs(samples))>.1)
    class Provider:
        def respond_audio(self,*args):raise RequestCancelled('old session')
    monkeypatch.setattr(recognition,'make_engine',lambda *args:Engine())
    monkeypatch.setattr(vad,'SpeechActivityDetector',VAD)
    monkeypatch.setattr(factory,'make_provider',lambda *args:Provider())
    def forbidden(*args):raise AssertionError('Piper must not start')
    monkeypatch.setattr(piper_adapter,'PiperAdapter',forbidden)
    inbox=queue.Queue();outbox=queue.Queue();cancel=threading.Event()
    speech=(np.ones(512*12)*10000).astype('<i2').tobytes()+bytes(512*42*2)
    thread=threading.Thread(target=voice_worker,args=(inbox,outbox,cancel,str(tmp_path),VoiceConfig()));thread.start()
    inbox.put(('session','s',speech,False));events=[]
    try:
        while True:
            event=outbox.get(timeout=3);events.append(event)
            if event['kind']=='session_end':break
        assert events[-1]['reason']=='cancelled_or_stale'
        assert not any(event['kind'] in ('voice_error','synthesis_started') for event in events)
    finally:inbox.put(('stop',));thread.join(3)
    assert not thread.is_alive()
