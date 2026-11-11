from dataclasses import replace
from jarvis.intelligence.settings import IntelligenceConfig
from jarvis.intelligence.dialogue_manager import DialogueManager
from jarvis.intelligence.contracts import Kind


def manager(root):return DialogueManager(root,replace(IntelligenceConfig(),llm_enabled=False,semantic_enabled=False))


def test_revision_ids_and_selective_modification(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y pon las luces rojas')
    plan_id=m.context.plan.plan_id
    steam=next(item.action_id for item in m.context.plan.active() if item.target=='steam')
    red=next(item.action_id for item in m.context.plan.active() if item.parameters.get('color')=='red')
    m.interpret('Mejor azules')
    assert m.context.plan.plan_id==plan_id and m.context.plan.revision==2
    assert next(item.action_id for item in m.context.plan.active() if item.target=='steam')==steam
    assert next(item.status for item in m.context.plan.items if item.action_id==red)=='replaced'
    assert len(m.context.plan.active())==2


def test_replace_is_distinct_from_append(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam')
    d,_=m.interpret('Y baja el volumen')
    assert d.plan_operation=='append' and len(m.context.plan.active())==2
    d,_=m.interpret('Olvida eso. Mejor abre Chrome')
    assert d.plan_operation=='replace'
    assert [item.target for item in m.context.plan.active()]==['chrome']


def test_cancelled_plan_items_have_no_physical_state(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y pon las luces rojas')
    d,_=m.interpret('Bueno, olvida lo de las luces')
    assert d.plan_operation=='cancel' and not d.end_session
    assert any(item.target=='main_light' and item.status=='cancelled' for item in m.context.plan.items)
    assert [item.target for item in m.context.plan.active()]==['steam']
    assert not d.executed


def test_plan_history_is_bounded_and_snapshot_keeps_ids(tmp_path):
    m=manager(tmp_path)
    for _ in range(40):m.interpret('Pon las luces rojas')
    assert len(m.context.plan.items)<=32
    snapshot=m.context.snapshot();other=manager(tmp_path);other.begin_session('next',snapshot)
    assert other.context.plan.snapshot()==m.context.plan.snapshot()


def test_exceeding_active_plan_limit_rolls_back(tmp_path):
    m=manager(tmp_path);m.interpret('Baja el volumen')
    for _ in range(7):m.interpret('Y baja el volumen')
    before=m.context.snapshot();count=len(m.executor.records)
    d,_=m.interpret('Y baja el volumen')
    assert d.interpretation.kind==Kind.CLARIFICATION and d.validation=='rejected'
    assert m.context.snapshot()==before and len(m.executor.records)==count


def test_held_partial_plan_depends_on_clarification(tmp_path):
    m=manager(tmp_path);m.interpret('Abre Steam y abre una aplicación')
    pending=next(item for item in m.context.plan.items if item.status=='pending_clarification')
    assert next(item for item in m.context.plan.items if item.status=='proposed').depends_on==[pending.action_id]
    assert not m.executor.records
    m.interpret('Chrome')
    assert {item.target for item in m.context.plan.active()}=={'chrome','steam'}
    assert not any(item.status=='pending_clarification' for item in m.context.plan.items)
