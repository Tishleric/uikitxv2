from __future__ import annotations

import os
import sys
import pandas as pd

# Ensure project root is on sys.path when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure bond_future_options package directory is importable for modules
# that use local (non-package) imports like `from bachelier_greek import ...`.
bfopts_dir = os.path.join(project_root, 'lib', 'trading', 'bond_future_options')
if bfopts_dir not in sys.path:
    sys.path.insert(0, bfopts_dir)

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update
import plotly.graph_objects as go
from lib.components.themes import get_graph_figure_layout_defaults

from lib.components import Button, ComboBox, Container, DataTable, Grid, RadioButton, default_theme
from apps.dashboards.aggregated_explorer.service import AggregatedCSVService
from lib.trading.bond_future_options.data_across_strikes import data_across_strikes


def create_app() -> dash.Dash:
    service = AggregatedCSVService()

    assets_folder_path = os.path.join(project_root, 'assets')
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        assets_folder=assets_folder_path,
        suppress_callback_exceptions=True,
    )

    day_options = [
        {"label": lbl, "value": val}
        for lbl, val in zip(
            ["Monday 18 AUG", "Tuesday 19 AUG", "Wednesday 20 AUG", "Thursday 21 AUG", "Friday OZN_SEP25"],
            ["18AUG25", "19AUG25", "20AUG25", "21AUG25", "OZN_SEP25"],
        )
        if val in service.list_available_days()
    ]

    day_selector = ComboBox(
        id="day-select",
        options=day_options,
        value=day_options[0]["value"] if day_options else None,
        clearable=False,
        theme=default_theme,
        style={"marginBottom": "10px"},
    ).render()

    side_selector = RadioButton(
        id="side-select",
        options=[{"label": "Call", "value": "C"}, {"label": "Put", "value": "P"}],
        value=None,
        inline=True,
        theme=default_theme,
        style={"marginBottom": "10px"},
    ).render()

    start_selector = ComboBox(
        id="start-time",
        options=[],
        value=None,
        clearable=False,
        theme=default_theme,
        style={"marginBottom": "10px"},
    ).render()

    end_selector = ComboBox(
        id="end-time",
        options=[],
        value=None,
        clearable=False,
        theme=default_theme,
        style={"marginBottom": "10px"},
    ).render()

    run_button = Button(
        id="run-analysis",
        label="Run Analysis",
        theme=default_theme,
        n_clicks=0,
        style={"marginTop": "10px"},
    ).render()

    results_grid = Grid(
        id="results-grid",
        children=[
            html.Div(
                "Select parameters and click Run Analysis.",
                style={"textAlign": "center", "color": default_theme.text_light},
            )
        ],
        style={"marginTop": "20px"},
    ).render()

    # Hidden stores
    store = dcc.Store(id="across-strikes-store", storage_type="memory")
    param_store = dcc.Store(id="param-selection-store", storage_type="session")

    app.layout = Container(
        id="aggregated-explorer",
        children=[
            store,
            param_store,
            html.H3("Aggregated Options Explorer", style={"color": default_theme.primary}),
            html.Label("Select Weekday", style={"color": default_theme.text_light}),
            day_selector,
            html.Label("Select Call/Put", style={"color": default_theme.text_light}),
            side_selector,
            html.Label("Select Start Time", style={"color": default_theme.text_light}),
            start_selector,
            html.Label("Select End Time", style={"color": default_theme.text_light}),
            end_selector,
            run_button,
            results_grid,
        ],
        style={"backgroundColor": default_theme.panel_bg},
    ).render()

    @app.callback(
        Output("side-select", "options"),
        Output("side-select", "value"),
        Input("day-select", "value"),
        prevent_initial_call=False,
    )
    def update_sides(day_value):
        if not day_value:
            return [
                {"label": "Call", "value": "C"},
                {"label": "Put", "value": "P"},
            ], None
        sides = service.list_available_sides(day_value)
        opts = [{"label": "Call", "value": "C"}, {"label": "Put", "value": "P"}]
        opts = [o for o in opts if o["value"] in sides]
        return opts, (opts[0]["value"] if opts else None)

    @app.callback(
        Output("start-time", "options"),
        Output("start-time", "value"),
        Input("day-select", "value"),
        Input("side-select", "value"),
        prevent_initial_call=False,
    )
    def update_start_times(day_value, side_value):
        if not day_value or not side_value:
            return [], None
        try:
            csv_path = service.get_csv_path(day_value, side_value)
            times = service.list_unique_timestamps(csv_path)
            opts = [{"label": t, "value": t} for t in times]
            return opts, (opts[0]["value"] if opts else None)
        except FileNotFoundError:
            return [], None

    @app.callback(
        Output("end-time", "options"),
        Output("end-time", "value"),
        Input("start-time", "value"),
        State("day-select", "value"),
        State("side-select", "value"),
        prevent_initial_call=False,
    )
    def update_end_times(start_value, day_value, side_value):
        if not day_value or not side_value or not start_value:
            return [], None
        try:
            csv_path = service.get_csv_path(day_value, side_value)
            times = service.list_unique_timestamps(csv_path)
            filtered = [t for t in times if t > start_value]
            opts = [{"label": t, "value": t} for t in filtered]
            return opts, (opts[0]["value"] if opts else None)
        except FileNotFoundError:
            return [], None

    @app.callback(
        Output("results-grid", "children"),
        Output("across-strikes-store", "data"),
        Input("run-analysis", "n_clicks"),
        State("day-select", "value"),
        State("side-select", "value"),
        State("start-time", "value"),
        State("end-time", "value"),
        prevent_initial_call=True,
    )
    def run_analysis(n_clicks, day_value, side_value, start_value, end_value):
        if not n_clicks:
            return no_update, no_update
        if not (day_value and side_value and start_value and end_value):
            return [html.Div("Please select all parameters.")], no_update
        try:
            csv_path = service.get_csv_path(day_value, side_value)
            df_start = service.get_rows_for_timestamp(csv_path, start_value)
            df_end = service.get_rows_for_timestamp(csv_path, end_value)
            # Ensure numeric types needed by decomposition
            for df in (df_start, df_end):
                if 'adjtheor' in df.columns:
                    df['adjtheor'] = pd.to_numeric(df['adjtheor'], errors='coerce')
                # Drop rows missing core fields
                df.dropna(subset=['underlying_future_price', 'vtexp', 'strike', 'adjtheor'], inplace=True)

            # Align by common strikes so data_across_strikes receives equal-length slices
            common_strikes = sorted(set(df_start['strike']).intersection(set(df_end['strike'])))
            if not common_strikes:
                return [html.Div("No common strikes between selected times.", style={"color": default_theme.danger})], no_update

            df_start_aligned = df_start[df_start['strike'].isin(common_strikes)].copy().sort_values('strike')
            df_end_aligned = df_end[df_end['strike'].isin(common_strikes)].copy().sort_values('strike')

            # Compute across-strikes PnL decomposition
            result_df = data_across_strikes(df_start_aligned, df_end_aligned)
            if result_df is None or len(result_df) == 0:
                return [html.Div("Analysis returned no rows (length mismatch or invalid data).", style={"color": default_theme.danger})], no_update

            summary = html.Div(
                f"{len(common_strikes)} strikes | {day_value} {side_value} | start {start_value} → end {end_value}",
                style={"color": default_theme.text_subtle, "marginBottom": "8px"},
            )

            table_across = DataTable(
                id="across-strikes-table",
                data=result_df,
                page_size=20,
                theme=default_theme,
            ).render()

            # Build figures
            df_plot = result_df.sort_values("moneyness").reset_index(drop=True)
            layout_defaults = get_graph_figure_layout_defaults(default_theme)

            fig_pnl = go.Figure()
            fig_pnl.add_trace(go.Scatter(x=df_plot["moneyness"], y=df_plot["pnl_explained"], mode="lines+markers", name="PnL Explained"))
            fig_pnl.add_trace(go.Scatter(x=df_plot["moneyness"], y=df_plot["pnl_actual"], mode="lines+markers", name="PnL Actual"))
            fig_pnl.update_layout(title="PnL vs Moneyness", **layout_defaults)

            fig_iv = go.Figure()
            fig_iv.add_trace(go.Scatter(x=df_plot["moneyness"], y=df_plot["IV1"], mode="lines+markers", name="IV1"))
            fig_iv.add_trace(go.Scatter(x=df_plot["moneyness"], y=df_plot["IV2"], mode="lines+markers", name="IV2"))
            fig_iv.update_layout(title="IV vs Moneyness", **layout_defaults)

            graphs = Grid(
                id="graphs-grid",
                children=[
                    html.Div(dcc.Graph(id="pnl-vs-moneyness", figure=fig_pnl, style={"height": "320px"})),
                    html.Div(dcc.Graph(id="iv-vs-moneyness", figure=fig_iv, style={"height": "320px"})),
                ],
                style={"marginTop": "16px"},
            ).render()

            # Dynamic parameter selector and graph area
            param_label = html.Label(
                "Select parameters to plot (multi)",
                style={"color": default_theme.text_light, "marginTop": "10px"},
            )
            param_selector = ComboBox(
                id="param-selector",
                options=[],
                value=[],
                multi=True,
                clearable=True,
                theme=default_theme,
                style={"marginTop": "6px", "marginBottom": "10px", "width": "100%"},
                placeholder="Choose one or more columns (e.g., delta_pnl, percentage_error, …)",
            ).render()

            param_combined_graph = dcc.Graph(id="param-combined-graph", style={"height": "960px", "width": "100%"})

            content = html.Div([summary, graphs, param_label, param_selector, param_combined_graph, table_across])
            return [content], df_plot.to_dict("records")
        except FileNotFoundError:
            return [html.Div("CSV not found for the selected parameters.")], no_update

    # Persist selection and restore after re-run
    @app.callback(
        Output("param-selection-store", "data"),
        Input("param-selector", "value"),
        prevent_initial_call=False,
    )
    def persist_param_selection(selected):
        return selected or []

    @app.callback(
        Output("param-selector", "options"),
        Output("param-selector", "value"),
        Input("across-strikes-store", "data"),
        State("param-selection-store", "data"),
        prevent_initial_call=False,
    )
    def populate_param_options(store_data, saved_selection):
        if not store_data:
            return [], []
        df = pd.DataFrame(store_data)
        numeric_cols = [c for c in df.columns if c != "moneyness" and pd.api.types.is_numeric_dtype(df[c])]
        options = [{"label": c, "value": c} for c in numeric_cols]
        # Keep only those previously selected that still exist
        restored = [c for c in (saved_selection or []) if c in numeric_cols]
        return options, restored

    # Render graphs for selected parameters
    @app.callback(
        Output("param-combined-graph", "figure"),
        Input("param-selector", "value"),
        State("across-strikes-store", "data"),
        prevent_initial_call=False,
    )
    def render_param_combined(selected_params, store_data):
        layout_defaults = get_graph_figure_layout_defaults(default_theme)
        if not store_data or not selected_params:
            fig = go.Figure()
            fig.update_layout(title="Select parameters to plot", **layout_defaults)
            return fig
        df = pd.DataFrame(store_data).sort_values("moneyness").reset_index(drop=True)
        fig = go.Figure()
        for col in selected_params:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                fig.add_trace(go.Scatter(x=df["moneyness"], y=df[col], mode="lines+markers", name=col))
        fig.update_layout(title="Selected parameters vs Moneyness", hovermode="x unified", **layout_defaults)
        return fig

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8060)


