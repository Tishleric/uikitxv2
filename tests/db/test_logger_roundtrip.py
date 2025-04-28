import json
import os
from datetime import datetime

import sqlalchemy as sa

from uikitxv2.core.trace_event import TraceEvent  # NEW
from uikitxv2.db.models import TraceLog
from uikitxv2.db.session import _DB_ENV, get_session, get_engine
from uikitxv2.db.sqlite_logger import SQLiteLogger

def test_logger_roundtrip(tmp_path):
    logger = SQLiteLogger()

    ev = TraceEvent(
        timestamp=datetime(2025, 1, 1),
        session_id="t123",
        span_id="s1", 
        parent_span_id=None,
        seq=0,
        func="unit_test",
        wall_ms=12.3,
        details={"foo": 1},
    )
    logger.log(ev)

    with get_session() as s:
        rec = s.query(TraceLog).one()
        assert rec.name == "unit_test"
        assert rec.duration_ms == 12.3
        payload = rec.payload_json
        if not isinstance(payload, dict):            # safety for future drivers
            payload = json.loads(payload)
        assert payload["foo"] == 1
