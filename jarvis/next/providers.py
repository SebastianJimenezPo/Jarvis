"""One bounded on-demand provider request; no automatic fallback or networking."""
import math
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Literal, Protocol
from .contracts import InterpretationRequest, ProviderReply

ErrorCode = Literal['unavailable', 'connection', 'authentication', 'quota', 'model_unavailable',
                    'timeout', 'cancelled', 'stale', 'invalid_response', 'busy', 'suspended', 'closed']


class ProviderError(Exception):
    def __init__(self, code: ErrorCode):
        if code not in ErrorCode.__args__:
            code = 'unavailable'
        self.code = code
        super().__init__(code)  # Never retain raw provider errors, headers or credentials.


@dataclass(frozen=True)
class ProviderCapabilities:
    name: str
    structured_output: bool = True
    remote: bool = False


@dataclass(frozen=True)
class RequestControl:
    deadline: float
    cancelled: threading.Event = field(default_factory=threading.Event)

    def checkpoint(self):
        if self.cancelled.is_set():
            raise ProviderError('cancelled')
        if time.monotonic() >= self.deadline:
            raise ProviderError('timeout')


class InterpretationProvider(Protocol):
    capabilities: ProviderCapabilities

    def interpret(self, request: InterpretationRequest, control: RequestControl) -> ProviderReply: ...
    def close(self) -> None: ...


class OfflineProvider:
    capabilities = ProviderCapabilities('offline', structured_output=False)

    def interpret(self, request, control):
        control.checkpoint()
        raise ProviderError('unavailable')

    def close(self):
        pass


class FakeProvider:
    """Explicit test dependency, never selected by the CLI. No transcript logging."""
    capabilities = ProviderCapabilities('fake')

    def __init__(self, responder: Callable):
        self.responder = responder
        self.calls = 0
        self.closed = False

    def interpret(self, request, control):
        control.checkpoint()
        self.calls += 1
        return self.responder(request, control)

    def close(self):
        self.closed = True


class ProviderRunner:
    def __init__(self, provider: InterpretationProvider, timeout=3.0):
        if not math.isfinite(timeout) or not 0.01 <= timeout <= 30:
            raise ValueError('Invalid provider timeout')
        self.provider, self.timeout = provider, timeout
        self._slot = threading.Lock()
        self._lock = threading.Lock()
        self._closed = False
        self._control = None
        self._failures = 0
        self._suspended_until = 0.0

    def call(self, request, current):
        with self._lock:
            if self._closed:
                raise ProviderError('closed')
            if time.monotonic() < self._suspended_until:
                raise ProviderError('suspended')
            if not self._slot.acquire(blocking=False):
                raise ProviderError('busy')
            control = RequestControl(time.monotonic() + self.timeout)
            self._control = control
        done = threading.Event()
        result = []

        def work():
            try:
                result.append(self.provider.interpret(request, control))
            except ProviderError as exc:
                result.append(ProviderError(exc.code))
            except Exception:
                result.append(ProviderError('unavailable'))
            finally:
                self._slot.release()
                done.set()

        # An uncooperative provider cannot block the caller or spawn an unbounded
        # fallback chain. Its sole slot stays occupied until it actually exits.
        threading.Thread(target=work, name='jarvis-next-provider', daemon=True).start()
        try:
            while True:
                if not current():
                    raise ProviderError('stale')
                control.checkpoint()
                if done.wait(min(0.02, max(0, control.deadline-time.monotonic()))):
                    break
            control.checkpoint()
            if not current():
                raise ProviderError('stale')
            if isinstance(result[0], ProviderError):
                raise result[0]
            return ProviderReply.model_validate(result[0])
        except ProviderError:
            control.cancelled.set()
            raise
        except Exception:
            raise ProviderError('invalid_response') from None
        finally:
            with self._lock:
                if self._control is control:
                    self._control = None

    def record(self, error=None):
        with self._lock:
            if error in ('stale', 'cancelled', 'busy', 'suspended', 'closed'):
                return
            self._failures = self._failures + 1 if error else 0
            if self._failures >= 3:
                self._suspended_until = time.monotonic() + 15
                self._failures = 0

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._control:
                self._control.cancelled.set()
        try:
            self.provider.close()
        except Exception:
            pass  # Never surface a credential-bearing SDK exception.
