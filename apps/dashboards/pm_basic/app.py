#!/usr/bin/env python3
"""
pm_scenario – Minimal Dash UI to run Pricing Monkey one-shot and display the DataFrame.

Uses wrapped UIKit components and invokes PMBasicRunner.collect_once().
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import importlib.util
import logging
import sys as _sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import time
import re
import pandas as pd

import dash
from dash import Input, Output, dcc, html, no_update
from datetime import datetime

from components import Button, Container, DataTable
from components.themes import default_theme

_runner_path = Path(__file__).parents[3] / "lib" / "trading" / "pricing_monkey" / "playwright_basic_runner.py"
spec = importlib.util.spec_from_file_location("pm_basic_runner", str(_runner_path))
if spec and spec.loader:
	_pm_mod = importlib.util.module_from_spec(spec)
	_sys.modules["pm_basic_runner"] = _pm_mod
	spec.loader.exec_module(_pm_mod)
	PMBasicRunner = getattr(_pm_mod, "PMBasicRunner")  # type: ignore[assignment]
	PMBasicSessionRunner = getattr(_pm_mod, "PMBasicSessionRunner")  # type: ignore[assignment]
else:
	from trading.pricing_monkey.playwright_basic_runner import PMBasicRunner  # type: ignore[import]
from trading.pricing_monkey.playwright_basic_runner import PMBasicSessionRunner  # type: ignore[import]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Elevate module logging to DEBUG with a dedicated handler for richer console output
if not logger.handlers:
	h = logging.StreamHandler()
	h.setLevel(logging.DEBUG)
	h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
	logger.addHandler(h)
	logger.setLevel(logging.DEBUG)
	logger.propagate = False
# Also increase verbosity of the PM runner logger if present
logging.getLogger("pm_playwright_basic").setLevel(logging.DEBUG)
try:
	_logs_dir = Path(__file__).parents[3] / "logs"
	_logs_dir.mkdir(parents=True, exist_ok=True)
	_file_handler = RotatingFileHandler(str(_logs_dir / "pm_basic_dash.log"), maxBytes=5_000_000, backupCount=3)
	_file_handler.setLevel(logging.DEBUG)
	_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
	logger.addHandler(_file_handler)
	logging.getLogger("pm_playwright_basic").addHandler(_file_handler)
except Exception:
	pass


def _df_to_table_props(df) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	if df is None or getattr(df, "empty", True):
		return [], []
	columns = [{"name": str(c), "id": str(c)} for c in df.columns]
	data = df.to_dict("records")
	return columns, data


app = dash.Dash(
	__name__,
	suppress_callback_exceptions=True,
	assets_folder=str(Path(__file__).parents[3] / "assets"),
)
app.title = "pm_scenario"


app.layout = Container(
	id="pm-basic-root",
	children=[
		html.H3("pm_scenario", style={"color": default_theme.primary}),
		Button(id="run-btn", label="Run Pricing Monkey"),
		html.Div(id="status", style={"marginTop": "10px", "color": default_theme.text_subtle}),
		html.Div(id="last-updated", style={"marginTop": "6px", "color": default_theme.text_subtle}),
		dcc.Interval(id="pm-tick", interval=1000, n_intervals=0, disabled=True),
		html.Div(id="pm-tables"),
	],
).render()


def _slice_by_option_headers(df) -> List[Tuple[str, Any]]:
	if df is None or getattr(df, "empty", True):
		return []
	option_rows: List[Tuple[int, str]] = []
	pat = re.compile(r"^\s*Option\s*(\d+)\s*$", re.IGNORECASE)
	for idx, row in df.iterrows():
		label: str | None = None
		for val in row.values:
			if isinstance(val, str):
				m = pat.match(val)
				if m:
					label = f"Option {m.group(1)}"
					break
		if label:
			option_rows.append((idx, label))
	if not option_rows:
		return [("All", df)]
	option_rows.append((len(df), "END"))
	slices: List[Tuple[str, Any]] = []
	for i in range(len(option_rows) - 1):
		start = option_rows[i][0] + 1
		end = option_rows[i + 1][0]
		label = option_rows[i][1]
		part = df.iloc[start:end].copy()
		slices.append((label, part))
	return slices


@app.callback(
	Output("pm-tables", "children"),
	Output("status", "children"),
	Output("last-updated", "children"),
	Output("pm-tick", "disabled"),
	Input("run-btn", "n_clicks"),
	Input("pm-tick", "n_intervals"),
	prevent_initial_call=True,
)
def run_and_display(n_clicks: int | None, n_intervals: int | None):
	try:
		status = "Running…"
		t0 = time.perf_counter()
		# Determine trigger
		trigger_id = None
		try:
			trigger_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
		except Exception:
			trigger_id = None
		logger.debug("Callback start | trigger=%s n_clicks=%s n_intervals=%s", trigger_id, n_clicks, n_intervals)
		# Start/reuse session runner; keep heavy Playwright work off the callback
		global _pm_session
		try:
			_pm_session
		except NameError:
			_pm_session = None  # type: ignore
		if _pm_session is None:
			_pm_session = PMBasicSessionRunner()
			logger.debug("Session created; starting background loop…")
			_pm_session.start_loop(interval_sec=1.0)
		# Fetch cached snapshot
		df, sig, updated = _pm_session.get_snapshot()
		if df is None or getattr(df, "empty", True):
			status = "Starting session… collecting first snapshot…"
			return no_update, status, no_update, (False if trigger_id == "run-btn" else no_update)
		slices = _slice_by_option_headers(df)
		logger.debug("slice_count=%d | slice_sizes=%s", len(slices), [len(p) for _, p in slices] if slices else [])

		# Build summary table:
		# - Drop display/excluded columns (also exclude Implied Vol (Daily BP))
		# - Do NOT sum: Underlying Shift, Underlying
		# - Sum all other numeric columns including Trade Amount
		excluded = {
			"Expiry Date",
			"Bloomberg",
			"Strike",
			"Bid",
			"Price",
			"Ask",
			"Trade Description",
			"Implied Vol (Daily BP)",
		}
		non_sum = {"Underlying Shift", "Underlying"}
		frames = [part for _, part in slices if part is not None and not getattr(part, "empty", True)]
		summary_df = pd.DataFrame()
		if frames:
			combined = pd.concat(frames, ignore_index=True)
			keep_cols = [c for c in combined.columns if c not in excluded]
			df2 = combined[keep_cols].copy()
			# Create numeric key for sorting/grouping on shift (positive first)
			if "Underlying Shift" in df2.columns:
				shift_series = pd.to_numeric(
					df2["Underlying Shift"].astype(str).str.replace(",", "").str.strip().str.replace("−", "-"),
					errors="coerce",
				)
				df2["__shift__"] = shift_series
			else:
				df2["__shift__"] = pd.RangeIndex(len(df2))
			# Normalize numeric columns for summation
			def _to_num(series: pd.Series) -> pd.Series:
				return pd.to_numeric(
					series.astype(str).str.replace(",", "").str.strip().str.replace("−", "-"),
					errors="coerce",
				).fillna(0)
			# Build aggregation dict
			agg: Dict[str, Any] = {}
			for col in df2.columns:
				if col == "__shift__":
					continue
				if col in non_sum:
					agg[col] = "first"
				else:
					agg[col] = (lambda s, _f=_to_num: _f(s).sum())
			g = df2.groupby("__shift__", dropna=False).agg(agg).reset_index(drop=False)
			# Sort with positive shifts first (descending)
			g = g.sort_values(by="__shift__", ascending=False, kind="stable").drop(columns=["__shift__"])
			# Reorder columns to original order (excluding excluded)
			preferred = [
				"Trade Amount",
				"Underlying Shift",
				"Underlying",
				"NPV",
				"scenario pnl",
				"DV01",
				"DV01 Gamma",
				"Theta",
				"Vega",
			]
			pref_order = [c for c in preferred if c in g.columns] + [c for c in g.columns if c not in preferred]
			summary_cols = [c for c in pref_order if c in g.columns]
			summary_df = g[summary_cols]
		children: List[Any] = []

		# Add summary section first if available
		if not summary_df.empty:
			children.append(html.H4("Summary", style={"color": default_theme.primary, "marginTop": "12px"}))
			children.append(
				DataTable(
					id="pm-summary",
					data=summary_df.to_dict("records"),
					columns=[{"name": str(c), "id": str(c)} for c in summary_df.columns],
					page_size=100,
					style_table={"overflowX": "auto"},
					style_cell={"fontFamily": "monospace", "fontSize": 12},
				).render()
			)
		total_rows = 0
		for i, (label, part) in enumerate(slices):
			total_rows += len(part)
			children.append(html.H4(label, style={"color": default_theme.primary, "marginTop": "12px"}))
			children.append(
				DataTable(
					id=f"pm-table-{i}",
					data=part.to_dict("records"),
					columns=[{"name": str(c), "id": str(c)} for c in part.columns],
					page_size=100,
					style_table={"overflowX": "auto"},
					style_cell={"fontFamily": "monospace", "fontSize": 12},
				).render()
			)
		status = f"Completed. Rows: {total_rows} Cols: {len(df.columns)} Slices: {len(slices)}"
		last_updated = f"Last updated: {datetime.fromtimestamp(updated).strftime('%H:%M:%S')}"
		# Enable interval only when triggered by run button; otherwise keep current state
		disable_flag = no_update
		if trigger_id == "run-btn":
			disable_flag = False
		logger.debug("Callback end | status='%s' last_updated='%s' interval_disabled=%s total_dt=%.3fs", status, last_updated, disable_flag, time.perf_counter() - t0)
		return children, status, last_updated, disable_flag
	except Exception as exc:
		logger.exception("pm_scenario run failed | trigger=%s n_clicks=%s n_intervals=%s", trigger_id if 'trigger_id' in locals() else None, n_clicks, n_intervals)
		# On error, keep interval state unchanged
		return no_update, f"Error: {exc}", no_update, no_update


# (Second callback removed by consolidation)
if __name__ == "__main__":
	app.run(debug=True, use_reloader=False, threaded=False)


