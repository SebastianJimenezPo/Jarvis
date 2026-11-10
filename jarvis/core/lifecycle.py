"""Single owner of capture, detector and state. GUI communicates through commands."""
import json
import logging
import queue
import threading
import time
from dataclasses import asdict
from jarvis.audio.capture import Capture
from jarvis.audio.converter import Converter
from jarvis.audio.buffers import RingBuffer
from jarvis.wakeword.rustpotter_adapter import RustpotterDetector
from .events import EventBus, Kind
from .state_machine import StateMachine, State


class LifecycleManager:
    def __init__(self, config, root, capture_factory=Capture, detector_factory=RustpotterDetector):
        self.config, self.root = config, root
        self.capture_factory, self.detector_factory = capture_factory, detector_factory
        self.bus = EventBus()
        self.bus.subscribe(self._log_event)
        self.machine = StateMachine(self.bus, config.active_seconds, config.cooldown_seconds)
        self.commands = queue.Queue(maxsize=64)
        self.thread = threading.Thread(target=self._run, name="jarvis-lifecycle")
        self.capture = self.detector = None
        self.ring = RingBuffer(round(config.preroll_seconds * 32000))
        self.pending = bytearray()
        self.failures = 0
        self.retry_at = 0.0
        self.suspended = False
        self.user_paused = not config.listening
        self.last_error = None
        self.last_device = None
        self.last_rate = None
        self.metrics = {"activations": 0, "restarts": 0, "capture_failures": 0,
                        "dropped_blocks": 0, "queue_peak": 0, "capture_overflows": 0,
                        "initialization_seconds": None}
        self.started = time.monotonic()
        self.stable_since = None
        self.latest = {**self.machine.snapshot(), **self.metrics}
        self.log = logging.getLogger("jarvis")
        from .voice_session import VoiceSessionManager
        self.voice = VoiceSessionManager(root, self._voice_event)
        self.ignore_audio_before = 0.0

    def _voice_event(self, event):
        self.log.info(event['kind'], extra={'fields':event})
        if event['kind'] == 'voice_state':
            self.machine.emit(Kind.VOICE_STATE,voice_state=event['state'])
        if event['kind'] in ('session_end','voice_error') and self.machine.state == State.AWAKE:
            self.machine.transition(State.DORMANT, event.get('reason',event['kind']))
            self.ring.clear()
            self.pending.clear()
            self.ignore_audio_before = time.monotonic() + self.voice.config.echo_guard_seconds
            # Reset the acoustic detector without reopening the microphone.
            if self.detector:
                self.detector.close()
                self.detector.start()

    def _log_event(self, event):
        self.log.info(event.kind.value, extra={"fields": {"generation": event.generation,
                      "session": event.session, **event.detail}})

    def start(self):
        self.thread.start()

    def command(self, name):
        try:
            self.commands.put_nowait(name)
        except queue.Full:
            self.log.warning("command_queue_full")

    def stop(self):
        self.command("stop")
        self.thread.join(timeout=25)
        if self.thread.is_alive():
            raise RuntimeError("El cierre no terminó; revisar los registros")

    def snapshot(self):
        return self.latest.copy()

    def _snapshot(self):
        metrics = self.metrics.copy()
        if self.capture:
            metrics["dropped_blocks"] += self.capture.blocks.dropped
            metrics["queue_peak"] = max(metrics["queue_peak"], self.capture.blocks.peak)
            metrics["capture_overflows"] += self.capture.overflows
        self.latest = {**self.machine.snapshot(), **metrics, "last_error": self.last_error,
                       "consecutive_failures": self.failures, "retry_at_monotonic": self.retry_at,
                       "capture_device": self.capture.device if self.capture else None,
                       "last_capture_device": self.last_device, "last_capture_rate": self.last_rate,
                       "detector_pid": (self.detector.process_handle.pid if self.detector and
                                         getattr(self.detector, "process_handle", None) else None),
                       "voice": self.voice.snapshot()}

    def _close_resources(self):
        self.voice.close()
        self.machine.invalidate()
        capture, detector = self.capture, self.detector
        self.capture = self.detector = None
        try:
            if capture:
                self.metrics["dropped_blocks"] += capture.blocks.dropped
                self.metrics["queue_peak"] = max(self.metrics["queue_peak"], capture.blocks.peak)
                self.metrics["capture_overflows"] += capture.overflows
                capture.close()
        finally:
            try:
                if detector:
                    detector.close()
            finally:
                self.pending.clear()
                self.ring.clear()

    def _open_resources(self):
        c = self.config
        self.detector = self.detector_factory(c.reference_path(self.root), c.threshold, c.avg_threshold)
        self.detector.start()
        self.capture = self.capture_factory(c.device, c.queue_blocks)
        self.converter = Converter(self.capture.rate)
        self.capture.start()
        self.last_device, self.last_rate = self.capture.device.copy(), self.capture.rate
        self.stable_since = time.monotonic()
        self.retry_at = None
        self.last_error = None
        if self.metrics["initialization_seconds"] is None:
            self.metrics["initialization_seconds"] = time.monotonic() - self.started
        self.machine.emit(Kind.AUDIO_READY, device=self.capture.device, rate=self.capture.rate,
                          target="16000 Hz mono s16le", frame_bytes=self.detector.frame_bytes)
        self.machine.transition(State.DORMANT, "resources_ready")

    def _fail(self, error):
        self.last_error = f"{type(error).__name__}: {error}"
        self.machine.emit(Kind.FAILURE, error=self.last_error)
        self._close_resources()
        self.machine.transition(State.DEGRADED, self.last_error)
        self.failures += 1
        self.metrics["restarts"] += 1
        self.retry_at = (time.monotonic() + min(self.config.retry_max_seconds,
                         self.config.retry_initial_seconds * 2 ** (self.failures - 1))
                         if self.failures < self.config.retry_limit else None)

    def _handle(self, command):
        if command.startswith('llm:'):
            from dataclasses import replace
            from jarvis.intelligence.settings import load_intelligence,save_intelligence
            selected=command.split(':',1)[1]
            if selected not in ('qwen3.5:2b','qwen3:1.7b'):return
            self.voice.close()
            if self.machine.state==State.AWAKE:self._voice_event({'kind':'session_end','reason':'model_changed'})
            save_intelligence(self.root,replace(load_intelligence(self.root),model=selected))
            return
        if command == 'cancel_response':
            self.voice.cancel()
            return
        if command.startswith('stt:') or command in ('toggle_tts','toggle_echo'):
            from dataclasses import replace
            from jarvis.speech.settings import save_voice
            self.voice.close()
            if self.machine.state == State.AWAKE:
                self._voice_event({'kind':'session_end','reason':'configuration_changed'})
            changes=({'engine':command.split(':',1)[1]} if command.startswith('stt:') else
                     {'diagnostic_echo':not self.voice.config.diagnostic_echo} if command=='toggle_echo' else
                     {'tts_enabled':not self.voice.config.tts_enabled})
            self.voice.config = replace(self.voice.config, **changes).validate()
            save_voice(self.root,self.voice.config)
            return
        if command == 'test_tts':
            if self.machine.state == State.DORMANT and self.machine.wake(self.machine.generation,manual=True):
                try:
                    self.voice.start(f'{self.machine.generation}:{self.machine.session}',test_tts=True)
                    self.machine.deadline = None
                except Exception as exc:
                    self._voice_event({'kind':'voice_error','error':str(exc)})
            return
        if command == "stop":
            self.machine.transition(State.STOPPING, "exit")
            return
        if command == "wake":
            self._wake(manual=True)
            return
        if command in ("pause", "suspend"):
            self.retry_at = None
            if command == "pause":
                self.user_paused = True
            else:
                self.suspended = True
            self._close_resources()
            self.machine.transition(State.PAUSED, command)
            return
        if command in ("resume", "power_resume", "devices_changed"):
            if command == "resume":
                self.user_paused = False
            elif command == "power_resume":
                self.suspended = False
            if self.user_paused or self.suspended:
                return
            self._close_resources()
            self.machine.transition(State.DEGRADED, command)
            self.failures = 0
            self.retry_at = time.monotonic() + (0.5 if command == "devices_changed" else 0)

    def _wake(self, score=None, manual=False, evidence=None):
        if not manual:
            import math
            valid_score=type(score) in (int,float) and math.isfinite(score) and 0 <= score <= 1
            if not valid_score or score < self.config.threshold:
                self.log.info('wake_candidate_rejected',extra={'fields':{
                    'score':score if valid_score else None,'threshold':self.config.threshold,
                    'reason':'below_threshold' if valid_score else 'invalid_score',
                    'state':self.machine.state.value}})
                return
            self.log.info('wake_candidate',extra={'fields':{
                'score':score,'threshold':self.config.threshold,'state':self.machine.state.value,
                'avg_score':(evidence or {}).get('avg_score'),
                'partial_matches':(evidence or {}).get('partial_matches'),
                'reference_scores':(evidence or {}).get('reference_scores')}})
        if self.machine.wake(self.machine.generation, score, manual):
            self.metrics["activations"] += 1
            if self.voice.available():
                try:
                    self.voice.start(f'{self.machine.generation}:{self.machine.session}',self.ring.snapshot(),acoustic_activation=not manual)
                    self.machine.deadline = None
                except Exception as exc:
                    self.voice.close()
                    self.log.exception('voice_start_failed_fallback_phase1')
            elif self.voice.config.enabled:
                self.log.warning('voice_unavailable_fallback_phase1',extra={'fields':{'error':self.voice.error}})
            if self.config.confirmation:
                import winsound
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_NODEFAULT)

    def _audio_step(self):
        try:
            timestamp, samples = self.capture.blocks.get(timeout=0.1)
        except queue.Empty:
            if time.monotonic() - self.capture.last_audio > 3:
                self.metrics["capture_failures"] += 1
                raise RuntimeError("No llegan bloques del micrófono desde hace 3 segundos")
            return
        if time.monotonic() - timestamp > 0.5:
            self.metrics["dropped_blocks"] += 1
            return
        if timestamp < self.ignore_audio_before:
            return
        pcm = self.converter.convert(samples)
        if self.voice.active:
            self.voice.feed(pcm,timestamp)
            return
        self.ring.append(pcm)
        self.pending.extend(pcm)
        size = self.detector.frame_bytes
        while len(self.pending) >= size:
            result = self.detector.process(bytes(self.pending[:size]))
            del self.pending[:size]
            if result.get("detected"):
                self._wake(result.get("score"),evidence=result)
                if self.voice.active:
                    self.pending.clear()
                    return

    def _run(self):
        try:
            if self.user_paused:
                self.machine.transition(State.PAUSED, "configuration")
                self.retry_at = None
            while self.machine.state != State.STOPPING:
                try:
                    while True:
                        self._handle(self.commands.get_nowait())
                        if self.machine.state == State.STOPPING:
                            break
                except queue.Empty:
                    pass
                if self.machine.state == State.STOPPING:
                    break
                try:
                    self.voice.poll()
                    if self.retry_at is not None and time.monotonic() >= self.retry_at:
                        self._open_resources()
                    if self.capture:
                        self._audio_step()
                        if self.failures and time.monotonic() - self.stable_since >= 30:
                            self.failures = 0
                    else:
                        try:
                            self._handle(self.commands.get(timeout=0.1))
                        except queue.Empty:
                            pass
                    self.machine.tick()
                except Exception as exc:
                    self._fail(exc)
                self._snapshot()
        except Exception as exc:
            self.last_error = f"Fatal: {exc}"
            self.log.exception("lifecycle_fatal")
            self.machine.transition(State.STOPPING, self.last_error)
        finally:
            self._close_resources()
            self._snapshot()
            self.log.info("shutdown_complete")
