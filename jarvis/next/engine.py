"""Text-only entry: one direct route or one provider, followed by local policy."""
import time
import uuid
from pydantic import ValidationError
from .contracts import Decision, InterpretationRequest, Outcome, Usage
from .direct import direct_decision
from .manager import ActionManager, PolicyError, StaleDecision
from .providers import OfflineProvider, ProviderError, ProviderRunner
from .tools import default_registry


class NextEngine:
    def __init__(self, provider=None, registry=None, timeout=3.0, ttl=120.0, clock=time.monotonic, review_enabled=False):
        self.registry = registry or default_registry()
        self.manager = ActionManager(self.registry, ttl, clock, review_enabled)
        self.runner = ProviderRunner(provider if provider is not None else OfflineProvider(), timeout)

    def begin_session(self, session_id):
        self.manager.begin_session(session_id)

    def interpret(self, text, session_id='cli', turn_id='1'):
        start = time.perf_counter()
        if not isinstance(text, str) or not text.strip() or len(text) > 1600:
            raise ValueError('Expected 1..1600 characters of text')
        if not isinstance(turn_id, str) or not 1 <= len(turn_id) <= 64:
            raise ValueError('Invalid turn identifier')
        route, decision, usage = 'direct', None, Usage()
        proposed_operation = None
        request_id, ticket = uuid.uuid4().hex, None

        def outcome(disposition, message, error=None, results=(), plan=None, policy_reason=None):
            return Outcome(request_id=request_id, session_id=session_id, turn_id=turn_id,
                generation=ticket.serial if ticket else 0, route=route, disposition=disposition, decision=decision,
                plan=plan if plan is not None else self.manager.snapshot(), results=results, message=message,
                error=error, seconds=time.perf_counter()-start, usage=usage,
                proposed_operation=proposed_operation, policy_reason=policy_reason)

        try:
            ticket = self.manager.begin_turn(text, session_id, turn_id)
            context = self.manager.snapshot()
            decision = direct_decision(text, context)
            if decision is None:
                route = 'offline' if isinstance(self.runner.provider, OfflineProvider) else 'provider'
                request = InterpretationRequest(request_id=request_id, session_id=session_id,
                    turn_id=turn_id, text=text, context=context, capabilities=self.registry.capabilities())
                reply = self.runner.call(request, lambda: self.manager.current(ticket))
                try:
                    decision = Decision.model_validate_json(reply.decision_json)
                except (ValidationError, ValueError):
                    raise ProviderError('invalid_response') from None
                usage = reply.usage
                self.runner.record()
            proposed_operation = decision.operation
            disposition, results, message, plan = self.manager.apply(ticket, decision)
            result = outcome(disposition, message, results=results, plan=plan)
            return result.model_copy(update={'review': self.manager.review(ticket)})
        except StaleDecision:
            decision = None
            return outcome('stale', '', 'stale')  # No cancelled/stale text may reach TTS.
        except ProviderError as exc:
            decision = None
            self.runner.record(exc.code)
            if exc.code in ('stale', 'cancelled', 'closed'):
                return outcome('stale', '', exc.code)
            return outcome('unavailable', 'El intérprete no está disponible. Puedo seguir con órdenes directas locales.', exc.code)
        except PolicyError as exc:
            decision = None
            return outcome('rejected', 'No puedo validar esa propuesta. No he ejecutado acciones.', 'policy_rejected', policy_reason=exc.reason)

    def cancel(self, session_id='cli', turn_id='ui-cancel'):
        return self.interpret('Cancela', session_id, turn_id)

    def confirm(self, review_id, session_id='cli', turn_id='local-review'):
        start = time.perf_counter()
        try:
            ticket, decision, disposition, results, message, plan = self.manager.confirm(review_id, session_id, turn_id)
            generation = ticket.serial
            error = 'review_invalid' if decision is None else None
        except StaleDecision:
            decision, disposition, results, message = None, 'stale', (), ''
            generation, error, plan = 0, 'stale', self.manager.snapshot()
        return Outcome(request_id=uuid.uuid4().hex, session_id=session_id, turn_id=turn_id,
            generation=generation, route='direct', disposition=disposition, decision=decision,
            plan=plan, results=results, message=message, error=error, seconds=time.perf_counter()-start)

    def close(self):
        self.manager.close()
        self.runner.close()
