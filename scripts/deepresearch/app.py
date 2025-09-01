# Path: apps/dashboards/accuracy_frontier/app.py
import os
import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px

# Set up paths for data and report
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
data_dir = os.path.join(base_path, "data", "output", "accuracy_validation")
report_path = os.path.join(base_path, "reports", "accuracy_frontier", "README.md")

# Load data from analysis outputs
df_thresh = pd.read_csv(os.path.join(data_dir, "threshold_sweep.csv"))
df_summary = pd.read_csv(os.path.join(data_dir, "summary_success_by_bins.csv"))
df_dotm = pd.read_csv(os.path.join(data_dir, "dotm_epsilon.csv"))
inflect = pd.read_csv(os.path.join(data_dir, "inflection_candidates.csv"))
try:
    df_vol = pd.read_csv(os.path.join(data_dir, "vol_diff_vs_pm.csv"))
except Exception:
    df_vol = pd.DataFrame()

# Load manifest to get counts (if available)
manifest_path = os.path.join(data_dir, "clean_manifest.csv")
initial_count = None; drop_count = None; kept_count = None
if os.path.exists(manifest_path):
    manifest_df = pd.read_csv(manifest_path, usecols=["keep"])
    drop_count = int((manifest_df["keep"] == False).sum())
    kept_count = int((manifest_df["keep"] == True).sum())
    initial_count = drop_count + kept_count
elif not df_summary.empty and "total_count" in df_summary.columns:
    kept_count = int(df_summary["total_count"].sum())
    drop_count = None
    initial_count = kept_count

# Extract recommended global threshold (All category)
rec_thresh = None
if not inflect[inflect['category'] == 'All'].empty:
    rec_val = inflect[inflect['category'] == 'All']['threshold_for_95pct'].iloc[0]
    if pd.notna(rec_val):
        rec_thresh = float(rec_val)

# Figure: Success vs threshold (overall vs safe-region)
fig_threshold = px.line()
if 'threshold' in df_thresh.columns:
    fig_threshold = px.line(df_thresh, x="threshold", y=["success_hi", "success_overall"],
                             labels={"threshold": "Adj. Price Threshold", "value": "Success Rate", "variable": "Metric"},
                             title="Success Rate vs Adj. Price Threshold")
    fig_threshold.add_hline(y=0.95, line_dash="dash", line_color="gray",
                             annotation_text="95% target", annotation_position="bottom right")
    if rec_thresh is not None:
        fig_threshold.add_vline(x=rec_thresh, line_dash="dot", line_color="green",
                                 annotation_text=f"Recommended τ = {rec_thresh:.6f}", annotation_position="top right")
    if "success_hi_ci_lower" in df_thresh.columns:
        fig_threshold.add_traces([{
            "type": "scatter", "x": df_thresh["threshold"], "y": df_thresh["success_hi_ci_upper"],
            "mode": "lines", "line": {"width": 0}, "showlegend": False, "hoverinfo": "skip"
        }, {
            "type": "scatter", "x": df_thresh["threshold"], "y": df_thresh["success_hi_ci_lower"],
            "mode": "lines", "fill": "tonexty",
            "line": {"width": 0}, "fillcolor": "rgba(0,0,255,0.1)",
            "name": "Success (95% CI)", "hoverinfo": "skip"
        }])
    fig_threshold.update_layout(yaxis=dict(range=[0,1]))

# Figure: DOTM success vs epsilon
fig_dotm = px.line()
if not df_dotm.empty:
    df_dotm_long = df_dotm.melt(id_vars="epsilon", var_name="moneyness_cutoff", value_name="success_rate")
    fig_dotm = px.line(df_dotm_long, x="epsilon", y="success_rate", color="moneyness_cutoff",
                       markers=True,
                       labels={"epsilon": "Epsilon (price increment)", "success_rate": "Success Rate", "moneyness_cutoff": "Moneyness ≤ cutoff"},
                       title="DOTM Success vs ε")
    fig_dotm.update_layout(yaxis=dict(range=[0,1]))

# Content for PM Comparison tab
if df_vol.empty or df_vol.shape[0] == 0:
    pm_content = html.Div("No Pricing Monkey vol data available for comparison.",
                          style={"fontStyle": "italic", "margin": "15px"})
else:
    pm_content = html.Div([
        html.H5("Vol Diff Data Sample"),
        dcc.Markdown(df_vol.head().to_csv(index=False))
    ])

# Load findings report markdown
findings_md = ""
if os.path.exists(report_path):
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            findings_md = f.read()
    except Exception:
        findings_md = "*Error loading findings report.*"

app = dash.Dash(__name__)
app.title = "Accuracy Frontier Analysis"

app.layout = html.Div([
    html.H1("Option Greeks Accuracy Frontier Dashboard"),
    dcc.Tabs([
        dcc.Tab(label="Overview", children=[
            html.Div([
                html.H3("Data Summary"),
                html.P(f"Total data points analyzed: {initial_count if initial_count is not None else 'N/A'}"),
                html.P(f"Data points dropped due to quality filters: {drop_count if drop_count is not None else 'N/A'}"),
                html.P(f"Data points included in analysis: {kept_count if kept_count is not None else 'N/A'}")
            ], style={"padding": "10px"}),
            html.H3("Findings"),
            dcc.Markdown(findings_md, style={"whiteSpace": "pre-wrap", "padding": "10px"})
        ]),
        dcc.Tab(label="Thresholds", children=[
            html.Div([
                dcc.Graph(figure=fig_threshold, config={"toImageButtonOptions": {"height": 500, "width": 700}})
            ], style={"padding": "10px"})
        ]),
        dcc.Tab(label="Frontiers", children=[
            html.Div([
                html.Label("Select Price Range:", style={"fontWeight": "bold"}),
                dcc.RadioItems(
                    id="price-filter",
                    options=[
                        {"label": "All", "value": "ALL"},
                        {"label": "≤0.015625", "value": "<=0.015625"},
                        {"label": "0.015625-0.05", "value": "0.015625-0.05"},
                        {"label": "0.05-0.125", "value": "0.05-0.125"},
                        {"label": ">0.125", "value": ">0.125"}
                    ],
                    value="ALL",
                    labelStyle={'display': 'inline-block', 'marginRight': '15px'}
                ),
                dcc.Graph(id="frontier-heatmap")
            ], style={"padding": "10px"})
        ]),
        dcc.Tab(label="DOTM", children=[
            html.Div([
                dcc.Graph(figure=fig_dotm, config={"toImageButtonOptions": {"height": 500, "width": 700}})
            ], style={"padding": "10px"})
        ]),
        dcc.Tab(label="PM Comparison", children=[
            html.Div(pm_content, style={"padding": "10px"})
        ])
    ])
])

@app.callback(
    dash.dependencies.Output("frontier-heatmap", "figure"),
    [dash.dependencies.Input("price-filter", "value")]
)
def update_frontier_heatmap(price_bin):
    if price_bin is None or price_bin == "ALL":
        df_all = df_summary.groupby(["moneyness_bin", "vtexp_bin"], as_index=False).agg({"success_count": "sum", "total_count": "sum"})
        df_all['success_rate'] = df_all['success_count'] / df_all['total_count']
        df_plot = df_all
    else:
        df_plot = df_summary[df_summary['adj_bin'] == price_bin]
    if df_plot.empty:
        return px.imshow([[None]], labels={"x": "Moneyness Bin", "y": "Time-to-Exp Bin", "color": "Success Rate"},
                         title="No data for selected range")
    pivot = df_plot.pivot(index="vtexp_bin", columns="moneyness_bin", values="success_rate")
    mon_labels = ["(-5,-2]", "(-2,-1]", "(-1,-0.5]", "(-0.5,-0.25]", "(-0.25,-0.125]", "(-0.125,-0.0625]",
                  "(-0.0625,-0.015625]", "( -0.015625,0]", "(0,0.015625]", "(0.015625,0.0625]", "(0.0625,0.125]",
                  "(0.125,0.25]", "(0.25,0.5]", "(0.5,1]", "(1,2]", "(2,5]"]
    vte_labels = ["<0.002", "0.002-0.01", "0.01-0.05", ">=0.05"]
    pivot = pivot.reindex(index=vte_labels, fill_value=None)
    pivot = pivot[[col for col in mon_labels if col in pivot.columns]]
    fig = px.imshow(pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                    color_continuous_scale="Viridis", aspect="auto",
                    labels={"x": "Moneyness Bin", "y": "Time-to-Expiry Bin", "color": "Success Rate"},
                    title="Success Rate by Moneyness vs Time-to-Expiry")
    fig.update_layout(yaxis=dict(dtick=1))
    fig.update_coloraxes(cmin=0, cmax=1)
    return fig

if __name__ == "__main__":
    app.run(debug=False)
