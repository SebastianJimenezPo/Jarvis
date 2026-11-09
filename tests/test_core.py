import json
from dataclasses import replace
import pytest
from jarvis.core.config import Config, load, save
from jarvis.core.events import EventBus
from jarvis.core.state_machine import StateMachine, State, ALLOWED
from jarvis.core.single_instance import SingleInstance


def machine():
    now = [100.0]
    bus = EventBus()
    events = []
    bus.subscribe(events.append)
    return StateMachine(bus, clock=lambda: now[0]), now, events


def test_session_timeout_cooldown_and_stale_events():
    m, now, events = machine()
    m.transition(State.DORMANT, "ready")
    assert not m.wake(99)
    assert m.wake(0)
    assert not m.wake(0)
    now[0] += 11
    m.tick(session=99)
    assert m.state == State.AWAKE
    m.tick(session=1)
    assert m.state == State.DORMANT
    assert not m.wake(0)
    now[0] += 4
    assert m.wake(0)
    m.transition(State.PAUSED, "pause")
    m.invalidate()
    now[0] += 100
    m.tick()
    assert m.state == State.PAUSED and m.deadline is None
    m.transition(State.DORMANT, "resume")
    assert not m.wake(0)
    assert m.wake(1)


@pytest.mark.parametrize("source", list(State))
@pytest.mark.parametrize("target", list(State))
def test_all_transition_pairs(source, target):
    m, _, _ = machine()
    m.state = source
    if target == source or target in ALLOWED[source]:
        m.transition(target, "test")
        assert m.state == target
    else:
        with pytest.raises(ValueError):
            m.transition(target, "test")


@pytest.mark.parametrize("field,value", [("active_seconds", 0), ("threshold", float("nan")),
    ("queue_blocks", True), ("version", 2), ("device", ""), ("log_level", "TRACE"),
    ("retry_max_seconds", 0.5), ("listening", "yes")])
def test_config_rejects_invalid(field, value):
    with pytest.raises(ValueError):
        replace(Config(), **{field: value}).validate()


def test_config_roundtrip_and_corruption_preserved(tmp_path):
    assert load(tmp_path) == Config()
    save(tmp_path, replace(Config(), device="Micrófono USB"))
    assert load(tmp_path).device == "Micrófono USB"
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load(tmp_path)
    assert path.read_text() == "{broken"


def test_windows_mutex():
    import uuid
    namespace = "JarvisTest-" + uuid.uuid4().hex
    with SingleInstance(namespace):
        with pytest.raises(RuntimeError, match="ya está"):
            with SingleInstance(namespace):
                pytest.fail("duplicate accepted")
    with SingleInstance(namespace):
        pass
