import sqlalchemy as sa

from uikitxv2.db.session import get_engine
from uikitxv2.decorators.trace_cpu import trace_cpu


@trace_cpu()
def add(x, y):
    return x + y

def test_trace_cpu_persists():
    assert add(1, 2) == 3
    assert add(2, 3) == 5

    eng = get_engine()
    rows = list(eng.execute(sa.text("SELECT seq, wall_ms FROM TraceLog")))
    assert len(rows) == 2
    assert rows[1].seq == 2
    assert rows[0].wall_ms > 0
