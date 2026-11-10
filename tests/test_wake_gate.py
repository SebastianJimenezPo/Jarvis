from dataclasses import replace
import pytest
from jarvis.core.config import Config
from jarvis.core.lifecycle import LifecycleManager
from jarvis.core.state_machine import State


@pytest.mark.parametrize('score',[0.506,0.5209,0.543,0.549999,None,float('nan'),float('inf'),-1,2,True])
def test_low_or_invalid_scores_never_activate(tmp_path,score):
    manager=LifecycleManager(replace(Config(),threshold=0.55,confirmation=False),tmp_path)
    manager.machine.transition(State.DORMANT,'ready')
    manager._wake(score)
    assert manager.machine.state==State.DORMANT
    assert manager.metrics['activations']==0


@pytest.mark.parametrize('score',[0.55,0.5855,0.6152])
def test_sufficient_scores_activate(tmp_path,score):
    manager=LifecycleManager(replace(Config(),threshold=0.55,confirmation=False),tmp_path)
    manager.machine.transition(State.DORMANT,'ready')
    manager._wake(score)
    assert manager.machine.state==State.AWAKE
    assert manager.metrics['activations']==1


def test_manual_diagnostic_activation_bypasses_acoustic_score(tmp_path):
    manager=LifecycleManager(replace(Config(),threshold=0.55,confirmation=False),tmp_path)
    manager.machine.transition(State.DORMANT,'ready')
    manager._wake(manual=True)
    assert manager.machine.state==State.AWAKE
