import sqlalchemy as sa

from uikitxv2.decorators.trace_cpu import trace_cpu
from uikitxv2.db.session import get_engine
from uikitxv2.core.logger_protocol import set_logger
from uikitxv2.db.sqlite_logger import SQLiteLogger


# -----------------------------------------------------------------------------
# Function under test
# -----------------------------------------------------------------------------
@trace_cpu()
def add(x: int, y: int) -> int:
    return x + y


# -----------------------------------------------------------------------------
# Integration test: decorator logs survive across calls
# -----------------------------------------------------------------------------
def test_trace_cpu_persists() -> None:
    # logger must point to the same engine the fixtures created
    set_logger(SQLiteLogger())
    engine = get_engine()

    # two calls → two rows expected
    assert add(1, 2) == 3
    assert add(2, 3) == 5

    with engine.connect() as conn:
        rows = list(conn.execute(sa.text("SELECT duration_ms FROM trace_log")))
    assert len(rows) == 2
    # each entry should have a positive duration
    assert all(r.duration_ms > 0 for r in rows)
