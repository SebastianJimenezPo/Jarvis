"""Only this layer commits state. Providers receive copies and never permissions."""
import math
import threading
import time
import uuid
from dataclasses import dataclass, field
from .contracts import ContextView, Decision, PlanItem, PlanReview, PolicyReason
from .direct import direct_decision
from .scope import blocked_scope


class StaleDecision(Exception):
    pass


class PolicyError(Exception):
    def __init__(self, reason='catalog'):
        self.reason = reason if reason in PolicyReason.__args__ else 'catalog'
        super().__init__(self.reason)


@dataclass(frozen=True)
class Ticket:
    session_id: str
    turn_id: str
    serial: int
    epoch: int
    revision: int
    text: str = field(repr=False)


@dataclass(frozen=True)
class PendingReview:
    ticket: Ticket
    decision: Decision
    view: PlanReview
    touched: tuple
    expires: float


class ActionPolicy:
    def __init__(self, registry):
        self.registry = registry

    def assess(self, decision: Decision, text: str, context: ContextView):
        if decision.expected_revision != context.revision:
            raise PolicyError('revision')
        if decision.plan_id != context.plan_id:
            raise PolicyError('plan_identity')
        known = {item.action_id: item.call for item in context.items}
        ids = [*decision.action_ids, *(change.action_id for change in decision.changes)]
        if len(ids) != len(set(ids)) or any(key not in known for key in ids):
            raise PolicyError('reference')
        spans = [decision.evidence, *(call.evidence for call in decision.actions)]
        if any(span and (span.end > len(text) or not text[span.start:span.end].strip()) for span in spans):
            raise PolicyError('evidence')
        for call in decision.actions:
            self.registry.validate(call)
            if self.registry.is_read(call) != (decision.operation == 'query_state'):
                raise PolicyError()
            if any(key not in known for key in call.depends_on):
                raise PolicyError('reference')
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
            raise PolicyError('direct_mismatch')
        return 'withheld'


class ActionManager:
    def __init__(self, registry, ttl=120.0, clock=time.monotonic, review_enabled=False):
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
        self._pending = None
        self.review_enabled = review_enabled is True

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
            self._pending = None
            self._expires = self.clock() + self.ttl

    def _expire(self):
        if self.clock() >= self._expires:
            self._context = ContextView(revision=self._context.revision+1)
            self._pending = None
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
            self._pending = None  # Any new ordinary turn supersedes the review.
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
            except PolicyError:
                raise
            except ValueError:
                raise PolicyError() from None
            if not self.current(ticket):
                raise StaleDecision()
            if authorization != 'direct':
                if self.review_enabled:
                    self._prepare_review(ticket, decision)
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

    def _prepare_review(self, ticket, decision):
        supported = ('create_plan', 'replace_plan', 'append_plan', 'modify_plan', 'remove_actions',
                     'cancel_subset', 'cancel_all', 'hold', 'query_state')
        if decision.operation not in supported:
            return
        if reason := blocked_scope(ticket.text, self._context):
            raise PolicyError(reason)
        context_bound = (decision.operation in ('hold', 'cancel_all', 'cancel_subset', 'remove_actions', 'modify_plan')
                         and decision.plan_id is not None and decision.plan_id == self._context.plan_id)
        if not decision.evidence and not decision.actions and not context_bound:
            raise PolicyError('scope')
        if decision.operation not in ('cancel_all', 'hold') and decision.temporal != 'now':
            raise PolicyError('temporal')
        proposed, touched = self._project(decision)
        now = self.clock()
        expires = min(self._expires, now+30)
        if expires <= now:
            raise StaleDecision()
        view = PlanReview(review_id=uuid.uuid4().hex, operation=decision.operation,
            source_text=ticket.text, base_revision=self._context.revision, proposed_plan=proposed, expires_in_seconds=expires-now)
        self._pending = PendingReview(ticket, decision.model_copy(deep=True), view,
            tuple(call.model_copy(deep=True) for call in touched), expires)

    def _project(self, decision):
        """Pure bounded reducer for a draft. Never authorizes or executes tools."""
        base, op = self._context, decision.operation
        if op in ('cancel_all', 'hold'):
            return ContextView(plan_id=base.plan_id, revision=base.revision+1,
                status='cancelled' if op == 'cancel_all' else 'withheld',
                items=() if op == 'cancel_all' else base.items), ()
        if op == 'query_state':
            return base.model_copy(deep=True), tuple(decision.actions)
        existing = list(base.items)
        touched = []
        plan_id = base.plan_id
        if op in ('create_plan', 'replace_plan'):
            existing, plan_id = [], uuid.uuid4().hex
        elif not plan_id or not existing:
            raise PolicyError('missing_plan')
        if op in ('cancel_subset', 'remove_actions'):
            existing = [item for item in existing if item.action_id not in decision.action_ids]
        elif op == 'modify_plan':
            changes = {change.action_id: change for change in decision.changes}
            updated = []
            for item in existing:
                change = changes.get(item.action_id)
                if change:
                    call = item.call.model_copy(update={'target': change.target or item.call.target,
                        'parameters': {**item.call.parameters, **change.parameters}, 'evidence': decision.evidence}, deep=True)
                    self.registry.validate(call)
                    touched.append(call)
                    item = item.model_copy(update={'call': call}, deep=True)
                updated.append(item)
            existing = updated
        for call in decision.actions:
            touched.append(call.model_copy(deep=True))
            existing.append(PlanItem(action_id=uuid.uuid4().hex, call=call.model_copy(deep=True)))
        keys = [(item.call.tool, item.call.target) for item in existing]
        ids = {item.action_id for item in existing}
        if len(keys) != len(set(keys)):
            raise PolicyError('conflict')
        if any(dep not in ids for item in existing for dep in item.call.depends_on):
            raise PolicyError('reference')
        try:
            proposed = ContextView(plan_id=plan_id, revision=base.revision+1,
                status='withheld' if existing else 'cancelled', items=tuple(existing))
        except ValueError:
            raise PolicyError('capacity') from None
        return proposed, tuple(touched)

    def review(self, ticket):
        with self._lock:
            pending = self._pending
            if pending and self.current(ticket) and pending.ticket == ticket and self.clock() < pending.expires:
                return pending.view.model_copy(deep=True)
            return None

    def confirm(self, review_id, session_id, turn_id):
        """Developer pilot: an explicit local review of THIS draft, simulation only."""
        with self._lock:
            self._expire()
            if self._closed or session_id != self._session:
                raise StaleDecision()
            pending, self._pending = self._pending, None
            previous_serial = self._serial
            self._serial += 1
            ticket = Ticket(session_id, turn_id, self._serial, self._epoch, self._context.revision, '')
            if (pending is None or pending.view.review_id != review_id or self.clock() >= pending.expires
                or pending.ticket.serial != previous_serial or pending.ticket.epoch != self._epoch
                or pending.ticket.revision != self._context.revision):
                return ticket, None, 'rejected', (), 'La propuesta no está vigente. Solicítala otra vez.', self._context.model_copy(deep=True)
            # Parameters and current capabilities are checked again before commit.
            for call in pending.touched:
                self.registry.validate(call)
            results = tuple(self.registry.simulate(call) for call in pending.touched)
            if not self.current(ticket):
                raise StaleDecision()
            decision = pending.decision
            projected = pending.view.proposed_plan.model_copy(deep=True)
            op = decision.operation
            if op not in ('hold', 'query_state') and projected.items:
                projected = projected.model_copy(update={'status': 'simulated'})
            self._context = projected
            self._expires = self.clock()+self.ttl
            if op == 'query_state':
                message, disposition = 'No puedo confirmar el estado real: solo hay herramientas simuladas.', 'simulated'
            elif op == 'hold':
                message, disposition = 'El plan queda retenido. No he ejecutado acciones.', 'held'
            elif op == 'cancel_all' or not projected.items:
                message, disposition = 'Descarté las propuestas indicadas. No he revertido acciones físicas.', 'cancelled'
            else:
                message, disposition = 'En simulación, apliqué la revisión del plan. No he ejecutado acciones físicas.', 'simulated'
            return ticket, decision, disposition, results, message, projected.model_copy(deep=True)

    def can_publish(self, outcome):
        """The future speech bridge must check this immediately before TTS."""
        with self._lock:
            return (not self._closed and outcome.session_id == self._session
                and outcome.generation == self._serial and outcome.plan.revision == self._context.revision
                and self.clock() < self._expires and outcome.disposition != 'stale')

    def close(self):
        with self._lock:
            self._closed = True
            self._pending = None
            self._serial += 1
            self._context = ContextView(revision=self._context.revision+1, status='cancelled')
