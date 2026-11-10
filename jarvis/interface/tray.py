import os
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from .diagnostics import ResourceSampler, write_report
from jarvis.system.windows_events import WindowsEvents
from jarvis.core.events import Kind


class StateBridge(QObject):
    changed = Signal(str)
    voice_changed = Signal(str)


def run(manager, root, exit_after=None):
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        raise RuntimeError("No está disponible la bandeja de Windows")
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setBrush(QColor("#28b8cf"))
    painter.drawEllipse(3, 3, 26, 26)
    painter.end()
    tray = QSystemTrayIcon(QIcon(pixmap), app)
    menu = QMenu()
    status = menu.addAction("STARTING")
    status.setEnabled(False)
    actions = {}
    for label, command in [("Pausar escucha", "pause"), ("Reanudar / reintentar", "resume"),
                           ("Probar activación manual", "wake")]:
        action = menu.addAction(label)
        action.triggered.connect(lambda checked=False, c=command: manager.command(c))
        actions[command] = action
    sampler = ResourceSampler()
    def diagnostics():
        path = write_report(root, {**manager.snapshot(), "resources": sampler.report()})
        os.startfile(path)
    menu.addAction("Abrir diagnósticos", diagnostics)
    menu.addAction("Abrir ubicación de registros", lambda: os.startfile(root / "logs"))
    menu.addSeparator()
    for label,command in [('Probar voz Piper','test_tts'),('Activar / desactivar respuestas habladas','toggle_tts'),
                          ('Repetir reconocimiento (diagnóstico)','toggle_echo'),
                          ('Cancelar respuesta','cancel_response'),('Probar transcripción (habla al activar)','wake')]:
        action=menu.addAction(label)
        action.triggered.connect(lambda checked=False,c=command:manager.command(c))
    engines=menu.addMenu('Motor de reconocimiento')
    for engine in ('moonshine-small','moonshine-tiny','whisper-base','whisper-small'):
        action=engines.addAction(engine)
        action.triggered.connect(lambda checked=False,e=engine:manager.command('stt:'+e))
    menu.addSeparator()
    menu.addAction("Salir completamente", app.quit)
    tray.setContextMenu(menu)
    events = WindowsEvents(app, manager.command, manager.config.device == "auto")
    def update(state):
        status.setText(state)
        tray.setToolTip("Jarvis · " + state)
        actions["pause"].setEnabled(state in ("DORMANT", "AWAKE", "DEGRADED"))
        actions["resume"].setEnabled(state in ("PAUSED", "DEGRADED"))
        actions["wake"].setEnabled(state == "DORMANT")
        if state == "STOPPING":
            app.quit()
    bridge = StateBridge()
    bridge.changed.connect(update)
    bridge.voice_changed.connect(lambda value: status.setText('AWAKE · '+value))
    manager.bus.subscribe(lambda event: bridge.changed.emit(event.detail["state"])
                          if event.kind == Kind.STATE_CHANGED else None)
    manager.bus.subscribe(lambda event: bridge.voice_changed.emit(event.detail['voice_state'])
                          if event.kind == Kind.VOICE_STATE else None)
    resources = QTimer()
    resources.timeout.connect(sampler.sample)
    resources.start(5000)
    sampler.sample()
    manager.start()
    tray.show()
    if exit_after:
        QTimer.singleShot(round(exit_after * 1000), app.quit)
    try:
        return app.exec()
    finally:
        resources.stop()
        events.close()
        manager.stop()
        sampler.sample()
        write_report(root, {**manager.snapshot(), "resources": sampler.report()})
        tray.hide()
