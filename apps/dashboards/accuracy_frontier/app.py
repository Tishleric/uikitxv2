import os
import sys
import dash
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
from components import Container, Grid, Graph


def _load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
DATA_DIR = os.path.join(BASE_PATH, "data", "output", "accuracy_validation")
REPORT_PATH = os.path.join(BASE_PATH, "reports", "accuracy_frontier", "README.md")

df_thresh = _load_csv(os.path.join(DATA_DIR, "threshold_sweep.csv"))
df_summary = _load_csv(os.path.join(DATA_DIR, "summary_success_by_bins.csv"))
df_dotm = _load_csv(os.path.join(DATA_DIR, "dotm_epsilon.csv"))
df_inflect = _load_csv(os.path.join(DATA_DIR, "inflection_candidates.csv"))
df_manifest = _load_csv(os.path.join(DATA_DIR, "clean_manifest.csv"))

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
        title="Success Rate vs AdjTheor Threshold",
    )
    fig.update_traces(hovertemplate="AdjTheor ≥ %{x:.6f}<br>Success: %{y:.0%}<extra></extra>")
    fig.update_layout(showlegend=True)
    fig.add_hline(y=0.95, line_dash="dash", line_color="gray", annotation_text="95% target")
    # Auto-fit Y with headroom to 1.0
    y_min = float(base[[c for c in base.columns if c in ("All", "OTM-only")]].min().min()) if not base.empty else 0.0
    lower = max(0.0, y_min - 0.05)
    fig.update_layout(yaxis=dict(range=[lower, 1]))
    return fig


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


def _load_findings_markdown() -> str:
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "*Error loading findings report.*"
    return "*No findings report found at reports/accuracy_frontier/README.md.*"


assets_folder_path = os.path.join(project_root, 'assets')
app = dash.Dash(__name__, suppress_callback_exceptions=True, serve_locally=True, assets_folder=assets_folder_path)
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
                        Container(
                            id="thresholds-panel",
                            theme=default_theme,
                            children=[
                                html.P(
                                    rec_summary_text or "",
                                    style={"color": default_theme.text_subtle, "marginBottom": "6px"},
                                ),
                                Loading(
                                    id="thresh-loading",
                                    theme=default_theme,
                                    type="circle",
                                    parent_style={"minHeight": "320px"},
                                    children=Graph(id="thresholds-graph", figure=_threshold_figure(), theme=default_theme).render(),
                                ).render()
                            ],
                        ).render()
                    ],
                ),
                dcc.Tab(
                    label="Frontiers",
                    children=[
                        Container(
                            id="frontiers-panel",
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
                                html.P(
                                    "Success rate = share of rows with |error_2nd_order| ≤ 5 AdjTheor units (absolute).",
                                    style={"fontStyle": "italic", "marginTop": "8px", "color": default_theme.text_subtle},
                                ),
                                Loading(
                                    id="frontier-loading",
                                    theme=default_theme,
                                    type="circle",
                                    parent_style={"minHeight": "320px"},
                                    children=Heatmap(id="frontier-heatmap").render(),
                                ).render(),
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
    dash.dependencies.Output("frontier-heatmap", "figure"),
    [dash.dependencies.Input("price-filter", "value")],
)
def update_frontier_heatmap(price_bin: str):
    if df_summary.empty:
        return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"})

    # Aggregate success rate for selected slice
    if not price_bin or price_bin == "ALL":
        df_all = (
            df_summary.groupby(["moneyness_bin", "vtexp_bin"], as_index=False, observed=False)
            .agg({"success_count": "sum", "total_count": "sum"})
        )
        df_all["success_rate"] = df_all["success_count"] / df_all["total_count"]
        df_plot = df_all
    else:
        df_plot = df_summary[df_summary["adj_bin"] == price_bin]

    if df_plot.empty:
        return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"}, title="No data for selected range")

    # Average success for the filtered slice
    if ("success_count" in df_plot.columns) and ("total_count" in df_plot.columns):
        total_succ = float(df_plot["success_count"].sum())
        total_cnt = float(df_plot["total_count"].sum())
        avg_rate = (total_succ / total_cnt) if total_cnt else None
    else:
        avg_rate = None

    pivot = df_plot.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
    # Enforce consistent axis ordering
    vte_labels = ["<0.002", "0.002-0.01", "0.01-0.05", ">=0.05"]
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
    ordered_cols = [c for c in mon_labels if c in pivot.columns]
    if not ordered_cols:
        ordered_cols = pivot.columns.tolist()
    pivot = pivot.reindex(index=vte_labels)
    pivot = pivot.reindex(columns=ordered_cols)

    # Build customdata: median adjtheor per cell (filtered manifest)
    custom = None
    if not df_manifest.empty:
        dfp = df_manifest.copy()
        # Prefer "kept" rows if available
        if "keep" in dfp.columns:
            dfp = dfp[dfp["keep"] == True].copy()
        for c in ("adjtheor", "moneyness", "vtexp"):
            if c in dfp.columns:
                dfp[c] = pd.to_numeric(dfp[c], errors="coerce")
        # Re-bin to match analysis
        mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
        vte_edges = [0, 0.002, 0.01, 0.05, 1.0]
        dfp["moneyness_bin"] = pd.cut(dfp.get("moneyness"), bins=mon_edges, labels=mon_labels, include_lowest=True)
        dfp["vtexp_bin"] = pd.cut(dfp.get("vtexp"), bins=vte_edges, labels=vte_labels, right=False)
        # Optional filter by price band
        if price_bin and price_bin != "ALL":
            adj_edges = [0, 0.015625, 0.05, 0.125, float("inf")]
            adj_labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
            dfp["adj_bin"] = pd.cut(dfp.get("adjtheor"), bins=adj_edges, labels=adj_labels, include_lowest=True)
            dfp = dfp[dfp["adj_bin"] == price_bin]
        med = (
            dfp.groupby(["vtexp_bin", "moneyness_bin"], dropna=False, observed=False)["adjtheor"].median().unstack("moneyness_bin")
        )
        med = med.reindex(index=vte_labels)
        med = med.reindex(columns=ordered_cols)
        custom = med.values

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
        title="Success rate by moneyness vs time-to-expiry",
    )
    if custom is not None:
        fig.data[0]["customdata"] = custom
        fig.data[0].update(hovertemplate="%{y} | %{x}<br>Success: %{z:.0%}<br>Median adjtheor: %{customdata:.6e}<extra></extra>")
    fig.update_layout(
        yaxis=dict(dtick=1),
        paper_bgcolor=default_theme.base_bg,
        plot_bgcolor=default_theme.base_bg,
        font=dict(color=default_theme.text_light),
    )
    fig.update_coloraxes(cmin=0, cmax=1, colorbar=dict(tickformat=".0%"))
    if avg_rate is not None:
        fig.update_layout(title=f"Success rate by moneyness vs time-to-expiry (avg: {avg_rate:.0%})")
    return fig


if __name__ == "__main__":
    port = int(os.getenv("ACCURACY_FRONTIER_PORT", "8060"))
    app.run(debug=False, port=port, dev_tools_hot_reload=False)


