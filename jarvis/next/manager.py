"""Only this layer commits state. Providers receive copies and never permissions."""
import math
import threading
import time
import uuid
from dataclasses import dataclass, field
from .contracts import ContextView, Decision, PlanItem
from .direct import direct_decision


class StaleDecision(Exception):
    pass


class PolicyError(Exception):
    pass


@dataclass(frozen=True)
class Ticket:
    session_id: str
    turn_id: str
    serial: int
    epoch: int
    revision: int
    text: str = field(repr=False)


class ActionPolicy:
    def __init__(self, registry):
        self.registry = registry

    def assess(self, decision: Decision, text: str, context: ContextView):
        if decision.expected_revision != context.revision or decision.plan_id != context.plan_id:
            raise PolicyError()
        known = {item.action_id: item.call for item in context.items}
        ids = [*decision.action_ids, *(change.action_id for change in decision.changes)]
        if len(ids) != len(set(ids)) or any(key not in known for key in ids):
            raise PolicyError()
        spans = [decision.evidence, *(call.evidence for call in decision.actions)]
        if any(span and (span.end > len(text) or not text[span.start:span.end].strip()) for span in spans):
            raise PolicyError()
        for call in decision.actions:
            self.registry.validate(call)
            if any(key not in known for key in call.depends_on):
                raise PolicyError()
        for change in decision.changes:
            call = known[change.action_id]
            self.registry.validate(call.model_copy(update={'target': change.target or call.target,
                'parameters': {**call.parameters, **change.parameters}}))
        # Reconstruct local evidence independently of route or provider claims.
        # Complex semantic authorization is intentionally not implemented yet.
        canonical = direct_decision(text, context)
        if canonical == decision:
            return 'direct'
        if canonical is not None:
            raise PolicyError()
        return 'withheld'


class ActionManager:
    def __init__(self, registry, ttl=120.0, clock=time.monotonic):
        if not math.isfinite(ttl) or not 1 <= ttl <= 600:
            raise ValueError('Invalid context TTL')
        self.registry, self.clock, self.ttl = registry, clock, ttl
        self.policy = ActionPolicy(registry)
        self._lock = threading.RLock()
        self._context = ContextView()
        self._session = None
        self._serial = self._epoch = 0
        self._expires = clock() + ttl
        self._closed = False

    def begin_session(self, session_id):
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 64:
            raise ValueError('Invalid session identifier')
        with self._lock:
            if self._closed:
                raise StaleDecision()
            self._session = session_id
            self._serial += 1
            self._epoch += 1
            self._context = ContextView()
            self._expires = self.clock() + self.ttl

    def _expire(self):
        if self.clock() >= self._expires:
            self._context = ContextView(revision=self._context.revision+1)
            self._epoch += 1
            self._expires = self.clock() + self.ttl

    def snapshot(self):
        with self._lock:
            self._expire()
            return self._context.model_copy(deep=True)

    def begin_turn(self, text, session_id, turn_id):
        with self._lock:
            self._expire()
            if self._closed or session_id != self._session:
                raise StaleDecision()
            self._serial += 1
            return Ticket(session_id, turn_id, self._serial, self._epoch, self._context.revision, text)

    def current(self, ticket):
        with self._lock:
            return (not self._closed and ticket.session_id == self._session
                and ticket.epoch == self._epoch and ticket.serial == self._serial
                and ticket.revision == self._context.revision and self.clock() < self._expires)

    def apply(self, ticket, decision):
        with self._lock:
            if not self.current(ticket):
                raise StaleDecision()
            # All candidate validation precedes state changes and simulated results.
            try:
                authorization = self.policy.assess(decision, ticket.text, self._context)
            except (ValueError, PolicyError):
                raise PolicyError() from None
            if not self.current(ticket):
                raise StaleDecision()
            if authorization != 'direct':
                return 'withheld', (), 'La propuesta necesita validación contextual; no he ejecutado acciones.', self._context.model_copy(deep=True)
            base = self._context
            if decision.operation == 'cancel_all':
                self._context = ContextView(plan_id=base.plan_id, revision=base.revision+1, status='cancelled')
                message, disposition, results = 'Descarté el plan pendiente. No he revertido acciones físicas.', 'cancelled', ()
            elif decision.operation == 'hold':
                self._context = base.model_copy(update={'revision': base.revision+1, 'status': 'withheld'}, deep=True)
                message, disposition, results = 'El plan queda retenido. No he ejecutado acciones.', 'held', ()
            elif decision.operation == 'negated':
                return 'held', (), 'No he cancelado el plan.', base.model_copy(deep=True)
            elif decision.operation == 'query_state':
                return 'simulated', tuple(self.registry.simulate(call) for call in decision.actions), 'No puedo confirmar el volumen real: la herramienta solo está simulada.', base.model_copy(deep=True)
            else:
                results = tuple(self.registry.simulate(call) for call in decision.actions)
                self._context = ContextView(plan_id=uuid.uuid4().hex, revision=base.revision+1, status='simulated',
                    items=tuple(PlanItem(action_id=uuid.uuid4().hex, call=call.model_copy(deep=True)) for call in decision.actions))
                call = decision.actions[0]
                descriptions = {
                    'applications.open': f'abriría {call.target}',
                    'system_audio.set_volume': f'ajustaría el volumen al {call.parameters.get("value")}%',
                    'system_audio.set_mute': 'silenciaría el audio',
                    'media.pause': 'pausaría la música',
                }
                message, disposition = 'En simulación, ' + descriptions[call.tool] + '.', 'simulated'
            self._expires = self.clock() + self.ttl
            return disposition, results, message, self._context.model_copy(deep=True)

    def can_publish(self, outcome):
        """The future speech bridge must check this immediately before TTS."""
        with self._lock:
            return (not self._closed and outcome.session_id == self._session
                and outcome.generation == self._serial and outcome.plan.revision == self._context.revision
                and self.clock() < self._expires and outcome.disposition != 'stale')

    def close(self):
        with self._lock:
            self._closed = True
            self._serial += 1
            self._context = ContextView(revision=self._context.revision+1, status='cancelled')
