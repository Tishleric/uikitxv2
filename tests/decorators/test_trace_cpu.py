import os
import tempfile

import sqlalchemy as sa
from contextlib import closing

from uikitxv2.core.logger_protocol import set_logger
from uikitxv2.db.sqlite_logger import SQLiteLogger
from uikitxv2.decorators.trace_cpu import trace_cpu

# bootstrap temp DB
_fd, db_path = tempfile.mkstemp()
os.close(_fd)
os.environ["UIKITX_DB_PATH"] = db_path
engine = sa.create_engine(f"sqlite:///{db_path}")
with engine.begin() as conn:                                      # create schema
    conn.execute(
        sa.text(open("src/uikitxv2/db/migrations/0001_trace_log.sql").read())
    )
set_logger(SQLiteLogger())

@trace_cpu()
def add(a, b):
    return a + b

def test_trace_cpu_row():
    assert add(2, 3) == 5
    with engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT wall_ms, cpu_pct_start FROM TraceLog")
        ).one()
    assert row.wall_ms > 0
    assert row.cpu_pct_start is not None
