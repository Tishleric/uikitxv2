from __future__ import annotations

import functools
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Callable

import psutil

from uikitxv2.core.logger_protocol import get_logger
from uikitxv2.core.trace_control import get_session_id
from uikitxv2.core.trace_event import TraceEvent

_span_stack: ContextVar[list[str]] = ContextVar("_span_stack", default=[])

def trace_cpu() -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # decorator factory
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            # span handling
            stack = _span_stack.get()
            parent = stack[-1] if stack else None
            span_id = uuid.uuid4().hex
            stack.append(span_id)
            _span_stack.set(stack)

            start_cpu = psutil.cpu_percent(interval=None)
            t0 = time.perf_counter()
            error = None
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                error = repr(exc)
                raise
            finally:
                ev = TraceEvent(
                    timestamp=datetime.now(timezone.utc),
                    session_id=get_session_id(),
                    span_id=span_id,
                    parent_span_id=parent,
                    seq=0,  # logger fills
                    func=f"{fn.__module__}.{fn.__qualname__}",
                    wall_ms=(time.perf_counter() - t0) * 1000,
                    cpu_pct_start=start_cpu,
                    cpu_pct_end=psutil.cpu_percent(interval=None),
                    error=error,
                    details={},
                )
                get_logger().log(ev)
                _span_stack.get().pop()

        return wrapper

    return decorator
