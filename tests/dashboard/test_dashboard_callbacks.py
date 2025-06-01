from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

from _pytest.monkeypatch import MonkeyPatch

from apps.dashboards.main.app import app as dash_module

dashboard_mod = cast(Any, dash_module)


def test_update_option_blocks_valid() -> None:
    """Updating option blocks with numeric input shows correct fields."""
    children = dashboard_mod.update_option_blocks("2")
    assert len(children) == 3
    assert children[0].style["display"] == "block"
    assert children[1].style["display"] == "block"
    assert children[2].style["display"] == "none"


def test_update_option_blocks_invalid() -> None:
    """Invalid input hides all but the first option block."""
    children = dashboard_mod.update_option_blocks("foo")
    assert len(children) == 3
    assert [c.style["display"] for c in children] == ["block", "none", "none"]


def test_refresh_log_data(monkeypatch: MonkeyPatch) -> None:
    """Refresh log data returns latest flow and performance entries."""
    flow = [{"id": 1}]
    perf = [{"fn": "a"}]

    monkeypatch.setattr(dashboard_mod, "query_flow_trace_logs", lambda limit=100: flow)
    monkeypatch.setattr(dashboard_mod, "query_performance_metrics", lambda: perf)

    out_flow, out_perf = dashboard_mod.refresh_log_data(1)
    assert out_flow == flow
    assert out_perf == perf


class DummyCtx(SimpleNamespace):
    pass


def test_toggle_logs_tables_performance() -> None:
    """Clicking performance toggle shows performance table."""
    ctx = DummyCtx(triggered=[{"prop_id": "logs-toggle-performance.n_clicks"}])
    with patch.object(dashboard_mod.dash, "callback_context", ctx):
        flow_style, perf_style, flow_btn, perf_btn = dashboard_mod.toggle_logs_tables(1, 2)
    assert flow_style["display"] == "none"
    assert perf_style["display"] == "block"
    assert perf_btn["backgroundColor"] == dashboard_mod.default_theme.primary
    assert flow_btn["backgroundColor"] == dashboard_mod.default_theme.panel_bg


def test_toggle_logs_tables_default() -> None:
    """No toggle clicks defaults to flow trace view."""
    ctx = DummyCtx(triggered=[])
    with patch.object(dashboard_mod.dash, "callback_context", ctx):
        flow_style, perf_style, flow_btn, perf_btn = dashboard_mod.toggle_logs_tables(None, None)
    assert flow_style["display"] == "block"
    assert perf_style["display"] == "none"
    assert flow_btn["backgroundColor"] == dashboard_mod.default_theme.primary
    assert perf_btn["backgroundColor"] == dashboard_mod.default_theme.panel_bg
