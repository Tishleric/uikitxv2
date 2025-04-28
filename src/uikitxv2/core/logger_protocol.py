# src/uikitxv2/core/logger_protocol.py
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .trace_event import TraceEvent


# --------------------------------------------------------------------- #
# Protocol
# --------------------------------------------------------------------- #
@runtime_checkable
class LoggerProtocol(Protocol):
    """Contract for writing trace events into any backend (SQLite, Cloud…)."""

    # **new API** – preferred by BaseDecorator subclasses
    @abstractmethod
    def log(self, ev: TraceEvent) -> None: ...

    # **legacy API** – still used by old tests; delegates to .log()
    def write(
        self,
        log_type: str,
        name: str,
        data: dict[str, Any],
        *,
        ts: datetime | None = None,
        duration_ms: float | None = None,
    ) -> None:  # noqa: D401
        ev = TraceEvent(
            timestamp=ts or datetime.utcnow(),
            session_id="legacy",
            span_id="legacy",
            parent_span_id=None,
            seq=0,
            func=name,
            wall_ms=duration_ms,
            details={"log_type": log_type, **data},
        )
        self.log(ev)


# --------------------------------------------------------------------- #
# Singleton accessor (DI)
# --------------------------------------------------------------------- #
_logger: LoggerProtocol | None = None


def set_logger(logger: LoggerProtocol) -> None:
    global _logger
    _logger = logger


def get_logger() -> LoggerProtocol:
    if _logger is None:
        from uikitxv2.db.sqlite_logger import SQLiteLogger  # lazy import
        set_logger(SQLiteLogger())
    return _logger
