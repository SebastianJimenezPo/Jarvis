from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Kind(str, Enum):
    VOICE_STATE = "voice_state"
    STATE_CHANGED = "state_changed"
    WAKEWORD_DETECTED = "wakeword_detected"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    AUDIO_READY = "audio_ready"
    FAILURE = "failure"


@dataclass(frozen=True)
class Event:
    kind: Kind
    generation: int
    session: int
    detail: dict


class EventBus:
    """Synchronous observers on the controller thread; observers must be quick."""
    def __init__(self):
        self._listeners: list[Callable[[Event], None]] = []

    def subscribe(self, listener: Callable[[Event], None]):
        self._listeners.append(listener)

    def publish(self, event: Event):
        import logging
        for listener in tuple(self._listeners):
            try:
                listener(event)
            except Exception:
                logging.getLogger("jarvis").exception("event_observer_failed")
