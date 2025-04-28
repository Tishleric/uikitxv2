# src/uikitxv2/decorators/trace_cpu.py
from __future__ import annotations

import time
from typing import Any

import psutil

from uikitxv2.core.base_decorator import BaseDecorator
from uikitxv2.core.trace_event import TraceEvent


class trace_cpu(BaseDecorator):  # noqa: N801  (decorator style)
    def _collect(self, fn, ev: TraceEvent, *a: Any, **k: Any):
        cpu_start = psutil.cpu_percent(interval=None)
        t0 = time.perf_counter()
        result = fn(*a, **k)
        ev.wall_ms = (time.perf_counter() - t0) * 1000
        ev.cpu_pct_start = cpu_start
        ev.cpu_pct_end = psutil.cpu_percent(interval=None)
        return result
