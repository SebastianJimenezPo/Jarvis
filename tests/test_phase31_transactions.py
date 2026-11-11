import threading
from dataclasses import replace
import pytest
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.ollama_client import RequestCancelled
from jarvis.intelligence.contracts import Kind


@pytest.mark.parametrize('new_session',[False,True])
def test_late_response_never_changes_newer_turn_or_session(tmp_path,new_session):
    entered=threading.Event();release=threading.Event();errors=[]
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):
            entered.set();assert release.wait(5)
            return 'Old response that must not reach Piper.'
        def unload(self):pass
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),semantic_enabled=False),client=Client())
    m.begin_session('old')
    def run():
        try:m.interpret('¿Qué es la RAM?','old','1')
        except RequestCancelled as exc:errors.append(type(exc))
    thread=threading.Thread(target=run);thread.start()
    try:
        assert entered.wait(3)
        session='new' if new_session else 'old'
        if new_session:m.begin_session(session)
        m.interpret('Abre Steam',session,'2');before=m.context.snapshot()
        release.set();thread.join(3)
        assert errors==[RequestCancelled]
        assert m.context.snapshot()==before
        assert m.last_decision.turn_id=='2' and len(m.executor.records)==1
    finally:release.set();thread.join(3)


def test_cancel_during_validation_rolls_back_pending_and_history(tmp_path):
    cancel=threading.Event()
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False),cancel=cancel)
    m.begin_session('s');before=m.context.snapshot()
    validate=m.validator.validate
    def stop(*args,**kwargs):
        result=validate(*args,**kwargs);cancel.set();return result
    m.validator.validate=stop
    with pytest.raises(RequestCancelled):m.interpret('Abre una aplicación','s')
    assert m.context.snapshot()==before


def test_context_expiring_during_model_call_cannot_commit(tmp_path):
    now=[100.0]
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):now[0]+=121;return 'Late'
        def unload(self):pass
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),semantic_enabled=False),client=Client(),clock=lambda:now[0])
    with pytest.raises(RequestCancelled):m.interpret('¿Qué es la RAM?')
    assert not m.context.history and not m.executor.records


def manager(root,cancel=None):
    return DialogueManager(root,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False),cancel=cancel)

def test_cancelled_interpretation_does_not_create_pending(tmp_path):
    cancel=threading.Event();m=manager(tmp_path,cancel);m.begin_session('s');before=m.context.snapshot()
    cancel.set()
    with pytest.raises(RequestCancelled):m.interpret('Abre una aplicación','s')
    assert m.context.snapshot()==before

def test_rejected_clarification_resolution_does_not_lose_pending(tmp_path):
    m=manager(tmp_path);m.interpret('Abre una aplicación');before=m.context.snapshot()
    def reject(*args,**kwargs):raise ValueError('controlled independent rejection')
    m.validator.validate=reject
    d,_=m.interpret('Steam')
    assert d.interpretation.kind==Kind.CLARIFICATION
    assert m.context.pending is not None
    assert m.context.pending.intent==before['pending']['intent']
    assert not m.executor.records

@pytest.mark.parametrize('text',['No canceles','No quiero cancelar','Espera','Todavía no','No, esa no','No era Chrome'])
def test_negation_during_pending_is_not_automatic_cancellation(tmp_path,text):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret(text)
    assert not d.interpretation.actions and m.context.pending is not None

def test_no_cancel_but_open_candidate(tmp_path):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret('No quiero cancelar, abre Spotify')
    assert [a.target for a in d.interpretation.actions]==['spotify']
