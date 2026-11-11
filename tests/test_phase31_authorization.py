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


@pytest.mark.parametrize('text',[
 'Apaga las luces al acabar la partida','Una vez termine el juego, apaga las luces',
 'Al finalizar la canción, baja el volumen','En cuanto termine la película, apaga la iluminación',
 'Solo cuando te lo diga, abre Chrome','No hagas nada hasta que termine',
 'Abre Steam al salir de clase','Abre Chrome una vez haya guardado',
 'Apaga la luz luego de cenar','Baja el volumen en cuanto acabe',
 'Pon las luces azules, pero todavía no','Abre Steam siempre que termine la partida'])
def test_future_never_authorizes_immediate_proposals(tmp_path,text):
    m=manager(tmp_path);d,_=m.interpret(text)
    assert not d.interpretation.actions
    assert not m.executor.records

@pytest.mark.parametrize('text',[
 'No, mejor azules, pero no hagas nada','Mejor azul cuando termine',
 'Mejor azul, pero no ahora','No, mejor azul, aunque todavía no lo cambies',
 'Déjalo en rojo, no lo cambies','Si es posible después, mejor azul',
 'No era una orden, solo estaba preguntando'])
def test_correction_cannot_bypass_prohibition_or_future(tmp_path,text):
    m=manager(tmp_path);m.interpret('Pon las luces rojas')
    old=[a.model_dump() for a in m.context.proposals];count=len(m.executor.records)
    d,_=m.interpret(text)
    assert not d.interpretation.actions and len(m.executor.records)==count
    assert [a.model_dump() for a in m.context.proposals]==old

def test_past_relative_reference_is_not_a_past_comment(tmp_path):
    d,_=manager(tmp_path).interpret('Abre la aplicación que usé ayer')
    assert d.interpretation.kind==Kind.CLARIFICATION

def test_forged_fast_reason_does_not_authorize_ungrounded_target(tmp_path):
    m=manager(tmp_path);m.interpret('Pon las luces rojas')
    forged=Interpretation(kind=Kind.ACTION_PROPOSAL,immediate=True,reason_code='context_correction',actions=[
        ActionProposal(intent='open_application',target='discord',source_clause='mejor azul')])
    with pytest.raises(ValueError):m.validator.validate(forged,'Mejor azul',m.context,trusted_fast=True)


@pytest.mark.parametrize('trusted',[False,True])
@pytest.mark.parametrize('text,intent,target,parameters',[
 ('Abre Chrome','get_system_status','system',{}),
 ('Pon las luces al 50','set_volume','system_audio',{'value':50}),
 ('Baja el brillo de las luces','set_light_brightness','main_light',{'delta':10})])
def test_route_label_never_grants_wrong_action(tmp_path,trusted,text,intent,target,parameters):
    m=manager(tmp_path)
    forged=Interpretation(kind=Kind.ACTION_PROPOSAL,immediate=True,actions=[ActionProposal(
        intent=intent,target=target,parameters=parameters,source_clause=text)])
    with pytest.raises(ValueError):m.validator.validate(forged,text,m.context,trusted_fast=trusted)


@pytest.mark.parametrize('text',[
 'Apaga las luces antes de acostarme','Abre Steam a condición de que guarde el trabajo',
 'Abre Chrome tras finalizar la copia','Abre Steam apenas salga del trabajo',
 'Apaga las luces mientras esté fuera','Ni se te ocurra abrir Steam',
 'De ningún modo abras Chrome','Me gustaría abrir Steam algún día',
 'Estaría bien abrir Steam','Steam abierto'])
def test_non_imperative_or_subordinate_text_does_not_authorize_forged_action(tmp_path,text):
    m=manager(tmp_path)
    intent='turn_off_light' if 'luces' in text else 'open_application'
    target='main_light' if intent=='turn_off_light' else 'chrome' if 'Chrome' in text else 'steam'
    forged=Interpretation(kind=Kind.ACTION_PROPOSAL,immediate=True,actions=[ActionProposal(intent=intent,target=target,source_clause=text)])
    with pytest.raises(ValueError):m.validator.validate(forged,text,m.context,trusted_fast=True)
