import time
from enum import Enum
from .events import Event, EventBus, Kind


class State(str, Enum):
    STARTING = "STARTING"
    DORMANT = "DORMANT"
    AWAKE = "AWAKE"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"


ALLOWED = {
    State.STARTING: {State.DORMANT, State.DEGRADED, State.PAUSED, State.STOPPING},
    State.DORMANT: {State.AWAKE, State.PAUSED, State.DEGRADED, State.STOPPING},
    State.AWAKE: {State.DORMANT, State.PAUSED, State.DEGRADED, State.STOPPING},
    State.PAUSED: {State.DORMANT, State.DEGRADED, State.STOPPING},
    State.DEGRADED: {State.DORMANT, State.PAUSED, State.STOPPING},
    State.STOPPING: set(),
}


class StateMachine:
    def __init__(self, bus: EventBus, active_seconds=10.0, cooldown_seconds=3.0, clock=time.monotonic):
        self.bus, self.clock = bus, clock
        self.active_seconds, self.cooldown_seconds = active_seconds, cooldown_seconds
        self.state = State.STARTING
        self.session = self.generation = 0
        self.deadline = None
        self.next_wake = 0.0
        self.since = clock()
        self.durations = {s.value: 0.0 for s in State}

    def emit(self, kind, **detail):
        self.bus.publish(Event(kind, self.generation, self.session, detail))

    def transition(self, target: State, reason: str):
        if target == self.state:
            return
        if target not in ALLOWED[self.state]:
            raise ValueError(f"Transición inválida: {self.state} → {target}")
        now, previous = self.clock(), self.state
        self.durations[previous.value] += now - self.since
        self.since, self.state = now, target
        if previous == State.AWAKE:
            self.deadline = None
            self.next_wake = now + self.cooldown_seconds
            self.emit(Kind.SESSION_ENDED, reason=reason)
        self.emit(Kind.STATE_CHANGED, previous=previous.value, state=target.value, reason=reason)

    def invalidate(self):
        self.generation += 1
        self.deadline = None

    def wake(self, generation: int, score=None, manual=False) -> bool:
        if generation != self.generation or self.state != State.DORMANT or self.clock() < self.next_wake:
            return False
        self.session += 1
        self.transition(State.AWAKE, "manual" if manual else "wakeword")
        self.deadline = self.clock() + self.active_seconds
        self.emit(Kind.WAKEWORD_DETECTED, score=score, manual=manual)
        self.emit(Kind.SESSION_STARTED)
        return True

    def tick(self, session=None):
        if session is not None and session != self.session:
            return
        if self.state == State.AWAKE and self.deadline is not None and self.clock() >= self.deadline:
            self.transition(State.DORMANT, "session_timeout")

    def snapshot(self):
        durations = self.durations.copy()
        durations[self.state.value] += self.clock() - self.since
        return {"state": self.state.value, "session": self.session,
                "generation": self.generation, "state_seconds": durations}
