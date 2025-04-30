# demo/app.py (Simplified)

import dash
from dash import html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import os
import sys
import logging
import atexit
import numpy as np

# --- Adjust Python path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)-8s - %(name)s - %(message)s')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logger.debug(f"Added '{src_path}' to sys.path")
else:
    logger.debug(f"'{src_path}' already in sys.path")
# --- End Path Adjustment ---

# --- Import uikitxv2 components ---
try:
    from components import Button, Tabs, Grid, DataTable, ComboBox, Graph
    from lumberjack.logging_config import setup_logging, shutdown_logging
    from utils.colour_palette import default_theme
    import plotly.graph_objects as go
    # Import the decorators
    from decorators.logger_decorator import FunctionLogger
    from decorators.trace_cpu import TraceCpu
    from decorators.trace_memory import TraceMemory
    logger.debug("Successfully imported uikitxv2 components and theme")
except ImportError as e:
    logger.error(f"Error importing uikitxv2 components: {e}")
    sys.exit(1)
# --- End uikitxv2 Import ---

# --- Logging Configuration ---
LOG_DB_DIR = os.path.join(project_root, 'logs')
LOG_DB_PATH = os.path.join(LOG_DB_DIR, 'demo_app_simple_logs.db')
os.makedirs(LOG_DB_DIR, exist_ok=True)
logger.debug(f"Ensuring log database directory exists: {LOG_DB_DIR}")
logger.debug(f"Using log database: {LOG_DB_PATH}")
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH,
    log_level_console=logging.DEBUG
)
atexit.register(shutdown_logging)
logger.info("Logging configured via setup_logging and shutdown registered.")

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "UIKitXv2 Tabs Demo"

# --- Define Mock Datasets ---
# Common x values
x_values = np.linspace(0, 10, 50)

# Data A: Linear trend
data_a_y = 2 * x_values + 1
data_a = go.Scatter(x=x_values, y=data_a_y, mode='lines+markers', name='Data A', line=dict(color=default_theme.primary))

# Data B: Sinusoidal wave
data_b_y = 10 * np.sin(x_values) + 5
data_b = go.Scatter(x=x_values, y=data_b_y, mode='lines+markers', name='Data B', line=dict(color=default_theme.accent))

# Data C: Exponential growth
data_c_y = 2 ** x_values / 100
data_c = go.Scatter(x=x_values, y=data_c_y, mode='lines+markers', name='Data C', line=dict(color=default_theme.secondary))

# Default empty figure
default_figure = go.Figure(layout=go.Layout(
    title="Select data and click Apply",
    xaxis_title="X Axis",
    yaxis_title="Y Axis",
    paper_bgcolor=default_theme.panel_bg,
    plot_bgcolor=default_theme.panel_bg,
    font=dict(color=default_theme.text_light),
))

logger.debug("Created mock datasets for interactive demo")

# --- UI Component Instantiation ---
simple_button = Button(label="Apply", id="simple-demo-button", theme=default_theme)
logger.debug("Instantiated uikitxv2.Button with theme")

# Create ComboBox component
combo_box = ComboBox(
    id="simple-demo-combobox",
    options=["Data A", "Data B", "Data C"],
    placeholder="Select data...",
    clearable=True,
    theme=default_theme
)
logger.debug("Instantiated uikitxv2.ComboBox with theme")

# Create empty Graph component
graph = Graph(
    id="simple-demo-graph",
    figure=default_figure,
    theme=default_theme
)
logger.debug("Instantiated uikitxv2.Graph with theme")

log_table = DataTable(
    id="log-table-display",
    columns=[
        {"name": "Timestamp", "id": "timestamp"},
        {"name": "Function", "id": "function_name"},
        {"name": "Duration (s)", "id": "execution_time_s", "type": "numeric", "format": dash_table.Format.Format(precision=3, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "CPU Δ (%)", "id": "cpu_usage_delta", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Memory Δ (MB)", "id": "memory_usage_delta_mb", "type": "numeric", "format": dash_table.Format.Format(precision=3, scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Log UUID", "id": "log_uuid"},
    ],
    data=[],
    filter_action="none",
    sort_action="native",
    page_size=10,
    theme=default_theme
)
logger.debug("Instantiated uikitxv2.DataTable for logs tab with theme")

# --- Define Tab Content using uikitxv2.Grid ---
components_tab_content_grid = Grid(
    id="grid-components-tab",
    children=[combo_box, simple_button, graph],
    col_widths=[3, 1, 8],
    theme=default_theme
)
logs_tab_content_grid = Grid(
    id="grid-logs-tab",
    children=[log_table],
    theme=default_theme
)
logger.debug("Defined tab content using uikitxv2.Grid with theme")

# --- Instantiate Tabs Component ---
main_tabs = Tabs(
    id="main-demo-tabs",
    tabs=[
        ("Components", components_tab_content_grid),
        ("Logs", logs_tab_content_grid)
    ],
    theme=default_theme
)
logger.debug("Instantiated uikitxv2.Tabs with theme")

# --- App Layout ---
# Just add black background to containing div
app.layout = html.Div([
    main_tabs.render()
], style={
    "backgroundColor": "#000000",
    "padding": "20px",
    "minHeight": "100vh"
})
logger.debug("Dash layout defined with black background")

# --- Callbacks ---
@app.callback(
    Output("simple-demo-graph", "figure"),
    [Input("simple-demo-button", "n_clicks")],
    [State("simple-demo-combobox", "value")]
)
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=False)
def update_graph(n_clicks, selected_data):
    """Update graph based on selected data when Apply button is clicked"""
    if n_clicks is None:
        # Initial load - return default figure
        return default_figure
    
    if selected_data is None:
        # No data selected - return default figure with message
        return go.Figure(layout=go.Layout(
            title="Please select a dataset",
            xaxis_title="X Axis",
            yaxis_title="Y Axis",
            paper_bgcolor=default_theme.panel_bg,
            plot_bgcolor=default_theme.panel_bg,
            font=dict(color=default_theme.text_light),
        ))
    
    # Create new figure with selected dataset
    fig = go.Figure(layout=go.Layout(
        title=f"Showing {selected_data}",
        xaxis_title="X Axis",
        yaxis_title="Y Axis",
        paper_bgcolor=default_theme.panel_bg,
        plot_bgcolor=default_theme.panel_bg,
        font=dict(color=default_theme.text_light),
    ))
    
    # Add appropriate trace based on selection
    if selected_data == "Data A":
        fig.add_trace(data_a)
    elif selected_data == "Data B":
        fig.add_trace(data_b)
    elif selected_data == "Data C":
        fig.add_trace(data_c)
    
    # Apply grid styling - use a darker version of secondary color for grid
    grid_color = "rgba(100, 100, 100, 0.2)"  # Subtle gray with transparency
    fig.update_xaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    fig.update_yaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    
    logger.debug(f"Updated graph with {selected_data}")
    return fig

# --- Execution ---
if __name__ == "__main__":
    logger.info("Starting Dash server...")
    app.run(debug=True, port=8050)

