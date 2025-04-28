from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(slots=True)
class TraceEvent:
    timestamp: datetime
    session_id: str
    span_id: str
    parent_span_id: Optional[str]
    seq: int
    func: str
    wall_ms: float | None = None
    cpu_pct_start: float | None = None
    cpu_pct_end: float | None = None
    error: str | None = None
    details: Dict[str, Any] = None
