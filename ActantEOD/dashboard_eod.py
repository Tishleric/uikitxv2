#!/usr/bin/env python3
"""
ActantEOD Dashboard Application

This dashboard provides interactive visualization and analysis of Actant scenario metrics data,
with dynamic JSON file selection and comprehensive UI controls.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
import os
import sys
from pathlib import Path

# --- Adjust Python path ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added '{project_root}' to sys.path for package 'src'")

# --- Create module alias for imports ---
import src
sys.modules['uikitxv2'] = src
# --- End Path ---

# Import wrapped components - using correct import pattern
from uikitxv2.components import Grid, ListBox, ComboBox, Graph, DataTable, Button, Container
from uikitxv2.utils.colour_palette import default_theme

# Import local modules
from file_manager import get_most_recent_json_file, scan_json_files, get_json_file_metadata
from data_service import ActantDataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app with assets folder for CSS
assets_folder_path_absolute = os.path.abspath(os.path.join(project_root, 'assets'))
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder=assets_folder_path_absolute)
app.title = "ActantEOD Dashboard"

# Initialize data service
data_service = ActantDataService()

# UI styling constants
text_style = {"color": default_theme.text_light, "marginBottom": "10px"}
header_style = {"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}


def create_dashboard_layout():
    """
    Create the main dashboard layout using wrapped components.
    
    Returns:
        Container: The main dashboard layout
    """
    return Container(
        id="main-container",
        children=[
            
            # Data loading section
            html.Div([
                html.P("Data Source:", style=text_style),
                html.Div(id="current-file-display", style={
                    "color": default_theme.text_subtle, 
                    "marginBottom": "10px",
                    "fontStyle": "italic"
                }),
                Button(
                    id="load-data-button",
                    label="Load Latest Data",
                    theme=default_theme,
                    n_clicks=0
                ).render()
            ], style={"marginBottom": "30px", "textAlign": "center"}),
            
            # Main content grid
            Grid(
                id="main-grid",
                children=[
                    # Left panel - Controls (30% width)
                    (html.Div(
                        id="controls-panel",
                        children=[
                            html.H4("Filters", style={"color": default_theme.primary, "marginBottom": "15px"}),
                            
                            # Scenario selection
                            html.P("Scenarios:", style=text_style),
                            ListBox(
                                id="scenario-listbox",
                                options=[],
                                value=[],
                                multi=True,
                                theme=default_theme,
                                style={"marginBottom": "20px", "width": "100%"}
                            ).render(),
                            
                            # Shock type selection
                            html.P("Shock Type:", style=text_style),
                            ComboBox(
                                id="shock-type-combobox",
                                options=[],
                                value=None,
                                placeholder="Select shock type",
                                theme=default_theme,
                                style={"marginBottom": "20px", "width": "100%"}
                            ).render(),
                            
                            # Metrics selection
                            html.P("Metrics:", style=text_style),
                            ListBox(
                                id="metrics-listbox",
                                options=[],
                                value=[],
                                multi=True,
                                theme=default_theme,
                                style={"marginBottom": "20px", "width": "100%"}
                            ).render(),
                        ],
                        style={
                            "backgroundColor": default_theme.panel_bg,
                            "padding": "20px",
                            "borderRadius": "5px", 
                            "height": "fit-content"
                        }
                    ), {"width": 4}),
                    
                    # Right panel - Visualization (70% width)
                    (Container(
                        id="visualization-panel",
                        children=[
                            # View toggle buttons
                            html.Div([
                                html.P("View Mode:", style={
                                    "color": default_theme.text_light, 
                                    "marginRight": "10px", 
                                    "marginBottom": "0"
                                }),
                                html.Div([
                                    Button(
                                        id="view-toggle-graph",
                                        label="Graph",
                                        theme=default_theme,
                                        n_clicks=1,
                                        style={
                                            "borderTopRightRadius": "0",
                                            "borderBottomRightRadius": "0",
                                            "borderRight": "none",
                                            "backgroundColor": default_theme.primary
                                        }
                                    ).render(),
                                    Button(
                                        id="view-toggle-table",
                                        label="Table",
                                        theme=default_theme,
                                        n_clicks=0,
                                        style={
                                            "borderTopLeftRadius": "0",
                                            "borderBottomLeftRadius": "0",
                                            "backgroundColor": default_theme.panel_bg
                                        }
                                    ).render()
                                ], style={"display": "flex"})
                            ], style={
                                "display": "flex", 
                                "alignItems": "center", 
                                "justifyContent": "center", 
                                "marginBottom": "20px"
                            }),
                            
                            # Graph container
                            html.Div(
                                id="graph-container",
                                children=[
                                    Graph(
                                        id="main-graph",
                                        figure={
                                            'data': [],
                                            'layout': go.Layout(
                                                title="Select data to visualize",
                                                xaxis_title="Shock Value",
                                                yaxis_title="Metric Value",
                                                plot_bgcolor=default_theme.base_bg,
                                                paper_bgcolor=default_theme.panel_bg,
                                                font_color=default_theme.text_light,
                                                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                                                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                                                margin=dict(l=60, r=20, t=60, b=50)
                                            )
                                        },
                                        theme=default_theme,
                                        style={"height": "500px"}
                                    ).render()
                                ],
                                style={"display": "block"}
                            ),
                            
                            # Table container
                            html.Div(
                                id="table-container",
                                children=[
                                    DataTable(
                                        id="main-table",
                                        data=[],
                                        columns=[],
                                        theme=default_theme,
                                        page_size=11,
                                        style_table={"overflowX": "auto", "height": "500px"},
                                        style_header={
                                            "backgroundColor": default_theme.primary,
                                            "color": default_theme.text_light,
                                            "fontWeight": "bold",
                                            "textAlign": "center"
                                        },
                                        style_cell={
                                            "backgroundColor": default_theme.base_bg,
                                            "color": default_theme.text_light,
                                            "textAlign": "center",
                                            "padding": "8px"
                                        }
                                    ).render()
                                ],
                                style={"display": "none"}
                            )
                        ],
                        style={
                            "backgroundColor": default_theme.panel_bg,
                            "padding": "20px",
                            "borderRadius": "5px"
                        }
                    ), {"width": 8})
                ]
            ).render(),
            
            # Data stores
            dcc.Store(id="data-loaded-store", data=False),
            dcc.Store(id="filtered-data-store", data=[])
        ],
        theme=default_theme,
        style={"padding": "20px", "backgroundColor": default_theme.base_bg, "minHeight": "100vh"}
    )


# Set app layout with proper page styling like dashboard.py
app.layout = html.Div(
    children=[
        html.H1("ActantEOD Dashboard", style={"textAlign": "center", "color": default_theme.primary, "padding": "20px 0"}),
        create_dashboard_layout().render()
    ],
    style={"backgroundColor": default_theme.base_bg, "padding": "20px", "minHeight": "100vh", "fontFamily": "Inter, sans-serif"}
)


@app.callback(
    [Output("current-file-display", "children"),
     Output("data-loaded-store", "data"),
     Output("scenario-listbox", "options"),
     Output("shock-type-combobox", "options"),
     Output("metrics-listbox", "options")],
    Input("load-data-button", "n_clicks"),
    prevent_initial_call=False
)
def load_data(n_clicks):
    """
    Load the most recent JSON file and populate filter options.
    
    Args:
        n_clicks: Number of button clicks
        
    Returns:
        Tuple of (file_display, data_loaded_flag, scenario_options, shock_type_options, metric_options)
    """
    try:
        # Get most recent JSON file
        json_file = get_most_recent_json_file()
        
        if json_file is None:
            return "No valid JSON files found", False, [], [], []
        
        # Load data into service
        success = data_service.load_data_from_json(json_file)
        
        if not success:
            return f"Failed to load {json_file.name}", False, [], [], []
        
        # Get metadata for display
        metadata = get_json_file_metadata(json_file)
        file_display = (
            f"Loaded: {metadata['filename']} "
            f"({metadata['size_mb']:.1f} MB, {metadata['scenario_count']} scenarios)"
        )
        
        # Get filter options
        scenarios = data_service.get_scenario_headers()
        scenario_options = [{"label": s, "value": s} for s in scenarios]
        
        shock_types = data_service.get_shock_types()
        shock_type_options = [{"label": s.replace("_", " ").title(), "value": s} for s in shock_types]
        
        metrics = data_service.get_metric_names()
        metric_options = [{"label": m, "value": m} for m in metrics]
        
        logger.info(f"Successfully loaded data from {json_file.name}")
        return file_display, True, scenario_options, shock_type_options, metric_options
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return f"Error loading data: {str(e)}", False, [], [], []


@app.callback(
    Output("filtered-data-store", "data"),
    [Input("scenario-listbox", "value"),
     Input("shock-type-combobox", "value"),
     Input("metrics-listbox", "value")],
    State("data-loaded-store", "data"),
    prevent_initial_call=True
)
def update_filtered_data(selected_scenarios, selected_shock_type, selected_metrics, data_loaded):
    """
    Update filtered data based on user selections.
    
    Args:
        selected_scenarios: List of selected scenario headers
        selected_shock_type: Selected shock type
        selected_metrics: List of selected metrics
        data_loaded: Whether data is loaded
        
    Returns:
        Filtered data as records for storage
    """
    if not data_loaded or not data_service.is_data_loaded():
        return []
    
    try:
        # Build filter parameters
        scenario_filter = selected_scenarios if selected_scenarios else None
        shock_type_filter = [selected_shock_type] if selected_shock_type else None
        metrics_filter = selected_metrics if selected_metrics else None
        
        # Get filtered data
        df = data_service.get_filtered_data(
            scenario_headers=scenario_filter,
            shock_types=shock_type_filter,
            metrics=metrics_filter
        )
        
        if df.empty:
            return []
        
        return df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        return []


@app.callback(
    [Output("graph-container", "style"),
     Output("table-container", "style"),
     Output("view-toggle-graph", "style"),
     Output("view-toggle-table", "style")],
    [Input("view-toggle-graph", "n_clicks"),
     Input("view-toggle-table", "n_clicks")],
    prevent_initial_call=True
)
def toggle_view(graph_clicks, table_clicks):
    """
    Toggle between graph and table views.
    
    Args:
        graph_clicks: Number of graph button clicks
        table_clicks: Number of table button clicks
        
    Returns:
        Tuple of (graph_style, table_style, graph_button_style, table_button_style)
    """
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "view-toggle-graph":
        # Show graph, hide table
        return (
            {"display": "block"},
            {"display": "none"},
            {
                "borderTopRightRadius": "0",
                "borderBottomRightRadius": "0", 
                "borderRight": "none",
                "backgroundColor": default_theme.primary
            },
            {
                "borderTopLeftRadius": "0",
                "borderBottomLeftRadius": "0",
                "backgroundColor": default_theme.panel_bg
            }
        )
    else:
        # Show table, hide graph
        return (
            {"display": "none"},
            {"display": "block"},
            {
                "borderTopRightRadius": "0",
                "borderBottomRightRadius": "0",
                "borderRight": "none", 
                "backgroundColor": default_theme.panel_bg
            },
            {
                "borderTopLeftRadius": "0",
                "borderBottomLeftRadius": "0",
                "backgroundColor": default_theme.primary
            }
        )


@app.callback(
    Output("main-graph", "figure"),
    [Input("filtered-data-store", "data"),
     Input("metrics-listbox", "value")],
    prevent_initial_call=True
)
def update_graph(filtered_data, selected_metrics):
    """
    Update the graph based on filtered data and selected metrics.
    
    Args:
        filtered_data: Filtered data records
        selected_metrics: List of selected metrics
        
    Returns:
        Updated Plotly figure
    """
    if not filtered_data or not selected_metrics:
        return {
            'data': [],
            'layout': go.Layout(
                title="Select scenarios and metrics to visualize",
                xaxis_title="Shock Value",
                yaxis_title="Metric Value",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
                margin=dict(l=60, r=20, t=60, b=50)
            )
        }
    
    try:
        df = pd.DataFrame(filtered_data)
        
        fig = go.Figure()
        
        # Create traces for each scenario-metric combination
        colors = px.colors.qualitative.Set1
        color_idx = 0
        
        for scenario in df['scenario_header'].unique():
            scenario_data = df[df['scenario_header'] == scenario]
            
            for metric in selected_metrics:
                if metric in scenario_data.columns:
                    fig.add_trace(go.Scatter(
                        x=scenario_data['shock_value'],
                        y=scenario_data[metric],
                        mode='lines+markers',
                        name=f"{scenario} - {metric}",
                        line=dict(color=colors[color_idx % len(colors)]),
                        marker=dict(size=6)
                    ))
                    color_idx += 1
        
        fig.update_layout(
            title="Scenario Metrics Analysis",
            xaxis_title="Shock Value",
            yaxis_title="Metric Value",
            plot_bgcolor=default_theme.base_bg,
            paper_bgcolor=default_theme.panel_bg,
            font_color=default_theme.text_light,
            xaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            margin=dict(l=60, r=20, t=60, b=50),
            legend=dict(
                bgcolor=default_theme.panel_bg,
                bordercolor=default_theme.secondary,
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating graph: {e}")
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Error creating graph: {str(e)}",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light
            )
        }


@app.callback(
    [Output("main-table", "data"),
     Output("main-table", "columns")],
    Input("filtered-data-store", "data"),
    prevent_initial_call=True
)
def update_table(filtered_data):
    """
    Update the table based on filtered data.
    
    Args:
        filtered_data: Filtered data records
        
    Returns:
        Tuple of (table_data, table_columns)
    """
    if not filtered_data:
        return [], []
    
    try:
        df = pd.DataFrame(filtered_data)
        
        # Create columns configuration
        columns = []
        for col in df.columns:
            column_config = {"name": col, "id": col}
            
            # Format numeric columns
            if df[col].dtype in ['float64', 'int64']:
                column_config["type"] = "numeric"
                column_config["format"] = {"specifier": ",.2f"}
            
            columns.append(column_config)
        
        return df.to_dict('records'), columns
        
    except Exception as e:
        logger.error(f"Error updating table: {e}")
        return [], []


if __name__ == "__main__":
    app.run(debug=True, port=8050) 