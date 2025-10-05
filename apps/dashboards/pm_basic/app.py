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
from decimal import Decimal, ROUND_HALF_UP
import threading
import time
import re
import pandas as pd

import dash
from dash import Input, Output, State, dcc, html, no_update
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

# Load writer by file path to avoid import issues
_writer_path = Path(__file__).parents[3] / "lib" / "trading" / "pricing_monkey" / "playwright_basic_writer.py"
spec_w = importlib.util.spec_from_file_location("pm_basic_writer", str(_writer_path))
if spec_w and spec_w.loader:
	_writer_mod = importlib.util.module_from_spec(spec_w)
	_sys.modules["pm_basic_writer"] = _writer_mod
	spec_w.loader.exec_module(_writer_mod)
	PMBasicWriter = getattr(_writer_mod, "PMBasicWriter")  # type: ignore[assignment]
else:
	from trading.pricing_monkey.playwright_basic_writer import PMBasicWriter  # type: ignore[import]

# Load Redis helper by file path (optional)
_redis_path = Path(__file__).parents[3] / "lib" / "trading" / "pricing_monkey" / "redis_io.py"
spec_r = importlib.util.spec_from_file_location("pm_redis_io", str(_redis_path))
if spec_r and spec_r.loader:
	_redis_mod = importlib.util.module_from_spec(spec_r)
	_sys.modules["pm_redis_io"] = _redis_mod
	spec_r.loader.exec_module(_redis_mod)
	pm_redis_publish = getattr(_redis_mod, "publish")  # type: ignore[assignment]
else:
	pm_redis_publish = None  # type: ignore[assignment]


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
		Button(id="run-btn", label="Run Pricing Monkey").render(),
		html.Div(id="status", style={"marginTop": "10px", "color": default_theme.text_subtle}),
		html.Div(id="last-updated", style={"marginTop": "6px", "color": default_theme.text_subtle}),
		dcc.Interval(id="pm-tick", interval=1000, n_intervals=0, disabled=True),
		# Mock writer inputs (Options 1-6)
		html.H4("Mock write to PM", style={"color": default_theme.primary, "marginTop": "14px"}),
		html.Div(
			[
				html.Div(
					[
						html.Span("Option 1", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-1", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-1", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				html.Div(
					[
						html.Span("Option 2", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-2", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-2", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				html.Div(
					[
						html.Span("Option 3", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-3", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-3", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				html.Div(
					[
						html.Span("Option 4", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-4", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-4", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				html.Div(
					[
						html.Span("Option 5", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-5", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-5", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				html.Div(
					[
						html.Span("Option 6", style={"display": "inline-block", "width": 80}),
						dcc.Input(id="opt-desc-6", placeholder="description (PM syntax)", style={"width": 360}),
						dcc.Input(id="opt-qty-6", placeholder="qty", style={"width": 100, "marginLeft": 8}),
					],
					style={"marginTop": 6},
				),
				Button(id="write-btn", label="Write to PM", style={"marginTop": 10}).render(),
				html.Div(id="write-status", style={"marginTop": 6, "color": default_theme.text_subtle}),
			]
		),
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
	# Diagnostic: log slice boundaries and sizes
	try:
		_bounds = []
		for i in range(len(option_rows) - 1):
			_start = option_rows[i][0] + 1
			_end = option_rows[i + 1][0]
			_bounds.append((option_rows[i][1], _start, _end, max(0, _end - _start)))
		logger.debug("slice_bounds=%s", _bounds)
	except Exception:
		pass
	for i in range(len(option_rows) - 1):
		start = option_rows[i][0] + 1
		end = option_rows[i + 1][0]
		label = option_rows[i][1]
		part = df.iloc[start:end].copy()
		# Diagnostic: peek underlying shift head/tail per slice
		try:
			if "Underlying Shift" in part.columns:
				us_head = list(part["Underlying Shift"].head(2))
				us_tail = list(part["Underlying Shift"].tail(2))
				logger.debug("slice %s | size=%d | us_head=%s | us_tail=%s", label, len(part), us_head, us_tail)
		except Exception:
			pass
		# Diagnostic: duplicate shifts in this slice
		try:
			if "Underlying Shift" in part.columns:
				_dup_mask = part.duplicated(subset=["Underlying Shift"], keep=False)
				_dup_counts = part.loc[_dup_mask, "Underlying Shift"].value_counts().to_dict()
				if _dup_counts:
					logger.debug("slice %s duplicate shifts -> %s", label, _dup_counts)
		except Exception:
			pass
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
		# Only create/start reader session when user explicitly clicks Run
		if _pm_session is None:
			if trigger_id != "run-btn":
				status = "Idle. Click 'Run Pricing Monkey' to start the reader."
				return no_update, status, no_update, no_update
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
			# Diagnostic: check potential duplicates before aggregation
			try:
				dup_cols = [c for c in ["Underlying Shift", "Underlying", "Trade Amount"] if c in combined.columns]
				if dup_cols:
					dups = combined.duplicated(subset=dup_cols, keep=False)
					dup_sample = combined.loc[dups, dup_cols].head(10).to_dict("records")
					logger.debug("pre-agg duplicates (first 5) on %s -> count=%d sample=%s", dup_cols, int(dups.sum()), dup_sample[:5])
			except Exception:
				pass
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
			# Financial-safe sum for scenario pnl using Decimal with 2dp HALF_UP
			def _sum_decimal_2dp(series: pd.Series) -> str:
				total = Decimal("0")
				for v in series:
					txt = str(v)
					txt = txt.replace(",", "").strip().replace("−", "-")
					try:
						d = Decimal(txt)
					except Exception:
						d = Decimal("0")
					total += d
				return str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
			# Build aggregation dict
			agg: Dict[str, Any] = {}
			for col in df2.columns:
				if col == "__shift__":
					continue
				if col in non_sum:
					agg[col] = "first"
				else:
					if col == "scenario pnl":
						agg[col] = _sum_decimal_2dp
					else:
						agg[col] = (lambda s, _f=_to_num: _f(s).sum())
			g = df2.groupby("__shift__", dropna=False).agg(agg).reset_index(drop=False)
			# Diagnostic: log per-shift Trade Amount totals to spot anomalies
			try:
				if "Trade Amount" in g.columns:
					logger.debug("trade_amount_by_shift=%s", dict(zip(df2["__shift__"], _to_num(df2["Trade Amount"]).groupby(df2["__shift__"]).sum())))
			except Exception:
				pass
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
			# Build display-only formatted summary (thousand separators) and keep Underlying Shift numeric
			summary_display_df = summary_df.copy()
			def _fmt_commas_2dp(val: Any) -> Any:
				try:
					if val is None:
						return val
					s = str(val).replace(",", "").replace("−", "-").strip()
					if s == "":
						return val
					# Use Decimal for rounding, then format with thousands separators
					q = Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
					return format(q, ",.2f")
				except Exception:
					return val
			# Ensure Underlying Shift stays numeric for filter_query styling
			if "Underlying Shift" in summary_display_df.columns:
				summary_display_df["Underlying Shift"] = pd.to_numeric(
					summary_display_df["Underlying Shift"].astype(str).str.replace(",", "").str.strip().str.replace("−", "-"),
					errors="coerce",
				)
			# Apply formatting to other columns only (display layer)
			for _col in summary_display_df.columns:
				if _col == "Underlying Shift":
					continue
				summary_display_df[_col] = summary_display_df[_col].apply(_fmt_commas_2dp)
		children: List[Any] = []

		# Add summary section first if available
		if not summary_df.empty:
			children.append(html.H4("Summary", style={"color": default_theme.primary, "marginTop": "12px"}))
			children.append(
				html.Div(
					"Note: 'scenario pnl' is summed using Decimal with 2-decimal ROUND_HALF_UP.",
					style={"color": default_theme.text_subtle, "fontSize": 12, "marginBottom": 6},
				)
			)
			children.append(
				DataTable(
					id="pm-summary",
					data=summary_display_df.to_dict("records"),
					columns=[{"name": str(c), "id": str(c)} for c in summary_display_df.columns],
					page_size=100,
					style_table={"overflowX": "auto"},
					style_cell={"fontFamily": "monospace", "fontSize": 12},
					style_data_conditional=[
						{
							"if": {"filter_query": "{Underlying Shift} = 0"},
							"borderTop": "2px solid #888",
							"borderBottom": "2px solid #888",
						}
					],
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
# Mock write callback (UI only wiring; session enqueue if available)
@app.callback(
	Output("write-status", "children"),
	Input("write-btn", "n_clicks"),
	State("opt-desc-1", "value"), State("opt-qty-1", "value"),
	State("opt-desc-2", "value"), State("opt-qty-2", "value"),
	State("opt-desc-3", "value"), State("opt-qty-3", "value"),
	State("opt-desc-4", "value"), State("opt-qty-4", "value"),
	State("opt-desc-5", "value"), State("opt-qty-5", "value"),
	State("opt-desc-6", "value"), State("opt-qty-6", "value"),
	prevent_initial_call=True,
)
def handle_write(n_clicks, d1, q1, d2, q2, d3, q3, d4, q4, d5, q5, d6, q6):
	rows = [20, 54, 88, 122, 156, 190]
	descs = [d1, d2, d3, d4, d5, d6]
	qtys = [q1, q2, q3, q4, q5, q6]
	# Build items for all rows; blanks become None → session will clear those cells
	items = []
	for idx, (desc, qty) in enumerate(zip(descs, qtys), start=1):
		val_desc = None if (desc is None or str(desc).strip() == "") else str(desc).strip()
		val_qty = None if (qty is None or str(qty).strip() == "") else str(qty).strip()
		items.append({"option": idx, "row": rows[idx-1], "desc": val_desc, "qty": val_qty})
	# Attempt to enqueue to session if writer API exists
	global _pm_session
	try:
		_pm_session
	except NameError:
		_pm_session = None  # type: ignore
	# Enqueue write into the running reader session (single-tab control)
	if _pm_session is None:
		return "Reader session is not running. Click 'Run Pricing Monkey' first."
	try:
		_pm_session.enqueue_write(items)  # type: ignore[attr-defined]
	except Exception as exc:
		return f"Failed to queue write: {exc}"
	# Optionally publish to Redis immediately for external listeners (the reader won't reload on it)
	try:
		if pm_redis_publish is not None:
			from datetime import datetime
			try:
				from zoneinfo import ZoneInfo
			except Exception:
				ZoneInfo = None  # type: ignore
			if ZoneInfo is not None:
				chi = datetime.now(ZoneInfo("America/Chicago"))
				ts = chi.isoformat(timespec="seconds")
			else:
				ts = datetime.now().isoformat(timespec="seconds")
			payload = {"timestamp_chi": ts, "items": [{"row": it["row"], "desc": it["desc"], "qty": it["qty"]} for it in items]}
			pm_redis_publish("pm:sheet_changed", payload)
	except Exception:
		pass
	return f"Queued {len(items)} item(s) for write."


# (Second callback removed by consolidation)
if __name__ == "__main__":
	app.run(debug=True, use_reloader=False, threaded=False)


