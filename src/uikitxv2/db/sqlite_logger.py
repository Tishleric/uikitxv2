from __future__ import annotations

import json
from datetime import datetime
from typing import Any, DefaultDict, Dict
from collections import defaultdict

from sqlalchemy import text

from uikitxv2.db.session import get_engine    # NEW – authoritative
from uikitxv2.core.logger_protocol import LoggerProtocol
from uikitxv2.core.trace_event import TraceEvent

_seq_counter: DefaultDict[str, int] = defaultdict(int)

class SQLiteLogger(LoggerProtocol):
    def log(self, ev: TraceEvent) -> None:
        """Persist a TraceEvent row into trace_log."""
        ev.seq = _seq_counter[ev.session_id] = _seq_counter[ev.session_id] + 1
        payload: Dict[str, Any] = ev.details or {}
        engine = get_engine()                         # fetch per-call
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO trace_log
                      (ts, log_type, name, duration_ms, payload_json)
                    VALUES
                      (:ts, :log_type, :name, :dur, json(:payload))
                    """
                ),
                {
                    "ts": ev.timestamp.isoformat(timespec="milliseconds"),
                    "log_type": "perf",
                    "name": ev.func,
                    "dur": ev.wall_ms,
                    "payload": json.dumps(payload),
                },
            )

    # Back-compat for old tests that still call .write()
    def write(  # noqa: D401
        self,
        log_type: str,
        name: str,
        data: dict[str, Any],
        *,
        ts: datetime | None = None,
        duration_ms: float | None = None,
    ) -> None:
        ev = TraceEvent(
            timestamp=ts or datetime.utcnow(),
            session_id="legacy",
            span_id="legacy",
            parent_span_id=None,
            seq=0,
            func=name,
            wall_ms=duration_ms,
            details=data,
        )
        self.log(ev)
