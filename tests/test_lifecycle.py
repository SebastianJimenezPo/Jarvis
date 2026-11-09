import time
from dataclasses import replace
import numpy as np
from jarvis.audio.buffers import AudioQueue
from jarvis.core.config import Config
from jarvis.core.lifecycle import LifecycleManager


class FakeCapture:
    live = 0
    fail = False
    def __init__(self, preference, capacity):
        self.device = {"name": "SIMULATED"}
        self.rate = 16000
        self.blocks = AudioQueue(capacity)
        self.overflows = 0
        self.last_audio = time.monotonic()
        self.opened = False
    def start(self):
        if self.fail:
            raise RuntimeError("simulated disconnect")
        self.opened = True
        type(self).live += 1
        self.blocks.put((time.monotonic(), np.zeros(320, dtype=np.float32)))
    def close(self):
        if self.opened:
            type(self).live -= 1
            self.opened = False


class FakeDetector:
    live = 0
    frame_bytes = 320
    def __init__(self, *args):
        self.opened = False
    def start(self):
        self.opened = True
        type(self).live += 1
    def process(self, pcm):
        return {"detected": False}
    def close(self):
        if self.opened:
            type(self).live -= 1
            self.opened = False


def wait_state(manager, state):
    end = time.monotonic() + 3
    while time.monotonic() < end:
        if manager.snapshot()["state"] == state:
            return
        time.sleep(0.02)
    raise AssertionError(manager.snapshot())


def test_pause_resume_suspend_and_exit(tmp_path):
    m = LifecycleManager(replace(Config(), confirmation=False), tmp_path, FakeCapture, FakeDetector)
    m.start()
    try:
        wait_state(m, "DORMANT")
        m.command("wake")
        wait_state(m, "AWAKE")
        m.command("pause")
        wait_state(m, "PAUSED")
        assert FakeCapture.live == FakeDetector.live == 0
        m.command("power_resume")
        time.sleep(0.15)
        assert m.snapshot()["state"] == "PAUSED"
        m.command("resume")
        wait_state(m, "DORMANT")
        m.command("suspend")
        wait_state(m, "PAUSED")
        m.command("power_resume")
        wait_state(m, "DORMANT")
    finally:
        m.stop()
    assert FakeCapture.live == FakeDetector.live == 0
    assert m.snapshot()["state"] == "STOPPING"


def test_failed_capture_manual_recovery_and_pause_cancels_retry(tmp_path):
    FakeCapture.fail = True
    m = LifecycleManager(replace(Config(), confirmation=False), tmp_path, FakeCapture, FakeDetector)
    m.start()
    try:
        wait_state(m, "DEGRADED")
        assert FakeDetector.live == 0
        m.command("pause")
        wait_state(m, "PAUSED")
        time.sleep(1.2)
        assert m.snapshot()["state"] == "PAUSED"
        FakeCapture.fail = False
        m.command("resume")
        wait_state(m, "DORMANT")
    finally:
        FakeCapture.fail = False
        m.stop()
    assert FakeCapture.live == FakeDetector.live == 0
