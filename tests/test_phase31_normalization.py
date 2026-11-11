from dataclasses import replace
import pytest
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.contracts import Kind


def manager(root):return DialogueManager(root,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False))


@pytest.mark.parametrize('text,intent,parameters',[
 ('Baja el volumen en diez','decrease_volume',{'amount':10}),
 ('Baja el volumen al diez','set_volume',{'value':10}),
 ('Baja el volumen diez puntos','decrease_volume',{'amount':10}),
 ('Sube cinco por ciento','increase_volume',{'amount':5}),
 ('Pon el volumen al treinta y cinco','set_volume',{'value':35}),
 ('Volumen al noventa y nueve','set_volume',{'value':99})])
def test_numerical_constructions_keep_meaning(tmp_path,text,intent,parameters):
    d,_=manager(tmp_path).interpret(text)
    assert [(a.intent,a.parameters) for a in d.interpretation.actions]==[(intent,parameters)]


def test_percent_suffix_is_not_a_hundred_prefix(tmp_path):
    d,_=manager(tmp_path).interpret('Pon el volumen al veinte por ciento')
    assert d.interpretation.actions[0].parameters=={'value':20}


@pytest.mark.parametrize('text',['Pon el volumen al 50.5','Pon el volumen al 20,5','Pon el volumen al 1/2','Pon el volumen al menos diez'])
def test_unsupported_or_ambiguous_number_is_not_truncated(tmp_path,text):
    m=manager(tmp_path);d,_=m.interpret(text)
    assert d.interpretation.kind==Kind.CLARIFICATION and not m.executor.records


@pytest.mark.parametrize('text',['Y que no alumbren tanto','Pon las luces menos fuertes','Me está encandilando'])
def test_colloquial_light_request_uses_valid_context(tmp_path,text):
    m=manager(tmp_path);m.interpret('Pon las luces rojas')
    d,_=m.interpret(text)
    assert [(a.intent,a.parameters) for a in d.interpretation.actions]==[('set_light_brightness',{'delta':-10})]


def test_no_cannot_accept_single_pending_candidate(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Chrome');m.fast.clarify('close_application',{},'application',['chrome'])
    d,_=m.interpret('No')
    assert not d.interpretation.actions and m.context.pending is not None


def test_short_color_after_clarification_can_be_corrected(tmp_path):
    m=manager(tmp_path);m.interpret('Pon las luces de otro color');m.interpret('Azul')
    d,_=m.interpret('No, verde')
    assert d.interpretation.actions[0].parameters=={'color':'green'}
