import os
import sys
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import plotly.express as px

# --- Path setup to enable wrapped components (matches other apps) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
lib_path = os.path.join(project_root, 'lib')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from components.basic.radiobutton import RadioButton
from components.basic.loading import Loading
from components.basic.heatmap import Heatmap
from components.themes.colour_palette import default_theme
from components.themes import get_graph_figure_layout_defaults
from components import Container, Grid, Graph
from components.advanced.datatable import DataTable


def _load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
DATA_DIR = os.path.join(BASE_PATH, "data", "output", "accuracy_validation")
REPORT_PATH = os.path.join(BASE_PATH, "reports", "accuracy_frontier", "README.md")

# Convert business years to hours (252 biz days × 24 hours)
HOURS_PER_YEAR = 24.0 * 252.0
DV01_THRESHOLD = 0.0625  # 0.1% of 62.5

df_thresh = _load_csv(os.path.join(DATA_DIR, "threshold_sweep.csv"))
df_vt_sweep = _load_csv(os.path.join(DATA_DIR, "vtexp_threshold_sweep.csv"))
df_mny_sweep = _load_csv(os.path.join(DATA_DIR, "moneyness_threshold_sweep.csv"))
df_thresh_flt = _load_csv(os.path.join(DATA_DIR, "threshold_sweep_flt.csv"))
df_vt_sweep_flt = _load_csv(os.path.join(DATA_DIR, "vtexp_threshold_sweep_flt.csv"))
df_mny_sweep_flt = _load_csv(os.path.join(DATA_DIR, "moneyness_threshold_sweep_flt.csv"))
df_summary = _load_csv(os.path.join(DATA_DIR, "summary_success_by_bins.csv"))
df_summary_flt = _load_csv(os.path.join(DATA_DIR, "summary_success_by_bins_flt.csv"))
df_dotm = _load_csv(os.path.join(DATA_DIR, "dotm_epsilon.csv"))
df_inflect = _load_csv(os.path.join(DATA_DIR, "inflection_candidates.csv"))
df_manifest = _load_csv(os.path.join(DATA_DIR, "clean_manifest.csv"))

# 7–8am dataset (Calls-only) outputs
DATA_DIR_78 = os.path.join(BASE_PATH, "data", "output", "accuracy_validation_7to8")
DATA_DIR_78_15 = os.path.join(BASE_PATH, "data", "output", "accuracy_validation_7to8_15m")
DATA_DIR_78_30 = os.path.join(BASE_PATH, "data", "output", "accuracy_validation_7to8_30m")
df_thresh_78 = _load_csv(os.path.join(DATA_DIR_78, "threshold_sweep.csv"))
df_vt_sweep_78 = _load_csv(os.path.join(DATA_DIR_78, "vtexp_threshold_sweep.csv"))
df_mny_sweep_78 = _load_csv(os.path.join(DATA_DIR_78, "moneyness_threshold_sweep.csv"))
df_thresh_flt_78 = _load_csv(os.path.join(DATA_DIR_78, "threshold_sweep_flt.csv"))
df_vt_sweep_flt_78 = _load_csv(os.path.join(DATA_DIR_78, "vtexp_threshold_sweep_flt.csv"))
df_mny_sweep_flt_78 = _load_csv(os.path.join(DATA_DIR_78, "moneyness_threshold_sweep_flt.csv"))
df_summary_78 = _load_csv(os.path.join(DATA_DIR_78, "summary_success_by_bins.csv"))
df_summary_flt_78 = _load_csv(os.path.join(DATA_DIR_78, "summary_success_by_bins_flt.csv"))
df_manifest_78 = _load_csv(os.path.join(DATA_DIR_78, "clean_manifest.csv"))

# 7–8am interval variants
data78 = {
    5: {
        "df_thresh": _load_csv(os.path.join(DATA_DIR_78, "threshold_sweep.csv")),
        "df_vt": _load_csv(os.path.join(DATA_DIR_78, "vtexp_threshold_sweep.csv")),
        "df_mny": _load_csv(os.path.join(DATA_DIR_78, "moneyness_threshold_sweep.csv")),
        "df_thresh_flt": _load_csv(os.path.join(DATA_DIR_78, "threshold_sweep_flt.csv")),
        "df_vt_flt": _load_csv(os.path.join(DATA_DIR_78, "vtexp_threshold_sweep_flt.csv")),
        "df_mny_flt": _load_csv(os.path.join(DATA_DIR_78, "moneyness_threshold_sweep_flt.csv")),
        "df_summary": _load_csv(os.path.join(DATA_DIR_78, "summary_success_by_bins.csv")),
        "df_summary_flt": _load_csv(os.path.join(DATA_DIR_78, "summary_success_by_bins_flt.csv")),
        "df_manifest": _load_csv(os.path.join(DATA_DIR_78, "clean_manifest.csv")),
    },
    15: {
        "df_thresh": _load_csv(os.path.join(DATA_DIR_78_15, "threshold_sweep.csv")),
        "df_vt": _load_csv(os.path.join(DATA_DIR_78_15, "vtexp_threshold_sweep.csv")),
        "df_mny": _load_csv(os.path.join(DATA_DIR_78_15, "moneyness_threshold_sweep.csv")),
        "df_thresh_flt": _load_csv(os.path.join(DATA_DIR_78_15, "threshold_sweep_flt.csv")),
        "df_vt_flt": _load_csv(os.path.join(DATA_DIR_78_15, "vtexp_threshold_sweep_flt.csv")),
        "df_mny_flt": _load_csv(os.path.join(DATA_DIR_78_15, "moneyness_threshold_sweep_flt.csv")),
        "df_summary": _load_csv(os.path.join(DATA_DIR_78_15, "summary_success_by_bins.csv")),
        "df_summary_flt": _load_csv(os.path.join(DATA_DIR_78_15, "summary_success_by_bins_flt.csv")),
        "df_manifest": _load_csv(os.path.join(DATA_DIR_78_15, "clean_manifest.csv")),
    },
    30: {
        "df_thresh": _load_csv(os.path.join(DATA_DIR_78_30, "threshold_sweep.csv")),
        "df_vt": _load_csv(os.path.join(DATA_DIR_78_30, "vtexp_threshold_sweep.csv")),
        "df_mny": _load_csv(os.path.join(DATA_DIR_78_30, "moneyness_threshold_sweep.csv")),
        "df_thresh_flt": _load_csv(os.path.join(DATA_DIR_78_30, "threshold_sweep_flt.csv")),
        "df_vt_flt": _load_csv(os.path.join(DATA_DIR_78_30, "vtexp_threshold_sweep_flt.csv")),
        "df_mny_flt": _load_csv(os.path.join(DATA_DIR_78_30, "moneyness_threshold_sweep_flt.csv")),
        "df_summary": _load_csv(os.path.join(DATA_DIR_78_30, "summary_success_by_bins.csv")),
        "df_summary_flt": _load_csv(os.path.join(DATA_DIR_78_30, "summary_success_by_bins_flt.csv")),
        "df_manifest": _load_csv(os.path.join(DATA_DIR_78_30, "clean_manifest.csv")),
    },
}

initial_count = drop_count = kept_count = None
if not df_manifest.empty and "keep" in df_manifest.columns:
    drop_count = int((df_manifest["keep"] == False).sum())
    kept_count = int((df_manifest["keep"] == True).sum())
    initial_count = drop_count + kept_count
elif (not df_summary.empty) and ("total_count" in df_summary.columns):
    kept_count = int(df_summary["total_count"].sum())
    initial_count = kept_count

rec_thresh = None
if not df_inflect.empty:
    row = df_inflect[df_inflect["category"] == "All"]
    if not row.empty:
        val = row["threshold_for_95pct"].iloc[0]
        if pd.notna(val):
            rec_thresh = float(val)

# Build a summary string for the recommended threshold (displayed above the chart)
rec_summary_text = ""
if rec_thresh is not None and not df_thresh.empty:
    _row = df_thresh[df_thresh["threshold"] == rec_thresh]
    if not _row.empty:
        _succ = float(_row.get("success_hi", pd.Series([None])).iloc[0]) if "success_hi" in _row.columns else None
        _cnt = int(_row.get("count_hi", pd.Series([0])).iloc[0]) if "count_hi" in _row.columns else None
        rec_summary_text = (
            f"Recommended AdjTheor threshold: {rec_thresh:.6f} — smallest threshold with Success ≥ 95% "
            f"(criterion: |error_2nd_order| ≤ 5 percentage points on rows with AdjTheor ≥ threshold). "
            f"Sample size at threshold: {_cnt if _cnt is not None else 'N/A'}."
        )


def _threshold_figure() -> "px.Figure":
    if df_thresh.empty or "threshold" not in df_thresh.columns:
        return px.line()
    # Single decision curve: success when rows with AdjTheor ≤ threshold are filtered out
    # Use success_hi from the sweep as "filtered success"
    have_otm = "success_hi_otm" in df_thresh.columns
    base = df_thresh[["threshold", "success_hi"]].copy()
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_thresh["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "AdjTheor Threshold", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="AdjTheor ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    # Auto-fit Y with headroom to 1.0
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    return fig


def _threshold_figure_from(df_thresh_any: pd.DataFrame) -> "px.Figure":
    if df_thresh_any.empty or "threshold" not in df_thresh_any.columns:
        return px.line()
    have_otm = "success_hi_otm" in df_thresh_any.columns
    base = df_thresh_any[["threshold", "success_hi"]].copy()
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_thresh_any["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "AdjTheor Threshold", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="AdjTheor ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    return fig


def _vtexp_threshold_figure_from(df_vt_any: pd.DataFrame) -> "px.Figure":
    if df_vt_any.empty or "vtexp_threshold" not in df_vt_any.columns:
        return px.line()
    have_otm = "success_hi_otm" in df_vt_any.columns
    base = df_vt_any[["vtexp_threshold", "success_hi"]].copy()
    base["threshold"] = base["vtexp_threshold"] * HOURS_PER_YEAR
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_vt_any["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "vtexp Threshold (hours)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="vtexp ≥ %{x:.1f}h<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _moneyness_threshold_figure_from(df_mny_any: pd.DataFrame) -> "px.Figure":
    if df_mny_any.empty or "moneyness_threshold" not in df_mny_any.columns:
        return px.line()
    have_otm = "success_hi_otm" in df_mny_any.columns
    base = df_mny_any[["moneyness_threshold", "success_hi"]].copy()
    base.rename(columns={"moneyness_threshold": "threshold", "success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_mny_any["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "moneyness Threshold (F−K)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="moneyness ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _threshold_figure_flt_78() -> "px.Figure":
    df = df_thresh_flt_78
    if df.empty or "threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["threshold", "success_hi"]].copy()
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "AdjTheor Threshold", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="AdjTheor ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    return fig


def _vtexp_threshold_figure_flt_78() -> "px.Figure":
    df = df_vt_sweep_flt_78
    if df.empty or "vtexp_threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["vtexp_threshold", "success_hi"]].copy()
    base["threshold"] = base["vtexp_threshold"] * HOURS_PER_YEAR
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "vtexp Threshold (hours)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="vtexp ≥ %{x:.1f}h<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _moneyness_threshold_figure_flt_78() -> "px.Figure":
    df = df_mny_sweep_flt_78
    if df.empty or "moneyness_threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["moneyness_threshold", "success_hi"]].copy()
    base.rename(columns={"moneyness_threshold": "threshold", "success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "moneyness Threshold (F−K)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="moneyness ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _vtexp_threshold_figure() -> "px.Figure":
    if df_vt_sweep.empty or "vtexp_threshold" not in df_vt_sweep.columns:
        return px.line()
    have_otm = "success_hi_otm" in df_vt_sweep.columns
    base = df_vt_sweep[["vtexp_threshold", "success_hi"]].copy()
    base["threshold"] = base["vtexp_threshold"] * HOURS_PER_YEAR
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_vt_sweep["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "vtexp Threshold (hours)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="vtexp ≥ %{x:.1f}h<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    # Auto-fit Y with headroom
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _moneyness_threshold_figure() -> "px.Figure":
    if df_mny_sweep.empty or "moneyness_threshold" not in df_mny_sweep.columns:
        return px.line()
    have_otm = "success_hi_otm" in df_mny_sweep.columns
    base = df_mny_sweep[["moneyness_threshold", "success_hi"]].copy()
    base.rename(columns={"moneyness_threshold": "threshold", "success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df_mny_sweep["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "moneyness Threshold (F−K)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="moneyness ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


# Filtered figure builders (use _flt CSVs)
def _threshold_figure_flt() -> "px.Figure":
    df = df_thresh_flt
    if df.empty or "threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["threshold", "success_hi"]].copy()
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "AdjTheor Threshold", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="AdjTheor ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    return fig


def _vtexp_threshold_figure_flt() -> "px.Figure":
    df = df_vt_sweep_flt
    if df.empty or "vtexp_threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["vtexp_threshold", "success_hi"]].copy()
    base["threshold"] = base["vtexp_threshold"] * HOURS_PER_YEAR
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "vtexp Threshold (hours)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="vtexp ≥ %{x:.1f}h<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig


def _moneyness_threshold_figure_flt() -> "px.Figure":
    df = df_mny_sweep_flt
    if df.empty or "moneyness_threshold" not in df.columns:
        return px.line()
    have_otm = "success_hi_otm" in df.columns
    base = df[["moneyness_threshold", "success_hi"]].copy()
    base.rename(columns={"moneyness_threshold": "threshold", "success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = df["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "moneyness Threshold (F−K)", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="moneyness ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    return fig
# Helpers for summary lines above charts
def _first_crossing(df: pd.DataFrame, xcol: str, ycol: str, target: float = 0.95) -> float | None:
    try:
        sub = df[[xcol, ycol]].dropna().sort_values(xcol)
        hit = sub[sub[ycol] >= target]
        if not hit.empty:
            return float(hit.iloc[0][xcol])
    except Exception:
        return None
    return None


def _fmt_vtexp(v: float | None) -> str:
    if v is None:
        return "N/A"
    days = v * 252.0
    hours = days * 24.0
    return f"{v:.6f} years (~{days:.3f} biz days, ~{hours:.1f} hours)"

def _fmt_vtexp_hours(v: float | None) -> str:
    if v is None:
        return "N/A"
    return f"{v * HOURS_PER_YEAR:.1f}h"
def _dotm_figure() -> "px.Figure":
    if df_dotm.empty:
        return px.line()
    long = df_dotm.melt(id_vars="epsilon", var_name="moneyness_cutoff", value_name="success_rate")
    fig = px.line(
        long,
        x="epsilon",
        y="success_rate",
        color="moneyness_cutoff",
        markers=True,
        labels={"epsilon": "Epsilon (price ticks)", "success_rate": "Success Rate"},
        title="DOTM Success vs ε",
    )
    fig.update_layout(yaxis=dict(range=[0, 1]))
    return fig


def _frontier_heatmap(dataframe: pd.DataFrame, title: str) -> "px.Figure":
    if dataframe.empty:
        return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"})
    df_plot = dataframe.copy()
    # Ensure unique pairs by aggregating counts where available
    if {"success_count", "total_count"}.issubset(df_plot.columns):
        agg_df = (
            df_plot.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)
            .agg({"success_count": "sum", "total_count": "sum"})
            .reset_index()
        )
        agg_df["success_rate"] = agg_df["success_count"] / agg_df["total_count"].replace({0: pd.NA})
    else:
        # Fallback: average success_rate per cell
        agg_df = (
            df_plot.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)["success_rate"]
            .mean()
            .reset_index()
        )
    pivot = agg_df.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
    # Order vtexp by our finer labels, and moneyness by the known label list
    vte_labels = [
        "<0.00025",
        "0.00025-0.0005",
        "0.0005-0.001",
        "0.001-0.002",
        "0.002-0.005",
        "0.005-0.01",
        "0.01-0.02",
        "0.02-0.05",
        ">=0.05",
    ]
    mon_labels = [
        "(-5,-2]",
        "(-2,-1]",
        "(-1,-0.5]",
        "(-0.5,-0.25]",
        "(-0.25,-0.125]",
        "(-0.125,-0.0625]",
        "(-0.0625,-0.015625]",
        "(-0.015625,0]",
        "(0,0.015625]",
        "(0.015625,0.05]",
        "(0.05,0.125]",
        "(>0.125)",
    ]
    pivot = pivot.reindex(index=vte_labels)
    pivot = pivot.reindex(columns=[c for c in mon_labels if c in pivot.columns])
    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        color_continuous_scale="RdYlGn",
        aspect="auto",
        labels={
            "x": "Distance from strike (F−K, price points)",
            "y": "Time to expiry (years, binned)",
            "color": "Success rate",
        },
        title=title,
    )
    fig.update_layout(
        yaxis=dict(dtick=1),
        paper_bgcolor=default_theme.base_bg,
        plot_bgcolor=default_theme.base_bg,
        font=dict(color=default_theme.text_light),
    )
    fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
    return fig
def _load_findings_markdown() -> str:
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "*Error loading findings report.*"
    return "*No findings report found at reports/accuracy_frontier/README.md.*"
def _parse_mon_label_to_range(lbl: str) -> tuple[float, float]:
    try:
        s = str(lbl)
        if s.startswith("(>") and s.endswith(")"):
            v = float(s[2:-1])
            return v, float("inf")
        if s.startswith("(") and s.endswith("]") and "," in s:
            a, b = s[1:-1].split(",", 1)
            return float(a), float(b)
        if s in ("nan", "None"):
            return -float("inf"), float("inf")
    except Exception:
        pass
    return -float("inf"), float("inf")


def _parse_hours_label_to_years_range(lbl: str) -> tuple[float, float]:
    try:
        s = str(lbl)
        if s.startswith("<") and s.endswith("h"):
            v_h = float(s[1:-1])
            return 0.0, v_h / HOURS_PER_YEAR
        if s.startswith(">=") and s.endswith("h"):
            v_h = float(s[2:-1])
            return v_h / HOURS_PER_YEAR, float("inf")
        if "-" in s and s.endswith("h"):
            a, b_h = s.split("-", 1)
            a_h = float(a)
            b_h = float(b_h[:-1])
            return a_h / HOURS_PER_YEAR, b_h / HOURS_PER_YEAR
    except Exception:
        pass
    return 0.0, float("inf")


def _years_label_to_hours(lbl: str) -> str:
    try:
        s = str(lbl)
        if s.startswith("<"):
            v = float(s[1:]) * HOURS_PER_YEAR
            return f"<{v:.1f}h"
        if s.startswith(">="):
            v = float(s[2:]) * HOURS_PER_YEAR
            return f">={v:.1f}h"
        if "-" in s:
            a, b = s.split("-", 1)
            va = float(a) * HOURS_PER_YEAR
            vb = float(b) * HOURS_PER_YEAR
            return f"{va:.1f}-{vb:.1f}h"
        v = float(s) * HOURS_PER_YEAR
        return f"{v:.1f}h"
    except Exception:
        return str(lbl)


# ---------------- DV01 sweep helpers -----------------
def _compute_dv01_sweep_from_manifest(manifest: pd.DataFrame, filtered: bool = False) -> pd.DataFrame:
    df = manifest.copy()
    if df.empty:
        return pd.DataFrame()
    # Hygiene and numeric coercions
    for c in ("dv01", "error_2nd_order", "moneyness", "vtexp"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "keep" in df.columns:
        df = df[df["keep"] == True]
    if filtered and {"vtexp", "moneyness"}.issubset(df.columns):
        two_hours_years = 2.0 / HOURS_PER_YEAR
        df = df[(df["vtexp"] >= two_hours_years) & (df["moneyness"].abs() <= 1.5)]
    if df.empty or "dv01" not in df.columns or "error_2nd_order" not in df.columns:
        return pd.DataFrame()

    # Success flags
    df["is_success"] = df["error_2nd_order"].abs() <= 5

    # OTM mask if columns are present
    mask_otm = None
    if {"itype", "moneyness"}.issubset(df.columns):
        mask_otm = ((df["itype"] == "C") & (df["moneyness"] < 0)) | ((df["itype"] == "P") & (df["moneyness"] > 0))

    # DV01 threshold grid – include 0.0 and 0.0625 and percentiles
    dv = df["dv01"].dropna()
    if dv.empty:
        return pd.DataFrame()
    q = dv.quantile([i / 100 for i in range(0, 101)])
    grid = sorted(set([0.0, 0.0625] + q.tolist()))

    rows = []
    for thr in grid:
        sub = df[df["dv01"] >= thr]
        if sub.empty:
            rows.append({"threshold": thr, "success_hi": None, "count_hi": 0, "success_hi_otm": None, "count_hi_otm": 0})
            continue
        rate_all = float(sub["is_success"].mean()) if not sub.empty else None
        cnt_all = int(len(sub))
        rate_otm = None
        cnt_otm = 0
        if mask_otm is not None:
            sub_otm = sub[((sub["itype"] == "C") & (sub["moneyness"] < 0)) | ((sub["itype"] == "P") & (sub["moneyness"] > 0))]
            if not sub_otm.empty:
                rate_otm = float(sub_otm["is_success"].mean())
                cnt_otm = int(len(sub_otm))
        rows.append({"threshold": thr, "success_hi": rate_all, "count_hi": cnt_all, "success_hi_otm": rate_otm, "count_hi_otm": cnt_otm})
    return pd.DataFrame(rows)


def _dv01_threshold_figure_from_manifest(manifest: pd.DataFrame, filtered: bool = False) -> "px.Figure":
    sweep = _compute_dv01_sweep_from_manifest(manifest, filtered=filtered)
    if sweep.empty or "threshold" not in sweep.columns:
        return px.line()
    have_otm = "success_hi_otm" in sweep.columns and sweep["success_hi_otm"].notna().any()
    base = sweep[["threshold", "success_hi"]].copy()
    base.rename(columns={"success_hi": "All"}, inplace=True)
    if have_otm:
        base["OTM-only"] = sweep["success_hi_otm"]
    fig = px.line(
        base,
        x="threshold",
        y=[c for c in base.columns if c in ("All", "OTM-only")],
        labels={"threshold": "DV01 Threshold", "value": "Success Rate", "variable": "Subset"},
        title="",
    )
    fig.update_traces(hovertemplate="DV01 ≥ %{x:.5f}<br>Success: %{y:.0%}<extra></extra>")
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    theme_layout = get_graph_figure_layout_defaults(default_theme)
    fig.update_layout(showlegend=True, **theme_layout)
    return fig


assets_folder_path = os.path.join(project_root, 'assets')
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    serve_locally=True,
    assets_folder=assets_folder_path,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "Accuracy Frontier Analysis"

app.layout = Container(
    id="frontier-root",
    theme=default_theme,
    children=[
        html.H1(
            "Option Greeks Accuracy Frontier Dashboard",
            style={"color": default_theme.primary, "margin": "10px 0 10px 0"},
        ),
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Overview",
                    children=[
                        Container(
                            id="overview-panel",
                            theme=default_theme,
                            children=[
                                html.H3("Data Summary", style={"color": default_theme.primary}),
                                html.P(f"Total data points analyzed: {initial_count if initial_count is not None else 'N/A'}"),
                                html.P(f"Data points dropped due to quality filters: {drop_count if drop_count is not None else 'N/A'}"),
                                html.P(f"Data points included in analysis: {kept_count if kept_count is not None else 'N/A'}"),
                                html.H3("Findings", style={"color": default_theme.primary, "marginTop": "10px"}),
                                dcc.Markdown(_load_findings_markdown(), style={"whiteSpace": "pre-wrap"}),
                            ],
                        ).render(),
                    ],
                ),
                dcc.Tab(
                    label="Thresholds",
                    children=[
                        html.P(
                            "Note: Right-hand charts exclude rows with vtexp < 2 hours and |moneyness| > 1.5.",
                            style={"color": default_theme.text_subtle, "margin": "6px 0 10px 0"},
                        ),
                        Grid(
                            id="thresholds-grid",
                            children=[
                                # Row 1: AdjTheor side-by-side
                                (
                                    Container(
                                        id="th-row1-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs AdjTheor Threshold", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "AdjTheor thresholds — All: "
                                                    + (f"{_first_crossing(df_thresh, 'threshold', 'success_hi'):.6f}" if not df_thresh.empty and _first_crossing(df_thresh, 'threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_thresh, 'threshold', 'success_hi_otm'):.6f}" if not df_thresh.empty and _first_crossing(df_thresh, 'threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="thresh-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="thresholds-graph", figure=_threshold_figure(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th-row1-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs AdjTheor Threshold (filtered)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "AdjTheor thresholds — All: "
                                                    + (f"{_first_crossing(df_thresh_flt, 'threshold', 'success_hi'):.6f}" if not df_thresh_flt.empty and _first_crossing(df_thresh_flt, 'threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_thresh_flt, 'threshold', 'success_hi_otm'):.6f}" if not df_thresh_flt.empty and _first_crossing(df_thresh_flt, 'threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="thresh-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="thresholds-graph-flt", figure=_threshold_figure_flt(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                # Row 2: vtexp side-by-side
                                (
                                    Container(
                                        id="th-row2-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs vtexp Threshold", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "vtexp thresholds — All: "
                                                    + _fmt_vtexp_hours(_first_crossing(df_vt_sweep, 'vtexp_threshold', 'success_hi'))
                                                    + ", OTM-only: "
                                                    + _fmt_vtexp_hours(_first_crossing(df_vt_sweep, 'vtexp_threshold', 'success_hi_otm'))
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="vt-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="vtexp-thresholds-graph", figure=_vtexp_threshold_figure(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th-row2-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs vtexp Threshold (filtered)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "vtexp thresholds — All: "
                                                    + _fmt_vtexp_hours(_first_crossing(df_vt_sweep_flt, 'vtexp_threshold', 'success_hi'))
                                                    + ", OTM-only: "
                                                    + _fmt_vtexp_hours(_first_crossing(df_vt_sweep_flt, 'vtexp_threshold', 'success_hi_otm'))
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="vt-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="vtexp-thresholds-graph-flt", figure=_vtexp_threshold_figure_flt(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                # Row 3: moneyness side-by-side
                                (
                                    Container(
                                        id="th-row3-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs moneyness Threshold", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "moneyness thresholds — All: "
                                                    + (f"{_first_crossing(df_mny_sweep, 'moneyness_threshold', 'success_hi'):.6f}" if not df_mny_sweep.empty and _first_crossing(df_mny_sweep, 'moneyness_threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_mny_sweep, 'moneyness_threshold', 'success_hi_otm'):.6f}" if not df_mny_sweep.empty and _first_crossing(df_mny_sweep, 'moneyness_threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="mny-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="moneyness-thresholds-graph", figure=_moneyness_threshold_figure(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th-row3-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs moneyness Threshold (filtered)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "moneyness thresholds — All: "
                                                    + (f"{_first_crossing(df_mny_sweep_flt, 'moneyness_threshold', 'success_hi'):.6f}" if not df_mny_sweep_flt.empty and _first_crossing(df_mny_sweep_flt, 'moneyness_threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_mny_sweep_flt, 'moneyness_threshold', 'success_hi_otm'):.6f}" if not df_mny_sweep_flt.empty and _first_crossing(df_mny_sweep_flt, 'moneyness_threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="mny-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="moneyness-thresholds-graph-flt", figure=_moneyness_threshold_figure_flt(), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                # Row 4: DV01 side-by-side
                                (
                                    Container(
                                        id="th-row4-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs DV01 Threshold", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "DV01 thresholds — All: "
                                                    + (
                                                        f"{_first_crossing(_compute_dv01_sweep_from_manifest(df_manifest), 'threshold', 'success_hi'):.5f}"
                                                        if not df_manifest.empty and not _compute_dv01_sweep_from_manifest(df_manifest).empty and _first_crossing(_compute_dv01_sweep_from_manifest(df_manifest), 'threshold', 'success_hi') is not None
                                                        else "N/A"
                                                    )
                                                    + ", OTM-only: "
                                                    + (
                                                        f"{_first_crossing(_compute_dv01_sweep_from_manifest(df_manifest), 'threshold', 'success_hi_otm'):.5f}"
                                                        if not df_manifest.empty and not _compute_dv01_sweep_from_manifest(df_manifest).empty and _first_crossing(_compute_dv01_sweep_from_manifest(df_manifest), 'threshold', 'success_hi_otm') is not None
                                                        else "N/A"
                                                    )
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="dv01-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="dv01-thresholds-graph", figure=_dv01_threshold_figure_from_manifest(df_manifest, filtered=False), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th-row4-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs DV01 Threshold (filtered)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "DV01 thresholds — All: "
                                                    + (
                                                        f"{_first_crossing(_compute_dv01_sweep_from_manifest(df_manifest, filtered=True), 'threshold', 'success_hi'):.5f}"
                                                        if not df_manifest.empty and not _compute_dv01_sweep_from_manifest(df_manifest, filtered=True).empty and _first_crossing(_compute_dv01_sweep_from_manifest(df_manifest, filtered=True), 'threshold', 'success_hi') is not None
                                                        else "N/A"
                                                    )
                                                    + ", OTM-only: "
                                                    + (
                                                        f"{_first_crossing(_compute_dv01_sweep_from_manifest(df_manifest, filtered=True), 'threshold', 'success_hi_otm'):.5f}"
                                                        if not df_manifest.empty and not _compute_dv01_sweep_from_manifest(df_manifest, filtered=True).empty and _first_crossing(_compute_dv01_sweep_from_manifest(df_manifest, filtered=True), 'threshold', 'success_hi_otm') is not None
                                                        else "N/A"
                                                    )
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="dv01-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="dv01-thresholds-graph-flt", figure=_dv01_threshold_figure_from_manifest(df_manifest, filtered=True), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                            ],
                        ).render()
                    ],
                ),
                dcc.Tab(
                    label="Thresholds (7–8am)",
                    children=[
                        html.P(
                            "Calls-only; Note: Right-hand charts exclude rows with vtexp < 2 hours and |moneyness| > 1.5.",
                            style={"color": default_theme.text_subtle, "margin": "6px 0 10px 0"},
                        ),
                        RadioButton(
                            id="interval-78-th",
                            options=[
                                {"label": "5 min", "value": 5},
                                {"label": "15 min", "value": 15},
                                {"label": "30 min", "value": 30},
                            ],
                            value=5,
                            inline=True,
                            labelStyle={"display": "inline-block", "marginRight": "15px"},
                        ).render(),
                        Grid(
                            id="thresholds-grid-78",
                            children=[
                                (
                                    Container(
                                        id="th78-row1-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs AdjTheor Threshold (7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "AdjTheor thresholds — All: "
                                                    + (f"{_first_crossing(df_thresh_78, 'threshold', 'success_hi'):.6f}" if not df_thresh_78.empty and _first_crossing(df_thresh_78, 'threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_thresh_78, 'threshold', 'success_hi_otm'):.6f}" if not df_thresh_78.empty and _first_crossing(df_thresh_78, 'threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="th78-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="thresholds-graph-78", figure=_threshold_figure_from(data78[5]["df_thresh"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row1-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs AdjTheor Threshold (filtered, 7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "AdjTheor thresholds — All: "
                                                    + (f"{_first_crossing(df_thresh_flt_78, 'threshold', 'success_hi'):.6f}" if not df_thresh_flt_78.empty and _first_crossing(df_thresh_flt_78, 'threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_thresh_flt_78, 'threshold', 'success_hi_otm'):.6f}" if not df_thresh_flt_78.empty and _first_crossing(df_thresh_flt_78, 'threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="th78-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="thresholds-graph-flt-78", figure=_threshold_figure_from(data78[5]["df_thresh_flt"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row2-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs vtexp Threshold (7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "vtexp thresholds — All: "
                                                    + _fmt_vtexp(_first_crossing(df_vt_sweep_78, 'vtexp_threshold', 'success_hi'))
                                                    + ", OTM-only: "
                                                    + _fmt_vtexp(_first_crossing(df_vt_sweep_78, 'vtexp_threshold', 'success_hi_otm'))
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="vt78-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="vtexp-thresholds-graph-78", figure=_vtexp_threshold_figure_from(data78[5]["df_vt"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row2-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs vtexp Threshold (filtered, 7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "vtexp thresholds — All: "
                                                    + _fmt_vtexp(_first_crossing(df_vt_sweep_flt_78, 'vtexp_threshold', 'success_hi'))
                                                    + ", OTM-only: "
                                                    + _fmt_vtexp(_first_crossing(df_vt_sweep_flt_78, 'vtexp_threshold', 'success_hi_otm'))
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="vt78-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="vtexp-thresholds-graph-flt-78", figure=_vtexp_threshold_figure_from(data78[5]["df_vt_flt"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row3-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs moneyness Threshold (7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "moneyness thresholds — All: "
                                                    + (f"{_first_crossing(df_mny_sweep_78, 'moneyness_threshold', 'success_hi'):.6f}" if not df_mny_sweep_78.empty and _first_crossing(df_mny_sweep_78, 'moneyness_threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_mny_sweep_78, 'moneyness_threshold', 'success_hi_otm'):.6f}" if not df_mny_sweep_78.empty and _first_crossing(df_mny_sweep_78, 'moneyness_threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="mny78-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="moneyness-thresholds-graph-78", figure=_moneyness_threshold_figure_from(data78[5]["df_mny"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row3-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs moneyness Threshold (filtered, 7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                (
                                                    "moneyness thresholds — All: "
                                                    + (f"{_first_crossing(df_mny_sweep_flt_78, 'moneyness_threshold', 'success_hi'):.6f}" if not df_mny_sweep_flt_78.empty and _first_crossing(df_mny_sweep_flt_78, 'moneyness_threshold', 'success_hi') is not None else "N/A")
                                                    + ", OTM-only: "
                                                    + (f"{_first_crossing(df_mny_sweep_flt_78, 'moneyness_threshold', 'success_hi_otm'):.6f}" if not df_mny_sweep_flt_78.empty and _first_crossing(df_mny_sweep_flt_78, 'moneyness_threshold', 'success_hi_otm') is not None else "N/A")
                                                ),
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="mny78-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="moneyness-thresholds-graph-flt-78", figure=_moneyness_threshold_figure_from(data78[5]["df_mny_flt"]), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                # Row 4: DV01 side-by-side (7–8am)
                                (
                                    Container(
                                        id="th78-row4-left",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs DV01 Threshold (7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                id="dv01-78-summary-left",
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="dv01-78-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="dv01-thresholds-graph-78", theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                                (
                                    Container(
                                        id="th78-row4-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Success Rate vs DV01 Threshold (filtered, 7–8am)", style={"color": default_theme.primary}),
                                            html.P(
                                                id="dv01-78-summary-right",
                                                style={"color": default_theme.text_subtle, "margin": "4px 0"},
                                            ),
                                            Loading(
                                                id="dv01-78-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "260px"},
                                                children=Graph(id="dv01-thresholds-graph-flt-78", theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 6}
                                ),
                            ],
                        ).render()
                    ],
                ),
                dcc.Tab(
                    label="Frontiers",
                    children=[
                        Grid(
                            id="frontiers-grid",
                            children=[
                                (
                                    Container(
                                        id="frontiers-left",
                                        theme=default_theme,
                                        children=[
                                            html.Label("Select AdjTheor Range:", style={"fontWeight": "bold", "color": default_theme.text_light}),
                                            RadioButton(
                                                id="price-filter",
                                                options=[
                                                    {"label": "All prices", "value": "ALL"},
                                                    {"label": "≤ 1 tick (~0.015625)", "value": "<=0.015625"},
                                                    {"label": "0.015625 – 0.05", "value": "0.015625-0.05"},
                                                    {"label": "0.05 – 0.125", "value": "0.05-0.125"},
                                                    {"label": "> 0.125", "value": ">0.125"},
                                                ],
                                                value="ALL",
                                                inline=True,
                                                labelStyle={"display": "inline-block", "marginRight": "15px"},
                                            ).render(),
                                            RadioButton(
                                                id="dv01-filter",
                                                options=[
                                                    {"label": "All DV01", "value": "ALL"},
                                                    {"label": "DV01 ≥ 0.0625", "value": "THRESH"},
                                                ],
                                                value="ALL",
                                                inline=True,
                                                labelStyle={"display": "inline-block", "marginRight": "15px"},
                                            ).render(),
                                            html.P(
                                                "Success rate = share of rows with |error_2nd_order| ≤ 5 AdjTheor units (absolute); hover shows median AdjTheor per cell.",
                                                style={"fontStyle": "italic", "marginTop": "8px", "color": default_theme.text_subtle},
                                            ),
                                            Loading(
                                                id="frontier-loading",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "320px"},
                                                children=Heatmap(id="frontier-heatmap").render(),
                                            ).render(),
                                            html.Br(),
                                            html.P(
                                                "Filtered heatmap: excludes vtexp < 2 hours and |moneyness| > 1.5.",
                                                style={"color": default_theme.text_subtle, "margin": "6px 0 10px 0"},
                                            ),
                                            Loading(
                                                id="frontier-loading-flt",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "320px"},
                                                children=Graph(id="frontier-heatmap-flt", figure=_frontier_heatmap(df_summary_flt, "Success rate by moneyness vs time-to-expiry (filtered)"), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 8}
                                ),
                                (
                                    Container(
                                        id="frontiers-right",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Cell rows", style={"color": default_theme.primary}),
                                            html.P(id="cell-rows-summary", style={"color": default_theme.text_subtle, "margin": "4px 0"}),
                                            DataTable(id="cell-rows-table", theme=default_theme, page_size=20).render(),
                                        ],
                                    ).render(),
                                    {"width": 4}
                                ),
                            ],
                        ).render()
                    ],
                ),
                dcc.Tab(
                    label="Frontiers (7–8am)",
                    children=[
                        Grid(
                            id="frontiers-grid-78",
                            children=[
                                (
                                    Container(
                                        id="frontiers-left-78",
                                        theme=default_theme,
                                        children=[
                                            html.Label("Select AdjTheor Range:", style={"fontWeight": "bold", "color": default_theme.text_light}),
                                            RadioButton(
                                                id="price-filter-78",
                                                options=[
                                                    {"label": "All prices", "value": "ALL"},
                                                    {"label": "≤ 1 tick (~0.015625)", "value": "<=0.015625"},
                                                    {"label": "0.015625 – 0.05", "value": "0.015625-0.05"},
                                                    {"label": "0.05 – 0.125", "value": "0.05-0.125"},
                                                    {"label": "> 0.125", "value": ">0.125"},
                                                ],
                                                value="ALL",
                                                inline=True,
                                                labelStyle={"display": "inline-block", "marginRight": "15px"},
                                            ).render(),
                                            RadioButton(
                                                id="interval-78",
                                                options=[
                                                    {"label": "5 min", "value": 5},
                                                    {"label": "15 min", "value": 15},
                                                    {"label": "30 min", "value": 30},
                                                ],
                                                value=5,
                                                inline=True,
                                                labelStyle={"display": "inline-block", "marginRight": "15px"},
                                            ).render(),
                                            RadioButton(
                                                id="dv01-filter-78",
                                                options=[
                                                    {"label": "All DV01", "value": "ALL"},
                                                    {"label": "DV01 ≥ 0.0625", "value": "THRESH"},
                                                ],
                                                value="ALL",
                                                inline=True,
                                                labelStyle={"display": "inline-block", "marginRight": "15px"},
                                            ).render(),
                                            html.P(
                                                "Success rate = share of rows with |error_2nd_order| ≤ 5 AdjTheor units (absolute); hover shows median AdjTheor per cell.",
                                                style={"fontStyle": "italic", "marginTop": "8px", "color": default_theme.text_subtle},
                                            ),
                                            Loading(
                                                id="frontier-loading-78",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "320px"},
                                                children=Heatmap(id="frontier-heatmap-78").render(),
                                            ).render(),
                                            html.Br(),
                                            html.P(
                                                "Filtered heatmap: excludes vtexp < 2 hours and |moneyness| > 1.5.",
                                                style={"color": default_theme.text_subtle, "margin": "6px 0 10px 0"},
                                            ),
                                            Loading(
                                                id="frontier-loading-flt-78",
                                                theme=default_theme,
                                                type="circle",
                                                parent_style={"minHeight": "320px"},
                                                children=Graph(id="frontier-heatmap-flt-78", figure=_frontier_heatmap(df_summary_flt_78, "Success rate by moneyness vs time-to-expiry (filtered, 7–8am)"), theme=default_theme).render(),
                                            ).render(),
                                        ],
                                    ).render(),
                                    {"width": 8}
                                ),
                                (
                                    Container(
                                        id="frontiers-right-78",
                                        theme=default_theme,
                                        children=[
                                            html.H3("Cell rows (7–8am)", style={"color": default_theme.primary}),
                                            html.P(id="cell-rows-summary-78", style={"color": default_theme.text_subtle, "margin": "4px 0"}),
                                            DataTable(id="cell-rows-table-78", theme=default_theme, page_size=20).render(),
                                        ],
                                    ).render(),
                                    {"width": 4}
                                ),
                            ],
                        ).render()
                    ],
                ),
                dcc.Tab(
                    label="DOTM",
                    children=[
                        Container(
                            id="dotm-panel",
                            theme=default_theme,
                            children=[
                                Loading(
                                    id="dotm-loading",
                                    theme=default_theme,
                                    type="circle",
                                    parent_style={"minHeight": "320px"},
                                    children=Graph(id="dotm-graph", figure=_dotm_figure(), theme=default_theme).render(),
                                ).render()
                            ],
                        ).render()
                    ],
                ),
            ]
        ),
    ],
).render()


@app.callback(
    [dash.dependencies.Output("frontier-heatmap", "figure"), dash.dependencies.Output("frontier-heatmap-flt", "figure")],
    [dash.dependencies.Input("price-filter", "value"), dash.dependencies.Input("dv01-filter", "value")],
)
def update_frontier_heatmaps(price_bin: str, dv01_filter: str):
    def build_fig(source_df: pd.DataFrame, price_band: str, apply_extra_filters: bool) -> "px.Figure":
        if source_df.empty:
            return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"})

        # Filter by price band if specified
        if not price_band or price_band == "ALL":
            dfp = source_df.copy()
        else:
            dfp = source_df[source_df["adj_bin"] == price_band].copy()

        if dfp.empty:
            return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"}, title="No data for selected range")

        # Aggregate to unique cells
        agg_df = (
            dfp.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)
            .agg({"success_count": "sum", "total_count": "sum"})
            .reset_index()
        )
        agg_df["success_rate"] = agg_df["success_count"] / agg_df["total_count"].replace({0: pd.NA})

        # Average success rate for title
        total_succ = float(agg_df["success_count"].sum())
        total_cnt = float(agg_df["total_count"].sum())
        avg_rate = (total_succ / total_cnt) if total_cnt else None

        # Determine axis orders from categorical metadata when available
        if hasattr(dfp["vtexp_bin"], "cat"):
            vte_order = list(dfp["vtexp_bin"].cat.categories)
        else:
            vte_order = list(dfp["vtexp_bin"].dropna().unique())
        if hasattr(dfp["moneyness_bin"], "cat"):
            mon_order = list(dfp["moneyness_bin"].cat.categories)
        else:
            mon_order = list(dfp["moneyness_bin"].dropna().unique())

        pivot = agg_df.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
        pivot = pivot.reindex(index=vte_order)
        pivot = pivot.reindex(columns=[c for c in mon_order if c in pivot.columns])

        # Build pass/fail text grid (tick / cross) based on threshold ≥ 95%
        pass_mask = pivot >= 0.95
        text_grid = [["✓" if bool(pass_mask.loc[y, x]) else "✗" for x in pivot.columns] for y in pivot.index]

        # Convert vtexp bin labels (years) to hours for readability
        HOURS_PER_YEAR = 24.0 * 252.0
        def _years_label_to_hours(lbl: str) -> str:
            try:
                s = str(lbl)
                if s.startswith("<"):
                    v = float(s[1:]) * HOURS_PER_YEAR
                    return f"<{v:.1f}h"
                if s.startswith(">="):
                    v = float(s[2:]) * HOURS_PER_YEAR
                    return f">={v:.1f}h"
                if "-" in s:
                    a, b = s.split("-", 1)
                    va = float(a) * HOURS_PER_YEAR
                    vb = float(b) * HOURS_PER_YEAR
                    return f"{va:.1f}-{vb:.1f}h"
                v = float(s) * HOURS_PER_YEAR
                return f"{v:.1f}h"
            except Exception:
                return str(lbl)
        y_labels_hours = [ _years_label_to_hours(idx) for idx in pivot.index.tolist() ]

        # Build mean AdjTheor customdata from manifest
        custom = None
        if not df_manifest.empty:
            mf = df_manifest.copy()
            if "keep" in mf.columns:
                mf = mf[mf["keep"] == True].copy()
            for c in ("adjtheor", "moneyness", "vtexp"):
                if c in mf.columns:
                    mf[c] = pd.to_numeric(mf[c], errors="coerce")
            # Apply extra filters for the filtered heatmap
            if apply_extra_filters:
                two_hours_years = 2.0 / (24.0 * 252.0)
                mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
            # Price band filter
            if price_band and price_band != "ALL":
                adj_edges = [0, 0.015625, 0.05, 0.125, float("inf")]
                adj_labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
                mf["adj_bin"] = pd.cut(mf.get("adjtheor"), bins=adj_edges, labels=adj_labels, include_lowest=True)
                mf = mf[mf["adj_bin"] == price_band]
            # Re-bin to match analysis bins currently present (use constant edges)
            mon_labels_const = [
                "(-5,-2]","(-2,-1]","(-1,-0.5]","(-0.5,-0.25]","(-0.25,-0.125]",
                "(-0.125,-0.0625]","(-0.0625,-0.015625]","(-0.015625,0]","(0,0.015625]",
                "(0.015625,0.05]","(0.05,0.125]","(>0.125)"
            ]
            mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
            mf["moneyness_bin"] = pd.cut(mf.get("moneyness"), bins=mon_edges, labels=mon_labels_const, include_lowest=True)
            vte_edges_const = [0, 0.00025, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 1.0]
            vte_labels_const = [
                "<0.00025","0.00025-0.0005","0.0005-0.001","0.001-0.002","0.002-0.005",
                "0.005-0.01","0.01-0.02","0.02-0.05",">=0.05"
            ]
            mf["vtexp_bin"] = pd.cut(mf.get("vtexp"), bins=vte_edges_const, labels=vte_labels_const, right=False)
            # Only compute mean customdata when both bins are available
            if "vtexp_bin" in mf.columns and "moneyness_bin" in mf.columns:
                vlabels = vte_labels_const
                mean_adj = (
                    mf.groupby(["vtexp_bin", "moneyness_bin"], dropna=False, observed=False)["adjtheor"]
                    .mean()
                    .unstack("moneyness_bin")
                )
                mean_adj = mean_adj.reindex(index=vlabels)
                mean_adj = mean_adj.reindex(columns=[c for c in mon_labels_const if c in mean_adj.columns])
                custom = mean_adj.values

        fig = px.imshow(
            pivot.values,
            x=pivot.columns.tolist(),
            y=y_labels_hours,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels={
                "x": "Distance from strike (F−K)",
                "y": "Time to expiry (hours, binned)",
                "color": "Success rate",
            },
            title=(f"Success rate by moneyness vs time-to-expiry (avg: {avg_rate:.0%})" if avg_rate is not None else "Success rate by moneyness vs time-to-expiry"),
        )
        if custom is not None:
            fig.data[0]["customdata"] = custom
            fig.data[0].update(hovertemplate="%{y} | %{x}<br>Success: %{z:.0%}<br>Avg adjtheor: %{customdata:.6e}<extra></extra>")
        # Add in-cell pass/fail annotations (✓/✗)
        fig.data[0].text = text_grid
        fig.data[0].texttemplate = "%{text}"
        fig.data[0].textfont = dict(color=default_theme.text_light, size=10)
        fig.update_layout(
            yaxis=dict(dtick=1),
            paper_bgcolor=default_theme.base_bg,
            plot_bgcolor=default_theme.base_bg,
            font=dict(color=default_theme.text_light),
            xaxis=dict(tickangle=35),
        )
        fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
        return fig

    # If DV01 filter is active, rebuild from manifest with dv01 >= threshold
    def build_with_dv01(source_manifest: pd.DataFrame, price_band: str, extra_filters: bool) -> "px.Figure":
        mf = source_manifest.copy()
        if mf.empty:
            return px.imshow([[None]])
        for c in ("adjtheor", "moneyness", "vtexp", "dv01", "error_2nd_order"):
            if c in mf.columns:
                mf[c] = pd.to_numeric(mf[c], errors="coerce")
        # Align hygiene with baseline: respect keep==True rows only when available
        if "keep" in mf.columns:
            mf = mf[mf["keep"] == True]
        # Apply extra filters used in filtered heatmap
        if extra_filters and {"vtexp", "moneyness"}.issubset(mf.columns):
            two_hours_years = 2.0 / HOURS_PER_YEAR
            mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
        # Price band
        if price_band and price_band != "ALL" and "adjtheor" in mf.columns:
            edges = [0, 0.015625, 0.05, 0.125, float("inf")]
            labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
            mf["adj_bin"] = pd.cut(mf["adjtheor"], bins=edges, labels=labels, include_lowest=True)
            mf = mf[mf["adj_bin"] == price_band]
        # DV01 filter
        dv_col = None
        for name in mf.columns:
            if name.lower() == "dv01":
                dv_col = name
                break
        if dv_col is not None:
            mf = mf[mf[dv_col] >= DV01_THRESHOLD]
        # Success determination
        if "error_2nd_order" in mf.columns:
            mf["is_success"] = mf["error_2nd_order"].abs() <= 5
        # Bin to canonical edges
        mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
        mon_labels = [
            "(-5,-2]","(-2,-1]","(-1,-0.5]","(-0.5,-0.25]","(-0.25,-0.125]",
            "(-0.125,-0.0625]","(-0.0625,-0.015625]","(-0.015625,0]","(0,0.015625]",
            "(0.015625,0.05]","(0.05,0.125]","(>0.125)"
        ]
        vte_edges = [0, 0.00025, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 1.0]
        vte_labels = [
            "<0.00025","0.00025-0.0005","0.0005-0.001","0.001-0.002","0.002-0.005",
            "0.005-0.01","0.01-0.02","0.02-0.05",">=0.05"
        ]
        mf["moneyness_bin"] = pd.cut(mf.get("moneyness"), bins=mon_edges, labels=mon_labels, include_lowest=True)
        mf["vtexp_bin"] = pd.cut(mf.get("vtexp"), bins=vte_edges, labels=vte_labels, right=False)
        agg_df = (
            mf.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)
            .agg(success_count=("is_success", "sum"), total_count=("is_success", "size"))
            .reset_index()
        )
        agg_df["success_rate"] = agg_df["success_count"] / agg_df["total_count"].replace({0: pd.NA})
        pivot = agg_df.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
        pivot = pivot.reindex(index=vte_labels)
        pivot = pivot.reindex(columns=[c for c in mon_labels if c in pivot.columns])
        y_labels_hours = [_years_label_to_hours(idx) for idx in pivot.index.tolist()]

        # Average success rate for title
        total_succ = float(agg_df["success_count"].sum())
        total_cnt = float(agg_df["total_count"].sum())
        avg_rate = (total_succ / total_cnt) if total_cnt else None

        fig = px.imshow(
            pivot.values,
            x=pivot.columns.tolist(),
            y=y_labels_hours,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels={"x": "Distance from strike (F−K)", "y": "Time to expiry (hours, binned)", "color": "Success rate"},
            title=(f"Success rate by moneyness vs time-to-expiry (DV01 filter, avg: {avg_rate:.0%})" if avg_rate is not None else "Success rate by moneyness vs time-to-expiry (DV01 filter)"),
        )
        # In-cell pass/fail overlay ✓/✗
        pass_mask = pivot >= 0.95
        text_grid = [["✓" if (y in pass_mask.index and x in pass_mask.columns and bool(pass_mask.loc[y, x])) else "✗" for x in pivot.columns] for y in pivot.index]
        fig.data[0].text = text_grid
        fig.data[0].texttemplate = "%{text}"
        fig.data[0].textfont = dict(color=default_theme.text_light, size=10)

        # Customdata: mean AdjTheor per cell for hover
        custom = None
        if not mf.empty:
            mean_adj = (
                mf.groupby(["vtexp_bin", "moneyness_bin"], dropna=False, observed=False)["adjtheor"]
                .mean()
                .unstack("moneyness_bin")
            )
            mean_adj = mean_adj.reindex(index=vte_labels)
            mean_adj = mean_adj.reindex(columns=[c for c in mon_labels if c in mean_adj.columns])
            custom = mean_adj.values
        if custom is not None:
            fig.data[0]["customdata"] = custom
            fig.data[0].update(hovertemplate="%{y} | %{x}<br>Success: %{z:.0%}<br>Avg adjtheor: %{customdata:.6e}<extra></extra>")
        fig.update_layout(
            yaxis=dict(dtick=1),
            paper_bgcolor=default_theme.base_bg,
            plot_bgcolor=default_theme.base_bg,
            font=dict(color=default_theme.text_light),
            xaxis=dict(tickangle=35),
        )
        fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
        return fig

    if dv01_filter == "THRESH":
        fig_all = build_with_dv01(df_manifest, price_bin, extra_filters=False)
        fig_flt = build_with_dv01(df_manifest, price_bin, extra_filters=True)
    else:
        fig_all = build_fig(df_summary, price_bin, apply_extra_filters=False)
        fig_flt = build_fig(df_summary_flt, price_bin, apply_extra_filters=True)
    return fig_all, fig_flt
@app.callback(
    [
        dash.dependencies.Output("cell-rows-table", "data"),
        dash.dependencies.Output("cell-rows-table", "columns"),
        dash.dependencies.Output("cell-rows-summary", "children"),
    ],
    [
        dash.dependencies.Input("frontier-heatmap", "clickData"),
        dash.dependencies.Input("frontier-heatmap-flt", "clickData"),
        dash.dependencies.Input("price-filter", "value"),
        dash.dependencies.Input("dv01-filter", "value"),
    ],
)
def populate_cell_rows(click_all, click_flt, price_band, dv01_filter):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [], [], ""
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    click = click_all if trigger_id == "frontier-heatmap" else click_flt
    if not click or "points" not in click or not click["points"]:
        return [], [], ""
    point = click["points"][0]
    mon_lbl = point.get("x")
    vte_lbl = point.get("y")
    mon_lo, mon_hi = _parse_mon_label_to_range(mon_lbl)
    vte_lo, vte_hi = _parse_hours_label_to_years_range(vte_lbl)

    mf = df_manifest.copy()
    # Respect baseline hygiene: apply keep==True when available
    if "keep" in mf.columns:
        mf = mf[mf["keep"] == True]
    for c in ("adjtheor", "moneyness", "vtexp"):
        if c in mf.columns:
            mf[c] = pd.to_numeric(mf[c], errors="coerce")
    # Apply filtered constraints when clicking the filtered heatmap
    if trigger_id == "frontier-heatmap-flt":
        two_hours_years = 2.0 / HOURS_PER_YEAR
        if {"vtexp", "moneyness"}.issubset(mf.columns):
            mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
    # Price band
    if price_band and price_band != "ALL" and "adjtheor" in mf.columns:
        edges = [0, 0.015625, 0.05, 0.125, float("inf")]
        labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
        mf["adj_bin"] = pd.cut(mf["adjtheor"], bins=edges, labels=labels, include_lowest=True)
        mf = mf[mf["adj_bin"] == price_band]
    # DV01 filter
    dv_col = None
    for name in mf.columns:
        if name.lower() == "dv01":
            dv_col = name
            break
    if dv01_filter == "THRESH" and dv_col is not None:
        mf = mf[mf[dv_col] >= DV01_THRESHOLD]
    # Range filters
    if {"moneyness", "vtexp"}.issubset(mf.columns):
        mf = mf[(mf["moneyness"] > mon_lo) & (mf["moneyness"] <= mon_hi) & (mf["vtexp"] >= vte_lo) & (mf["vtexp"] <= vte_hi)]

    if mf.empty:
        return [], [], f"No rows for cell (moneyness {mon_lbl}, vtexp {vte_lbl})."

    # Derive display columns safely
    def hours_from_years(x):
        try:
            return float(x) * HOURS_PER_YEAR
        except Exception:
            return None
    if "vtexp" in mf.columns:
        mf["vtexp_hours"] = mf["vtexp"].apply(hours_from_years)

    preferred_cols = [
        "timestamp", "symbol", "itype", "strike", "underlying_future_price", "moneyness",
        "adjtheor", "vtexp_hours", "error_2nd_order", "pnl_realized", "pnl_explained", "pnl_explained_2nd_order",
        # Greeks (include when present)
        "delta", "gamma", "vega", "theta", "speed", "volga", "vanna", "veta", "charm", "theta_dot", "dv01",
        "bid", "ask", "source_file"
    ]
    cols = [c for c in preferred_cols if c in mf.columns]
    if not cols:
        cols = list(mf.columns)[:20]
    data = mf[cols].to_dict("records")
    columns = [{"name": c, "id": c} for c in cols]
    summary = f"{len(mf)} rows (moneyness {mon_lbl}, vtexp {vte_lbl}); price band: {price_band or 'ALL'}; DV01: {'≥0.0625' if dv01_filter=='THRESH' else 'ALL'}; filtered: {'yes' if trigger_id == 'frontier-heatmap-flt' else 'no'}"
    return data, columns, summary



@app.callback(
    [
        dash.dependencies.Output("thresholds-graph-78", "figure"),
        dash.dependencies.Output("thresholds-graph-flt-78", "figure"),
        dash.dependencies.Output("vtexp-thresholds-graph-78", "figure"),
        dash.dependencies.Output("vtexp-thresholds-graph-flt-78", "figure"),
        dash.dependencies.Output("moneyness-thresholds-graph-78", "figure"),
        dash.dependencies.Output("moneyness-thresholds-graph-flt-78", "figure"),
        dash.dependencies.Output("dv01-thresholds-graph-78", "figure"),
        dash.dependencies.Output("dv01-thresholds-graph-flt-78", "figure"),
        dash.dependencies.Output("dv01-78-summary-left", "children"),
        dash.dependencies.Output("dv01-78-summary-right", "children"),
    ],
    [dash.dependencies.Input("interval-78-th", "value")],
)
def update_thresholds_78(interval_min: int):
    ds = data78.get(interval_min, data78[5])
    fig_adj = _threshold_figure_from(ds["df_thresh"])
    fig_adj_flt = _threshold_figure_from(ds["df_thresh_flt"])
    fig_vt = _vtexp_threshold_figure_from(ds["df_vt"])
    fig_vt_flt = _vtexp_threshold_figure_from(ds["df_vt_flt"])
    fig_mny = _moneyness_threshold_figure_from(ds["df_mny"])
    fig_mny_flt = _moneyness_threshold_figure_from(ds["df_mny_flt"])
    # DV01 figures and summaries
    dv01_fig = _dv01_threshold_figure_from_manifest(ds.get("df_manifest", pd.DataFrame()), filtered=False)
    dv01_fig_flt = _dv01_threshold_figure_from_manifest(ds.get("df_manifest", pd.DataFrame()), filtered=True)
    sweep_left = _compute_dv01_sweep_from_manifest(ds.get("df_manifest", pd.DataFrame()), filtered=False)
    sweep_right = _compute_dv01_sweep_from_manifest(ds.get("df_manifest", pd.DataFrame()), filtered=True)
    left_all = _first_crossing(sweep_left, "threshold", "success_hi") if not sweep_left.empty else None
    left_otm = _first_crossing(sweep_left, "threshold", "success_hi_otm") if not sweep_left.empty else None
    right_all = _first_crossing(sweep_right, "threshold", "success_hi") if not sweep_right.empty else None
    right_otm = _first_crossing(sweep_right, "threshold", "success_hi_otm") if not sweep_right.empty else None
    def _fmt(v):
        try:
            return f"{float(v):.5f}"
        except Exception:
            return "N/A"
    left_txt = f"DV01 thresholds — All: {_fmt(left_all)}, OTM-only: {_fmt(left_otm)}"
    right_txt = f"DV01 thresholds — All: {_fmt(right_all)}, OTM-only: {_fmt(right_otm)}"
    return fig_adj, fig_adj_flt, fig_vt, fig_vt_flt, fig_mny, fig_mny_flt, dv01_fig, dv01_fig_flt, left_txt, right_txt


@app.callback(
    [dash.dependencies.Output("frontier-heatmap-78", "figure"), dash.dependencies.Output("frontier-heatmap-flt-78", "figure")],
    [dash.dependencies.Input("price-filter-78", "value"), dash.dependencies.Input("interval-78", "value"), dash.dependencies.Input("dv01-filter-78", "value")],
)
def update_frontier_heatmaps_78(price_bin: str, interval_min: int, dv01_filter: str):
    def build_fig(source_df: pd.DataFrame, price_band: str, apply_extra_filters: bool) -> "px.Figure":
        if source_df.empty:
            return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"})

        # Filter by price band if specified
        if not price_band or price_band == "ALL":
            dfp = source_df.copy()
        else:
            dfp = source_df[source_df["adj_bin"] == price_band].copy()

        if dfp.empty:
            return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"}, title="No data for selected range")

        # Aggregate to unique cells
        agg_df = (
            dfp.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)
            .agg({"success_count": "sum", "total_count": "sum"})
            .reset_index()
        )
        agg_df["success_rate"] = agg_df["success_count"] / agg_df["total_count"].replace({0: pd.NA})

        # Average success rate for title
        total_succ = float(agg_df["success_count"].sum())
        total_cnt = float(agg_df["total_count"].sum())
        avg_rate = (total_succ / total_cnt) if total_cnt else None

        # Determine axis orders from categorical metadata when available
        if hasattr(dfp["vtexp_bin"], "cat"):
            vte_order = list(dfp["vtexp_bin"].cat.categories)
        else:
            vte_order = list(dfp["vtexp_bin"].dropna().unique())
        if hasattr(dfp["moneyness_bin"], "cat"):
            mon_order = list(dfp["moneyness_bin"].cat.categories)
        else:
            mon_order = list(dfp["moneyness_bin"].dropna().unique())

        pivot = agg_df.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
        pivot = pivot.reindex(index=vte_order)
        pivot = pivot.reindex(columns=[c for c in mon_order if c in pivot.columns])

        # Build pass/fail text grid (tick / cross) based on threshold ≥ 95%
        pass_mask = pivot >= 0.95
        text_grid = [["✓" if bool(pass_mask.loc[y, x]) else "✗" for x in pivot.columns] for y in pivot.index]

        # Convert vtexp bin labels (years) to hours for readability
        HOURS_PER_YEAR = 24.0 * 252.0
        def _years_label_to_hours(lbl: str) -> str:
            try:
                s = str(lbl)
                if s.startswith("<"):
                    v = float(s[1:]) * HOURS_PER_YEAR
                    return f"<{v:.1f}h"
                if s.startswith(">="):
                    v = float(s[2:]) * HOURS_PER_YEAR
                    return f">={v:.1f}h"
                if "-" in s:
                    a, b = s.split("-", 1)
                    va = float(a) * HOURS_PER_YEAR
                    vb = float(b) * HOURS_PER_YEAR
                    return f"{va:.1f}-{vb:.1f}h"
                v = float(s) * HOURS_PER_YEAR
                return f"{v:.1f}h"
            except Exception:
                return str(lbl)
        y_labels_hours = [ _years_label_to_hours(idx) for idx in pivot.index.tolist() ]

        # Build mean AdjTheor customdata from manifest (7–8am)
        custom = None
        if not df_manifest_78.empty:
            mf = df_manifest_78.copy()
            for c in ("adjtheor", "moneyness", "vtexp"):
                if c in mf.columns:
                    mf[c] = pd.to_numeric(mf[c], errors="coerce")
            if apply_extra_filters:
                two_hours_years = 2.0 / (24.0 * 252.0)
                mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
            if price_band and price_band != "ALL":
                adj_edges = [0, 0.015625, 0.05, 0.125, float("inf")]
                adj_labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
                mf["adj_bin"] = pd.cut(mf.get("adjtheor"), bins=adj_edges, labels=adj_labels, include_lowest=True)
                mf = mf[mf["adj_bin"] == price_band]
            mon_labels_const = [
                "(-5,-2]","(-2,-1]","(-1,-0.5]","(-0.5,-0.25]","(-0.25,-0.125]",
                "(-0.125,-0.0625]","(-0.0625,-0.015625]","(-0.015625,0]","(0,0.015625]",
                "(0.015625,0.05]","(0.05,0.125]","(>0.125)"
            ]
            mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
            mf["moneyness_bin"] = pd.cut(mf.get("moneyness"), bins=mon_edges, labels=mon_labels_const, include_lowest=True)
            vte_edges_const = [0, 0.00025, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 1.0]
            vte_labels_const = [
                "<0.00025","0.00025-0.0005","0.0005-0.001","0.001-0.002","0.002-0.005",
                "0.005-0.01","0.01-0.02","0.02-0.05",">=0.05"
            ]
            mf["vtexp_bin"] = pd.cut(mf.get("vtexp"), bins=vte_edges_const, labels=vte_labels_const, right=False)
            if "vtexp_bin" in mf.columns and "moneyness_bin" in mf.columns:
                vlabels = vte_labels_const
                mean_adj = (
                    mf.groupby(["vtexp_bin", "moneyness_bin"], dropna=False, observed=False)["adjtheor"]
                    .mean()
                    .unstack("moneyness_bin")
                )
                mean_adj = mean_adj.reindex(index=vlabels)
                mean_adj = mean_adj.reindex(columns=[c for c in mon_labels_const if c in mean_adj.columns])
                custom = mean_adj.values

        fig = px.imshow(
            pivot.values,
            x=pivot.columns.tolist(),
            y=y_labels_hours,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels={
                "x": "Distance from strike (F−K)",
                "y": "Time to expiry (hours, binned)",
                "color": "Success rate",
            },
            title=(f"Success rate by moneyness vs time-to-expiry (avg: {avg_rate:.0%})" if avg_rate is not None else "Success rate by moneyness vs time-to-expiry"),
        )
        if custom is not None:
            fig.data[0]["customdata"] = custom
            fig.data[0].update(hovertemplate="%{y} | %{x}<br>Success: %{z:.0%}<br>Avg adjtheor: %{customdata:.6e}<extra></extra>")
        fig.data[0].text = text_grid
        fig.data[0].texttemplate = "%{text}"
        fig.data[0].textfont = dict(color=default_theme.text_light, size=10)
        fig.update_layout(
            yaxis=dict(dtick=1),
            paper_bgcolor=default_theme.base_bg,
            plot_bgcolor=default_theme.base_bg,
            font=dict(color=default_theme.text_light),
            xaxis=dict(tickangle=35),
        )
        fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
        return fig

    data = data78.get(interval_min, data78[5])
    def build_with_dv01(source_manifest: pd.DataFrame, price_band: str, extra_filters: bool) -> "px.Figure":
        mf = source_manifest.copy()
        if mf.empty:
            return px.imshow([[None]])
        for c in ("adjtheor", "moneyness", "vtexp", "dv01", "error_2nd_order"):
            if c in mf.columns:
                mf[c] = pd.to_numeric(mf[c], errors="coerce")
        if "keep" in mf.columns:
            mf = mf[mf["keep"] == True]
        if extra_filters and {"vtexp", "moneyness"}.issubset(mf.columns):
            two_hours_years = 2.0 / HOURS_PER_YEAR
            mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
        if price_band and price_band != "ALL" and "adjtheor" in mf.columns:
            edges = [0, 0.015625, 0.05, 0.125, float("inf")]
            labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
            mf["adj_bin"] = pd.cut(mf["adjtheor"], bins=edges, labels=labels, include_lowest=True)
            mf = mf[mf["adj_bin"] == price_band]
        dv_col = None
        for name in mf.columns:
            if name.lower() == "dv01":
                dv_col = name
                break
        if dv_col is not None:
            mf = mf[mf[dv_col] >= DV01_THRESHOLD]
        if "error_2nd_order" in mf.columns:
            mf["is_success"] = mf["error_2nd_order"].abs() <= 5
        mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
        mon_labels = [
            "(-5,-2]","(-2,-1]","(-1,-0.5]","(-0.5,-0.25]","(-0.25,-0.125]",
            "(-0.125,-0.0625]","(-0.0625,-0.015625]","(-0.015625,0]","(0,0.015625]",
            "(0.015625,0.05]","(0.05,0.125]","(>0.125)"
        ]
        vte_edges = [0, 0.00025, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 1.0]
        vte_labels = [
            "<0.00025","0.00025-0.0005","0.0005-0.001","0.001-0.002","0.002-0.005",
            "0.005-0.01","0.01-0.02","0.02-0.05",">=0.05"
        ]
        mf["moneyness_bin"] = pd.cut(mf.get("moneyness"), bins=mon_edges, labels=mon_labels, include_lowest=True)
        mf["vtexp_bin"] = pd.cut(mf.get("vtexp"), bins=vte_edges, labels=vte_labels, right=False)
        agg_df = (
            mf.groupby(["moneyness_bin", "vtexp_bin"], dropna=False, observed=False)
            .agg(success_count=("is_success", "sum"), total_count=("is_success", "size"))
            .reset_index()
        )
        agg_df["success_rate"] = agg_df["success_count"] / agg_df["total_count"].replace({0: pd.NA})
        pivot = agg_df.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
        pivot = pivot.reindex(index=vte_labels)
        pivot = pivot.reindex(columns=[c for c in mon_labels if c in pivot.columns])
        y_labels_hours = [_years_label_to_hours(idx) for idx in pivot.index.tolist()]
        # Average success rate for title
        total_succ = float(agg_df["success_count"].sum())
        total_cnt = float(agg_df["total_count"].sum())
        avg_rate = (total_succ / total_cnt) if total_cnt else None

        fig = px.imshow(
            pivot.values,
            x=pivot.columns.tolist(),
            y=y_labels_hours,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels={"x": "Distance from strike (F−K)", "y": "Time to expiry (hours, binned)", "color": "Success rate"},
            title=(
                f"Success rate by moneyness vs time-to-expiry (DV01 filter, 7–8am, avg: {avg_rate:.0%})"
                if avg_rate is not None
                else "Success rate by moneyness vs time-to-expiry (DV01 filter, 7–8am)"
            ),
        )
        # In-cell pass/fail overlay ✓/✗ at 95%
        pass_mask = pivot >= 0.95
        text_grid = [[
            "✓" if (y in pass_mask.index and x in pass_mask.columns and bool(pass_mask.loc[y, x])) else "✗"
            for x in pivot.columns
        ] for y in pivot.index]
        fig.data[0].text = text_grid
        fig.data[0].texttemplate = "%{text}"
        fig.data[0].textfont = dict(color=default_theme.text_light, size=10)

        # Customdata hover: mean AdjTheor per cell
        custom = None
        if not mf.empty:
            mean_adj = (
                mf.groupby(["vtexp_bin", "moneyness_bin"], dropna=False, observed=False)["adjtheor"]
                .mean()
                .unstack("moneyness_bin")
            )
            mean_adj = mean_adj.reindex(index=vte_labels)
            mean_adj = mean_adj.reindex(columns=[c for c in mon_labels if c in mean_adj.columns])
            custom = mean_adj.values
        if custom is not None:
            fig.data[0]["customdata"] = custom
            fig.data[0].update(hovertemplate="%{y} | %{x}<br>Success: %{z:.0%}<br>Avg adjtheor: %{customdata:.6e}<extra></extra>")
        fig.update_layout(
            yaxis=dict(dtick=1),
            paper_bgcolor=default_theme.base_bg,
            plot_bgcolor=default_theme.base_bg,
            font=dict(color=default_theme.text_light),
            xaxis=dict(tickangle=35),
        )
        fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
        return fig

    if dv01_filter == "THRESH":
        fig_all = build_with_dv01(data["df_manifest"], price_bin, extra_filters=False)
        fig_flt = build_with_dv01(data["df_manifest"], price_bin, extra_filters=True)
    else:
        fig_all = build_fig(data["df_summary"], price_bin, apply_extra_filters=False)
        fig_flt = build_fig(data["df_summary_flt"], price_bin, apply_extra_filters=True)
    return fig_all, fig_flt


@app.callback(
    [
        dash.dependencies.Output("cell-rows-table-78", "data"),
        dash.dependencies.Output("cell-rows-table-78", "columns"),
        dash.dependencies.Output("cell-rows-summary-78", "children"),
    ],
    [
        dash.dependencies.Input("frontier-heatmap-78", "clickData"),
        dash.dependencies.Input("frontier-heatmap-flt-78", "clickData"),
        dash.dependencies.Input("price-filter-78", "value"),
        dash.dependencies.Input("interval-78", "value"),
        dash.dependencies.Input("dv01-filter-78", "value"),
    ],
)
def populate_cell_rows_78(click_all, click_flt, price_band, interval_min, dv01_filter):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [], [], ""
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    click = click_all if trigger_id == "frontier-heatmap-78" else click_flt
    if not click or "points" not in click or not click["points"]:
        return [], [], ""
    point = click["points"][0]
    mon_lbl = point.get("x")
    vte_lbl = point.get("y")
    mon_lo, mon_hi = _parse_mon_label_to_range(mon_lbl)
    vte_lo, vte_hi = _parse_hours_label_to_years_range(vte_lbl)

    data = data78.get(interval_min, data78[5])
    mf = data.get("df_manifest", pd.DataFrame()).copy()
    if "keep" in mf.columns:
        mf = mf[mf["keep"] == True]
    for c in ("adjtheor", "moneyness", "vtexp"):
        if c in mf.columns:
            mf[c] = pd.to_numeric(mf[c], errors="coerce")
    if trigger_id == "frontier-heatmap-flt-78":
        two_hours_years = 2.0 / HOURS_PER_YEAR
        if {"vtexp", "moneyness"}.issubset(mf.columns):
            mf = mf[(mf["vtexp"] >= two_hours_years) & (mf["moneyness"].abs() <= 1.5)]
    if price_band and price_band != "ALL" and "adjtheor" in mf.columns:
        edges = [0, 0.015625, 0.05, 0.125, float("inf")]
        labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
        mf["adj_bin"] = pd.cut(mf["adjtheor"], bins=edges, labels=labels, include_lowest=True)
        mf = mf[mf["adj_bin"] == price_band]
    dv_col = None
    for name in mf.columns:
        if name.lower() == "dv01":
            dv_col = name
            break
    if dv01_filter == "THRESH" and dv_col is not None:
        mf = mf[mf[dv_col] >= DV01_THRESHOLD]
    if {"moneyness", "vtexp"}.issubset(mf.columns):
        mf = mf[(mf["moneyness"] > mon_lo) & (mf["moneyness"] <= mon_hi) & (mf["vtexp"] >= vte_lo) & (mf["vtexp"] <= vte_hi)]

    if mf.empty:
        return [], [], f"No rows for cell (moneyness {mon_lbl}, vtexp {vte_lbl})."

    def hours_from_years(x):
        try:
            return float(x) * HOURS_PER_YEAR
        except Exception:
            return None
    if "vtexp" in mf.columns:
        mf["vtexp_hours"] = mf["vtexp"].apply(hours_from_years)

    preferred_cols = [
        "timestamp", "symbol", "itype", "strike", "underlying_future_price", "moneyness",
        "adjtheor", "vtexp_hours", "error_2nd_order", "pnl_realized", "pnl_explained", "pnl_explained_2nd_order",
        "delta", "gamma", "vega", "theta", "speed", "volga", "vanna", "veta", "charm", "theta_dot", "dv01",
        "bid", "ask", "source_file"
    ]
    cols = [c for c in preferred_cols if c in mf.columns]
    if not cols:
        cols = list(mf.columns)[:20]
    data_out = mf[cols].to_dict("records")
    columns = [{"name": c, "id": c} for c in cols]
    summary = f"{len(mf)} rows (moneyness {mon_lbl}, vtexp {vte_lbl}); price band: {price_band or 'ALL'}; DV01: {'≥0.0625' if dv01_filter=='THRESH' else 'ALL'}; filtered: {'yes' if trigger_id == 'frontier-heatmap-flt-78' else 'no'}"
    return data_out, columns, summary


if __name__ == "__main__":
    port = int(os.getenv("ACCURACY_FRONTIER_PORT", "8060"))
    app.run(debug=False, port=port, dev_tools_hot_reload=False)


