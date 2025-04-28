from __future__ import annotations

import functools
import inspect
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Protocol, runtime_checkable

from .logger_protocol import get_logger  # existing helper returning singleton
from .trace_control import get_session_id, is_enabled
from .trace_event import TraceEvent


@runtime_checkable
class LoggerProtocol(Protocol):
    def log(self, ev: TraceEvent) -> None: ...

_span_stack: ContextVar[list[str]] = ContextVar("span_stack", default=[])

class BaseDecorator:
    def __call__(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        is_coroutine = inspect.iscoroutinefunction(fn)

        @functools.wraps(fn)
        async def _aw(*args: Any, **kw: Any):
            return await self._invoke(fn, args, kw)

        @functools.wraps(fn)
        def _sync(*args: Any, **kw: Any):
            return self._invoke(fn, args, kw)

        return _aw if is_coroutine else _sync  # type: ignore[return-value]

    def _invoke(self, fn: Callable[..., Any], args, kw):
        if not is_enabled():
            return fn(*args, **kw)

        stack = _span_stack.get()
        parent = stack[-1] if stack else None
        span_id = uuid.uuid4().hex
        stack.append(span_id)
        _span_stack.set(stack)

        ev = TraceEvent(
            timestamp=time.utcnow(),  # py311: datetime.utcnow is naive; adjust later
            session_id=get_session_id(),
            span_id=span_id,
            parent_span_id=parent,
            seq=0,  # logger will fill
            func=f"{fn.__module__}.{fn.__qualname__}",
            details={},
        )
        try:
            result = self._collect(fn, ev, *args, **kw)
            return result
        except Exception as err:  # noqa: BLE001
            ev.error = repr(err)
            raise
        finally:
            get_logger().log(ev)
            _span_stack.get().pop()

    # concrete decorators override
    def _collect(self, fn, ev: TraceEvent, *a, **k):  # noqa: ANN001
        return fn(*a, **k)
