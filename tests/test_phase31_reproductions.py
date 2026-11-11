"""Development regressions authored before hardening; never a reserved holdout."""
import threading
from dataclasses import replace
import pytest
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.contracts import Kind,Interpretation,ActionProposal
from jarvis.intelligence.ollama_client import RequestCancelled


def manager(root,cancel=None):
    return DialogueManager(root,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False),cancel=cancel)


def test_append_preserves_prior_plan(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y pon las luces rojas')
    m.interpret('Y baja el volumen')
    assert {a.intent for a in m.context.proposals}=={'open_application','set_light_color','decrease_volume'}


def test_short_parameter_correction_keeps_color_and_application(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y pon las luces rojas')
    m.interpret('Mejor azules');m.interpret('Y el brillo al veinte');d,_=m.interpret('No, al treinta')
    assert d.interpretation.actions[0].parameters=={'value':30}
    assert any(a.target=='steam' for a in m.context.proposals)
    assert any(a.parameters.get('color')=='blue' for a in m.context.proposals)


def test_two_explicit_lights_are_not_reduced_to_desk(tmp_path):
    m=manager(tmp_path);d,_=m.interpret('Enciende la luz principal y la luz del escritorio')
    assert {a.target for a in d.interpretation.actions}=={'main_light','desk_light'}
    d,_=m.interpret('Apágala')
    assert d.interpretation.kind==Kind.CLARIFICATION


@pytest.mark.parametrize('text,value',[
 ('Volumen al veinte',20),('Volumen al veinticinco',25),('Volumen al treinta y cinco',35),('Volumen al cien',100)])
def test_short_absolute_values(tmp_path,text,value):
    d,_=manager(tmp_path).interpret(text)
    assert d.interpretation.actions[0].parameters=={'value':value}


def test_selective_cancellation_preserves_application(tmp_path):
    m=manager(tmp_path);m.interpret('Pon las luces rojas y abre Steam')
    d,_=m.interpret('Bueno, olvida lo de las luces')
    assert not d.interpretation.actions
    assert [a.target for a in m.context.proposals]==['steam']
