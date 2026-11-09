import json
import subprocess
import sys
import time
from dataclasses import replace
import pytest
from jarvis.core.config import Config
from jarvis.core.lifecycle import LifecycleManager
from jarvis.wakeword.rustpotter_adapter import RustpotterDetector
from test_lifecycle import FakeCapture, FakeDetector, wait_state


def test_stalled_detector_watchdog_and_cleanup(tmp_path):
    script = tmp_path / "stall.py"
    script.write_text('import json,time\nprint(json.dumps({"type":"ready","protocol":1,"sample_rate":16000,"encoding":"s16le","frame_bytes":320}),flush=True)\ntime.sleep(60)\n')
    detector = RustpotterDetector(tmp_path / "unused", 0.5, 0.2)
    detector.command = [sys.executable, str(script)]
    try:
        detector.start()
        process = detector.process_handle
        with pytest.raises(TimeoutError):
            detector.process(bytes(320))
    finally:
        detector.close()
    assert process.poll() is not None
    assert not detector.reader.is_alive()


def test_retry_budget_is_bounded(tmp_path):
    class BrokenDetector(FakeDetector):
        def start(self):
            raise RuntimeError("broken detector")
    m = LifecycleManager(replace(Config(), retry_limit=2, retry_initial_seconds=0.5),
                         tmp_path, FakeCapture, BrokenDetector)
    m.start()
    try:
        wait_state(m, "DEGRADED")
        time.sleep(1.2)
        state = m.snapshot()
        assert state["consecutive_failures"] == 2 and state["retry_at_monotonic"] is None
        time.sleep(0.5)
        assert m.snapshot()["consecutive_failures"] == 2
    finally:
        m.stop()


def test_disabled_start_never_opens_audio(tmp_path):
    m = LifecycleManager(replace(Config(), listening=False), tmp_path, FakeCapture, FakeDetector)
    m.start()
    try:
        wait_state(m, "PAUSED")
        assert FakeCapture.live == FakeDetector.live == 0
    finally:
        m.stop()


def test_job_kills_child_on_parent_crash(tmp_path):
    import psutil
    script = tmp_path / "parent.py"
    script.write_text('import subprocess,sys,time\nfrom jarvis.system.process_job import ProcessJob\np=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"],creationflags=subprocess.CREATE_NO_WINDOW)\njob=ProcessJob(p)\nprint(p.pid,flush=True)\ntime.sleep(60)\n')
    parent = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    child_pid = None
    try:
        child_pid = int(parent.stdout.readline())
        assert psutil.pid_exists(child_pid)
        parent.kill()
        parent.wait(timeout=3)
        deadline = time.monotonic() + 3
        while psutil.pid_exists(child_pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not psutil.pid_exists(child_pid)
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()
        parent.stdout.close()
        if child_pid and psutil.pid_exists(child_pid):
            psutil.Process(child_pid).kill()
