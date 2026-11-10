from dataclasses import replace
import pytest
from jarvis.intelligence.settings import IntelligenceConfig,save_intelligence
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.contracts import Kind


def test_phase3_provider_keeps_context_between_voice_turns(tmp_path):
    from jarvis.intelligence.provider import make_provider
    from jarvis.dialogue.bridge import DialogueBridge,UserUtterance
    save_intelligence(tmp_path,replace(IntelligenceConfig(),enabled=True,semantic_enabled=False,llm_enabled=False))
    provider=make_provider(tmp_path);provider.begin_session('s')
    bridge=DialogueBridge(provider)
    try:
        reply=bridge.respond(UserUtterance('s','1','Pon las luces rojas','es',0))
        assert 'simulación' in reply.text and not reply.end_session
        reply=bridge.respond(UserUtterance('s','2','No, mejor azules','es',1))
        assert 'azul' in reply.text
        assert provider.manager.context.proposals[0].parameters['color']=='blue'
        snapshot=provider.snapshot()
        provider.begin_session('new',snapshot)
        reply=bridge.respond(UserUtterance('new','1','Y baja el brillo','es',2))
        assert 'brillo' in reply.text
        assert all(r.status=='proposed_simulated' for r in provider.manager.context.referents)
    finally:provider.close()


def test_memory_is_volatile_and_stale_snapshots_expire(tmp_path):
    now=[100.0]
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False),clock=lambda:now[0])
    m.interpret('Abre Steam');snapshot=m.context.snapshot()
    now[0]+=121
    other=DialogueManager(tmp_path,m.config,clock=lambda:now[0]);other.begin_session('new',snapshot)
    assert not other.context.targets('application')


def test_light_correction_preserves_other_plan_items(tmp_path):
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False))
    m.interpret('Voy a jugar, quiero las luces rojas y Steam abierto')
    d,_=m.interpret('No, mejor azules')
    assert len(d.interpretation.actions)==1
    assert any(a.target=='steam' for a in m.context.proposals)
    assert any(a.parameters.get('color')=='blue' for a in m.context.proposals)
    m.interpret('Y que estén más suaves')
    assert any(a.intent=='set_light_brightness' for a in m.context.proposals)
    assert any(a.parameters.get('color')=='blue' for a in m.context.proposals)


def test_inference_json_is_not_action_authorization(tmp_path):
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):
            return '{"kind":"action_proposal","actions":[{"intent":"open_application","target":"chrome","source_clause":"quiero un cafe"}]}'
        def unload(self):pass
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),semantic_enabled=False),client=Client())
    d,_=m.interpret('Quiero un café')
    assert d.interpretation.kind==Kind.CLARIFICATION
    assert not m.executor.records


def test_invalid_intelligence_config_falls_back_to_phase2(tmp_path):
    from jarvis.intelligence.provider import make_provider
    from jarvis.dialogue.bridge import Phase2ResponseProvider
    (tmp_path/'intelligence.json').write_text('{broken',encoding='utf-8')
    assert isinstance(make_provider(tmp_path),Phase2ResponseProvider)


def test_real_semantic_path_when_models_explicitly_installed():
    from jarvis.core.config import data_dir
    root=data_dir()
    if not (root/'intelligence_models'/'calibration-e5-small.json').exists():pytest.skip('Semantic assets not installed')
    m=DialogueManager(root,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=True))
    try:
        d,_=m.interpret('La música está demasiado fuerte')
        assert d.route=='semantic' and d.interpretation.actions[0].intent=='decrease_volume'
        d,_=m.interpret('No bajes el volumen')
        assert d.route=='fast' and not d.interpretation.actions
    finally:m.close()


def test_compact_context_obeys_budget(tmp_path):
    m=DialogueManager(tmp_path,replace(IntelligenceConfig(),context_tokens=512))
    for _ in range(20):m.context.exchange('x'*800,'y'*1000)
    import json
    assert len(json.dumps(m.compact_context()))<=700


def test_diagnostics_do_not_leak_transcript_in_validation_errors(tmp_path):
    from jarvis.intelligence.provider import IntelligenceResponseProvider
    provider=IntelligenceResponseProvider(tmp_path,config=replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False))
    provider.manager.interpret('Hola')
    provider.manager.last_error='ValidationError: private words from an invalid model response'
    assert 'private words' not in provider.diagnostic()['last_error']
