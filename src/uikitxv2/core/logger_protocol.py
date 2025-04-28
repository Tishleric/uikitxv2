from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerProtocol(Protocol):
    """Contract for writing trace events into any backend (SQLite, Cloud, etc.)."""

    @abstractmethod
    def write(  # noqa: D401 – imperative verb acceptable
        self,
        log_type: str,           # 'perf' · 'data' · 'move'
        name: str,               # human-friendly label (e.g., function name)
        data: dict[str, Any],    # free-form payload
        *,
        ts: datetime | None = None,  # UTC; backend stamps if None
        duration_ms: float | None = None,  # optional performance metric
    ) -> None: ...
