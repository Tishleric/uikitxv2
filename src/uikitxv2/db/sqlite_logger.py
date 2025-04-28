from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict

from sqlalchemy import create_engine, text

from uikitxv2.core.logger_protocol import LoggerProtocol
from uikitxv2.core.trace_event import TraceEvent

_DB_PATH = Path(
    os.environ.get("UIKITX_DB_PATH", Path.home() / ".uikitx" / "traces.db")
)
engine = create_engine(f"sqlite:///{_DB_PATH}", future=True)

_seq_counter: DefaultDict[str, int] = defaultdict(int)

class SQLiteLogger(LoggerProtocol):
    def log(self, ev: TraceEvent) -> None:
        ev.seq = _seq_counter[ev.session_id] = _seq_counter[ev.session_id] + 1
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO TraceLog
                    (timestamp, session_id, span_id, parent_span_id, seq, func,
                     wall_ms, cpu_pct_start, cpu_pct_end, error)
                    VALUES (:ts, :sid, :span, :parent, :seq, :func,
                            :wall, :cpu0, :cpu1, :err)
                    """
                ),
                {
                    "ts": ev.timestamp.isoformat(timespec="milliseconds"),
                    "sid": ev.session_id,
                    "span": ev.span_id,
                    "parent": ev.parent_span_id,
                    "seq": ev.seq,
                    "func": ev.func,
                    "wall": ev.wall_ms,
                    "cpu0": ev.cpu_pct_start,
                    "cpu1": ev.cpu_pct_end,
                    "err": ev.error,
                },
            )
