from dataclasses import replace
import pytest
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.contracts import Kind


def manager(root):
    return DialogueManager(root,replace(IntelligenceConfig(),semantic_enabled=False,llm_enabled=False))


def test_color_clarification_after_application_request(tmp_path):
    m=manager(tmp_path)
    d,_=m.interpret('Abre una aplicación')
    assert d.interpretation.kind==Kind.CLARIFICATION
    d,_=m.interpret('Steam')
    assert d.interpretation.actions[0].target=='steam'
    d,response=m.interpret('Pon las luces de otro color')
    assert d.route=='fast' and 'color' in response
    d,_=m.interpret('Azul')
    assert d.interpretation.actions[0].parameters=={'color':'blue'}


def test_new_request_replaces_pending_question_without_opening_app(tmp_path):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret('Pon las luces de otro color')
    assert m.context.pending.intent=='set_light_color'
    d,_=m.interpret('Azul')
    assert [a.intent for a in d.interpretation.actions]==['set_light_color']
    assert len(m.executor.records)==1


def test_pending_question_cannot_consume_negated_application(tmp_path):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret('No abras Steam')
    assert d.interpretation.kind==Kind.NEGATED and not m.executor.records


def test_color_clarification_preserves_earlier_unemitted_action(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y pon las luces de otro color')
    assert not m.executor.records
    d,_=m.interpret('Azul')
    assert [a.intent for a in d.interpretation.actions]==['open_application','set_light_color']


@pytest.mark.parametrize('text',['Cancela','Cancélalo','Cancela eso','Por favor cancela','Jarvis cancela todo','Cancela la solicitud, por favor'])
def test_cancel_is_fast_clears_context_and_ends_session(tmp_path,text):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret(text)
    assert d.route=='fast' and d.interpretation.kind==Kind.CANCEL
    assert d.end_session and m.context.pending is None
    assert not m.executor.records


def test_out_of_range_spoken_number_is_not_twenty(tmp_path):
    m=manager(tmp_path)
    d,_=m.interpret('Pon el volumen al ciento veinte por ciento')
    assert d.interpretation.kind==Kind.CLARIFICATION
    assert not m.executor.records
    d,_=m.interpret('Cincuenta')
    assert d.interpretation.actions[0].parameters=={'value':50}


@pytest.mark.parametrize('value',['ciento uno','ciento 20','doscientos cincuenta','menos diez','mil'])
def test_spoken_out_of_range_values_are_not_truncated(tmp_path,value):
    m=manager(tmp_path)
    d,_=m.interpret('Pon el volumen al '+value+' por ciento')
    assert d.interpretation.kind==Kind.CLARIFICATION and not m.executor.records


@pytest.mark.parametrize('text',['Explícamelo más fácil','Dime la diferencia entre RAM y almacenamiento','Abre una aplicación desconocida','Cancela eso'])
def test_unrelated_turns_never_load_embeddings(tmp_path,text):
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):return 'La RAM conserva datos temporales.'
        def unload(self):pass
    m=DialogueManager(tmp_path,IntelligenceConfig(),client=Client())
    def forbidden(*args):raise AssertionError('unnecessary embedding load')
    m.semantic.load=forbidden
    m.interpret(text)
    assert m.semantic.provider is None
    assert not m.last_error


def test_supported_semantic_complaint_still_reaches_router(tmp_path):
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),llm_enabled=False))
    calls=[]
    m.semantic.candidate=lambda text:(calls.append(text) or (None,[]))
    m.interpret('La música está demasiado fuerte')
    assert calls==['La música está demasiado fuerte']


def test_voice_cpu_limit_respects_allowed_processors(monkeypatch):
    from jarvis.system import voice_resources
    calls=[]
    class Process:
        def cpu_affinity(self,cpus=None):
            if cpus is None:return [2,3,6,7]
            calls.append(cpus)
        def nice(self,value):calls.append(value)
    monkeypatch.setattr(voice_resources.psutil,'Process',Process)
    voice_resources.configure_voice_process(2)
    assert calls[0]==[2,3]


@pytest.mark.parametrize('text',['Cancela','Cancélalo','Cancelar'])
def test_cancel_is_not_suppressed_as_an_ambiguous_wake_word(text):
    from jarvis.dialogue.bridge import activation_only_candidate
    assert not activation_only_candidate(text,first_turn=True)


@pytest.mark.parametrize('text',['Por favor, pon la luz principal de color rojo.','Por favor, abre Steam.','Abre Steam, por favor.'])
def test_stt_polite_commas_do_not_send_direct_requests_to_llm(tmp_path,text):
    m=manager(tmp_path)
    d,_=m.interpret(text)
    assert d.route=='fast' and d.interpretation.kind==Kind.ACTION_PROPOSAL


def test_new_polite_request_replaces_pending_clarification(tmp_path):
    m=manager(tmp_path);m.interpret('Abre una aplicación')
    d,_=m.interpret('Por favor, pon las luces de otro color.')
    assert d.route=='fast' and m.context.pending.intent=='set_light_color'
