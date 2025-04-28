import json
import os
from datetime import datetime

from uikitxv2.db.models import TraceLog
from uikitxv2.db.session import _DB_ENV, SQLiteLogger, get_session


def test_logger_roundtrip(tmp_path):
    os.environ[_DB_ENV] = str(tmp_path / "test.db")
    logger = SQLiteLogger()

    # Pass the data as a dict - SQLiteLogger should handle JSON conversion
    test_data = {"foo": 1}
    logger.write("perf", "unit_test", test_data, duration_ms=12.3, ts=datetime(2025, 1, 1))

    with get_session() as s:
        rec = s.query(TraceLog).one()
        assert rec.name == "unit_test"
        assert rec.duration_ms == 12.3
        # The payload is loaded from JSON, so we need to access it properly
        payload = rec.payload_json if isinstance(rec.payload_json, dict) else json.loads(rec.payload_json)
        assert payload["foo"] == 1
