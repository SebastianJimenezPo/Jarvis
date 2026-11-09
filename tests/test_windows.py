import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from jarvis.core.config import Config, save


def test_pythonw_launcher_in_path_with_spaces(tmp_path):
    root = tmp_path / "perfil con espacios y acentos á"
    save(root, replace(Config(), listening=False))
    launcher = Path(__file__).resolve().parents[1] / "scripts" / "run_resident.pyw"
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    result = subprocess.run([str(pythonw), str(launcher), "--data-dir", str(root), "--exit-after", "1"],
                            cwd=tmp_path, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0
    report = json.loads((root / "diagnostics" / "latest.json").read_text(encoding="utf-8"))
    assert report["state"] == "STOPPING"
    assert report["state_seconds"]["PAUSED"] > 0.5
    assert report["activations"] == 0


def test_tray_menu_actions_dispatch_and_close(tmp_path):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMenu
    from jarvis.interface.tray import run
    from jarvis.core.lifecycle import LifecycleManager
    from test_lifecycle import FakeCapture, FakeDetector
    app = QApplication.instance() or QApplication([])
    config = replace(Config(), confirmation=False)
    manager = LifecycleManager(config, tmp_path, FakeCapture, FakeDetector)
    (tmp_path / "logs").mkdir()
    recorded = []
    def trigger(label):
        menus = [w for w in QApplication.topLevelWidgets() if isinstance(w, QMenu)]
        action = next(a for menu in menus for a in menu.actions() if a.text() == label)
        action.trigger()
    def record():
        recorded.append(manager.snapshot()["state"])
    QTimer.singleShot(200, lambda: trigger("Pausar escucha"))
    QTimer.singleShot(450, record)
    QTimer.singleShot(500, lambda: trigger("Reanudar / reintentar"))
    QTimer.singleShot(800, record)
    QTimer.singleShot(850, lambda: trigger("Probar activación manual"))
    QTimer.singleShot(1100, record)
    QTimer.singleShot(1200, lambda: trigger("Salir completamente"))
    run(manager, tmp_path, exit_after=3)
    assert recorded == ["PAUSED", "DORMANT", "AWAKE"]
    assert manager.snapshot()["state"] == "STOPPING"
    assert FakeCapture.live == FakeDetector.live == 0
