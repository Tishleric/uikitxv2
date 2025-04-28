import sqlalchemy as sa
from uikitxv2.db.session import get_engine

from uikitxv2.core.logger_protocol import set_logger
from uikitxv2.db.sqlite_logger import SQLiteLogger
from uikitxv2.decorators.trace_cpu import trace_cpu

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _prepare_logger() -> None:
    """Install a fresh SQLiteLogger that targets the same engine
    created by get_engine() inside the fixtures."""
    set_logger(SQLiteLogger())


# -----------------------------------------------------------------------------
# Function under test
# -----------------------------------------------------------------------------
@trace_cpu()
def add(a: int, b: int) -> int:
    return a + b


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_trace_cpu_row() -> None:
    _prepare_logger()
    engine = get_engine()

    # call
    assert add(2, 3) == 5

    # verify one row written
    with engine.connect() as conn:
        duration, payload = conn.execute(
            sa.text("SELECT duration_ms, payload_json FROM trace_log")
        ).one()

    assert duration > 0
    assert payload is not None  # JSON string (“{}”) for this simple call


def test_trace_cpu_persists() -> None:
    """Sanity-check that multiple calls append multiple rows."""
    _prepare_logger()
    engine = get_engine()

    add(1, 2)
    add(2, 3)

    with engine.connect() as conn:
        (cnt,) = conn.execute(
            sa.text("SELECT COUNT(*) FROM trace_log")
        ).one()

    assert cnt >= 2
