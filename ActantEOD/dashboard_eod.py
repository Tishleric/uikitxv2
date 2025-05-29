#!/usr/bin/env python3
"""
ActantEOD Dashboard Application.

A comprehensive dashboard for analyzing End-of-Day trading data from Actant,
with support for multi-scenario visualization, metric categorization, and
both tabular and graphical views.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
from dash.dependencies import ALL, MATCH

# Add parent directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import UIKit components
from src.components import (
    Button, Checkbox, ComboBox, Container, DataTable, 
    Graph, Grid, ListBox, RangeSlider, Toggle
)
from src.utils.colour_palette import default_theme

# Import local modules
from data_service import ActantDataService
from file_manager import get_most_recent_json_file, get_json_file_metadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize data service
data_service = ActantDataService()

# Initialize Dash app with assets folder for CSS styling
assets_folder_path = str(project_root / "assets")
app = Dash(__name__, assets_folder=assets_folder_path)
app.title = "ActantEOD Dashboard"

# Suppress callback exceptions for dynamic components
app.config.suppress_callback_exceptions = True

# UI styling constants
text_style = {"color": default_theme.text_light, "marginBottom": "10px"}
header_style = {"color": default_theme.primary, "marginBottom": "20px", "textAlign": "center"}


def format_shock_value_for_display(value: float, shock_type: str) -> str:
    """
    Format shock value for display based on shock type.
    
    Args:
        value: Shock value as float
        shock_type: Type of shock ('percentage' or 'absolute_usd')
        
    Returns:
        Formatted string for display
    """
    if shock_type == "percentage":
        # Convert decimal to percentage and format
        percentage = value * 100
        if percentage == 0:
            return "0%"
        return f"{percentage:+.1f}%"
    else:  # absolute_usd
        # Format as currency
        if value == 0:
            return "$0"
        return f"${value:+.2f}"


def create_shock_amount_options(shock_values: List[float], shock_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Create formatted options for shock amount listbox.
    
    Args:
        shock_values: List of shock values
        shock_type: Type of shock for formatting, or None for mixed display
        
    Returns:
        List of option dictionaries with label and value
    """
    if not shock_values:
        return []
    
    options = []
    for value in shock_values:
        if shock_type:
            # Use specific formatting for known shock type
            label = format_shock_value_for_display(value, shock_type)
        else:
            # Mixed display - determine type based on value range
            # Percentage values are between -0.5 and 0.5 (excluding larger absolute values)
            # This handles the case where we have both percentage (-0.3 to 0.3) and absolute (-2.0 to 2.0)
            if -0.5 <= value <= 0.5:
                label = format_shock_value_for_display(value, "percentage")
            else:
                label = format_shock_value_for_display(value, "absolute_usd")
        
        options.append({"label": label, "value": value})
    
    return options


def _create_density_aware_marks(shock_values: List[float], shock_type: str) -> Dict[float, str]:
    """
    Create marks dictionary with mode-specific labeling strategies.
    
    Args:
        shock_values: List of shock values to create marks for
        shock_type: Type of shock for formatting
        
    Returns:
        Dictionary mapping shock values to label strings (empty string = no label)
    """
    if not shock_values:
        return {}
    
    marks = {}
    
    if shock_type == "absolute_usd":
        # Absolute mode: label everything (less cluttered by nature)
        for val in shock_values:
            marks[val] = format_shock_value_for_display(val, shock_type)
    
    elif shock_type == "percentage":
        # Percentage mode: surgical labeling strategy
        outer_threshold = 0.005  # ±0.5% boundary
        inner_targets = [-0.0025, 0.0, 0.0025]  # -0.25%, 0%, +0.25%
        tolerance = 0.0001  # Floating-point precision tolerance
        
        for val in shock_values:
            if abs(val) >= outer_threshold:
                # Sparse outer regions: show all labels
                marks[val] = format_shock_value_for_display(val, shock_type)
            else:
                # Dense inner region: only specific target values
                if any(abs(val - target) < tolerance for target in inner_targets):
                    marks[val] = format_shock_value_for_display(val, shock_type)
                else:
                    marks[val] = ""  # Tick exists but no label
    
    return marks


def _create_tooltip_config(shock_type: str) -> Dict:
    """
    Create tooltip configuration that matches label formatting.
    
    Args:
        shock_type: Type of shock for formatting
        
    Returns:
        Dictionary with tooltip configuration
    """
    if shock_type == "percentage":
        # For percentage mode, use a basic tooltip configuration
        return {
            "placement": "bottom",
            "always_visible": False,
            "template": "{value:.1%}"  # Try percentage format
        }
    else:  # absolute_usd
        # For absolute mode, use currency format
        return {
            "placement": "bottom",
            "always_visible": False,
            "template": "${value:.2f}"  # Try currency format
        }


def create_dashboard_layout():
    """Create the main dashboard layout with new design."""
    return Container(
        id="main-layout",
        children=[
            # Title Section
            html.Div([
                html.H1(
                    "ActantEOD Dashboard", 
                    style={
                        "textAlign": "center", 
                        "color": default_theme.primary, 
                        "marginBottom": "10px",
                        "fontSize": "2.5em",
                        "fontWeight": "600"
                    }
                ),
                # Load data section
                Container(
                    id="load-data-container",
                    children=[
                        html.Div([
                            Button(
                                id="load-data-button",
                                label="Load Latest Actant Data",
                                theme=default_theme,
                                style={"marginRight": "10px"}
                            ).render(),
                            Button(
                                id="load-pm-button", 
                                label="Load PM Data",
                                theme=default_theme,
                                style={"marginRight": "20px"}
                            ).render(),
                            html.Div(
                                id="current-file-display",
                                children="No data loaded",
                                style={
                                    "color": default_theme.text_light,
                                    "fontSize": "14px",
                                    "display": "inline-block",
                                    "verticalAlign": "middle"
                                }
                            )
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "marginBottom": "20px"
                        })
                    ],
                    style={
                        "backgroundColor": default_theme.panel_bg,
                        "padding": "15px",
                        "borderRadius": "5px",
                        "marginBottom": "20px"
                    }
                ).render()
            ]),
            
            # Top Controls Grid
            html.Div(
                id="controls-section",
                children=[
                    Grid(
                        id="controls-grid",
                        children=[
                            # Scenarios Column
                            (Container(
                                id="scenarios-container",
                                children=[
                                    html.H4("Scenarios", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    ListBox(
                                        id="scenario-listbox",
                                        options=[],
                                        value=[],
                                        multi=True,
                                        theme=default_theme,
                                        style={"height": "200px"}
                                    ).render()
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 3}),
                            
                            # Metric Categories Column
                            (Container(
                                id="categories-container",
                                children=[
                                    html.H4("Metric Categories", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    html.Div(id="metric-categories-container")
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 4}),
                            
                            # Filters Column
                            (Container(
                                id="filters-container",
                                children=[
                                    html.H4("Filters", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "10px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    html.P("Prefix Filter:", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "5px",
                                        "fontSize": "14px"
                                    }),
                                    ListBox(
                                        id="prefix-filter-listbox",
                                        options=[
                                            {"label": "All", "value": "all"},
                                            {"label": "Base (no prefix)", "value": "base"},
                                            {"label": "AB prefixed", "value": "ab"},
                                            {"label": "BS prefixed", "value": "bs"},
                                            {"label": "PA prefixed", "value": "pa"}
                                        ],
                                        value="all",
                                        multi=False,
                                        theme=default_theme,
                                        style={"height": "120px"}
                                    ).render()
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 2}),
                            
                            # View Options Column
                            (Container(
                                id="toggles-container",
                                children=[
                                    html.H4("View Options", style={
                                        "color": default_theme.text_light,
                                        "marginBottom": "15px",
                                        "fontSize": "16px",
                                        "fontWeight": "500"
                                    }),
                                    
                                    # Horizontal row of button pairs
                                    html.Div([
                                        # Graph/Table toggle
                                        html.Div([
                                            html.P("View:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="view-mode-graph-btn",
                                                    label="Graph",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="view-mode-table-btn",
                                                    label="Table",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"flex": "1", "textAlign": "center"}),
                                        
                                        # Absolute/Percentage toggle
                                        html.Div([
                                            html.P("Values:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="percentage-absolute-btn",
                                                    label="Absolute",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="percentage-percentage-btn",
                                                    label="Percentage",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"flex": "1", "textAlign": "center"}),
                                        
                                        # Scenario/Metric View toggle
                                        html.Div([
                                            html.P("Mode:", style={
                                                "color": default_theme.text_light, 
                                                "marginBottom": "5px", 
                                                "fontSize": "14px",
                                                "textAlign": "center"
                                            }),
                                            html.Div([
                                                Button(
                                                    id="viz-mode-scenario-btn",
                                                    label="Scenario",
                                                    theme=default_theme,
                                                    n_clicks=1,  # Default selected
                                                    style={
                                                        'borderTopRightRadius': '0',
                                                        'borderBottomRightRadius': '0',
                                                        'borderRight': 'none',
                                                        'backgroundColor': default_theme.primary
                                                    }
                                                ).render(),
                                                Button(
                                                    id="viz-mode-metric-btn",
                                                    label="Metric",
                                                    theme=default_theme,
                                                    n_clicks=0,
                                                    style={
                                                        'borderTopLeftRadius': '0',
                                                        'borderBottomLeftRadius': '0',
                                                        'backgroundColor': default_theme.panel_bg
                                                    }
                                                ).render()
                                            ], style={"display": "flex", "justifyContent": "center"})
                                        ], style={"flex": "1", "textAlign": "center"})
                                        
                                    ], style={
                                        "display": "flex", 
                                        "justifyContent": "space-between",
                                        "gap": "20px"
                                    })
                                ],
                                style={
                                    "backgroundColor": default_theme.panel_bg,
                                    "padding": "15px",
                                    "borderRadius": "5px"
                                }
                            ), {"width": 3})
                        ]
                    ).render()
                ],
                style={"marginBottom": "20px"}
            ),
            
            # Bottom Visualization Grid
            html.Div(
                id="visualization-section",
                children=[
                    html.Div(id="dynamic-visualization-grid")
                ]
            ),
            
            # Data stores
            dcc.Store(id="data-loaded-store", data=False),
            dcc.Store(id="pm-data-loaded-store", data=False),
            dcc.Store(id="metric-categories-store", data={}),
            dcc.Store(id="selected-metrics-store", data=[]),
            dcc.Store(id="shock-ranges-store", data={}),
            dcc.Store(id="toggle-states-store", data={
                "is_table_view": False,
                "is_percentage": False,
                "is_metric_view": False
            })
        ],
        theme=default_theme,
        style={"padding": "20px", "backgroundColor": default_theme.base_bg, "minHeight": "100vh"}
    )


# Set app layout
app.layout = html.Div(
    children=[create_dashboard_layout().render()],
    style={
        "backgroundColor": default_theme.base_bg,
        "padding": "20px", 
        "minHeight": "100vh",
        "fontFamily": "Inter, sans-serif"
    }
)


@app.callback(
    [Output("current-file-display", "children"),
     Output("data-loaded-store", "data"),
     Output("scenario-listbox", "options"),
     Output("metric-categories-store", "data")],
    Input("load-data-button", "n_clicks"),
    prevent_initial_call=False
)
def load_data(n_clicks):
    """Load the most recent JSON file and populate filter options."""
    try:
        json_file = get_most_recent_json_file()
        
        if json_file is None:
            return "No valid JSON files found", False, [], {}
        
        success = data_service.load_data_from_json(json_file)
        
        if not success:
            return f"Failed to load {json_file.name}", False, [], {}
        
        # Get metadata for display
        metadata = get_json_file_metadata(json_file)
        file_display = (
            f"Loaded: {metadata['filename']} "
            f"({metadata['size_mb']:.1f} MB, {metadata['scenario_count']} scenarios)"
        )
        
        # Get filter options
        scenarios = data_service.get_scenario_headers()
        scenario_options = [{"label": s, "value": s} for s in scenarios]
        
        # Get categorized metrics
        metric_categories = data_service.categorize_metrics()
        
        logger.info(f"Successfully loaded data from {json_file.name}")
        return file_display, True, scenario_options, metric_categories
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return f"Error loading data: {str(e)}", False, [], {}


@app.callback(
    Output("metric-categories-container", "children"),
    [Input("metric-categories-store", "data"),
     Input("prefix-filter-listbox", "value")],
    prevent_initial_call=True
)
def update_metric_categories(metric_categories, prefix_filter):
    """Create metric category checkboxes and listboxes."""
    if not metric_categories:
        return html.Div("No metrics available", style={"color": default_theme.text_light})
    
    # Define all expected categories in order
    all_categories = ["Delta", "Epsilon", "Gamma", "Theta", "Vega", "Zeta", "Vol", "OEV", "Th PnL", "Misc"]
    category_components = []
    
    for category in all_categories:
        # Get metrics for this category (empty list if category doesn't exist)
        metrics = metric_categories.get(category, [])
        
        # Filter metrics by prefix
        filtered_metrics = data_service.filter_metrics_by_prefix(metrics, prefix_filter)
        
        # Determine if category should be disabled
        is_disabled = len(filtered_metrics) == 0
        
        # Create options for the listbox
        metric_options = [{"label": m, "value": m} for m in filtered_metrics]
        
        # Style for disabled categories
        checkbox_style = {"marginBottom": "5px"}
        if is_disabled:
            checkbox_style["opacity"] = "0.5"
        
        category_div = html.Div([
            # Category checkbox
            Checkbox(
                id=f"category-{category.lower().replace(' ', '-')}-checkbox",
                options=[{"label": f"{category} ({len(filtered_metrics)} metrics)", "value": category}],
                value=[],
                theme=default_theme,
                style=checkbox_style
            ).render(),
            
            # Metrics listbox (initially collapsed)
            html.Div([
                ListBox(
                    id=f"category-{category.lower().replace(' ', '-')}-listbox",
                    options=metric_options if not is_disabled else [{"label": "No metrics available", "value": "", "disabled": True}],
                    value=[],
                    multi=True,
                    theme=default_theme,
                    style={
                        "height": "100px", 
                        "fontSize": "12px",
                        "opacity": "0.5" if is_disabled else "1.0",
                        "pointerEvents": "none" if is_disabled else "auto"
                    }
                ).render()
            ], id=f"category-{category.lower().replace(' ', '-')}-container",
               style={"display": "none", "marginLeft": "20px", "marginBottom": "10px"})
        ], style={"marginBottom": "5px"})
        
        category_components.append(category_div)
    
    return category_components


@app.callback(
    [Output("category-delta-container", "style", allow_duplicate=True),
     Output("category-epsilon-container", "style", allow_duplicate=True),
     Output("category-gamma-container", "style", allow_duplicate=True),
     Output("category-theta-container", "style", allow_duplicate=True),
     Output("category-vega-container", "style", allow_duplicate=True),
     Output("category-zeta-container", "style", allow_duplicate=True),
     Output("category-vol-container", "style", allow_duplicate=True),
     Output("category-oev-container", "style", allow_duplicate=True),
     Output("category-th-pnl-container", "style", allow_duplicate=True),
     Output("category-misc-container", "style", allow_duplicate=True)],
    [Input("category-delta-checkbox", "value"),
     Input("category-epsilon-checkbox", "value"),
     Input("category-gamma-checkbox", "value"),
     Input("category-theta-checkbox", "value"),
     Input("category-vega-checkbox", "value"),
     Input("category-zeta-checkbox", "value"),
     Input("category-vol-checkbox", "value"),
     Input("category-oev-checkbox", "value"),
     Input("category-th-pnl-checkbox", "value"),
     Input("category-misc-checkbox", "value")],
    prevent_initial_call=True
)
def toggle_category_visibility(*checkbox_values):
    """Toggle visibility of metric listboxes based on checkbox state."""
    styles = []
    
    for value in checkbox_values:
        if value:  # Checkbox is checked
            styles.append({"display": "block", "marginLeft": "20px", "marginBottom": "10px"})
        else:  # Checkbox is unchecked
            styles.append({"display": "none", "marginLeft": "20px", "marginBottom": "10px"})
    
    return styles


@app.callback(
    Output("selected-metrics-store", "data"),
    [Input("category-delta-listbox", "value"),
     Input("category-epsilon-listbox", "value"),
     Input("category-gamma-listbox", "value"),
     Input("category-theta-listbox", "value"),
     Input("category-vega-listbox", "value"),
     Input("category-zeta-listbox", "value"),
     Input("category-vol-listbox", "value"),
     Input("category-oev-listbox", "value"),
     Input("category-th-pnl-listbox", "value"),
     Input("category-misc-listbox", "value"),
     Input("category-delta-checkbox", "value"),
     Input("category-epsilon-checkbox", "value"),
     Input("category-gamma-checkbox", "value"),
     Input("category-theta-checkbox", "value"),
     Input("category-vega-checkbox", "value"),
     Input("category-zeta-checkbox", "value"),
     Input("category-vol-checkbox", "value"),
     Input("category-oev-checkbox", "value"),
     Input("category-th-pnl-checkbox", "value"),
     Input("category-misc-checkbox", "value")],
    prevent_initial_call=True
)
def collect_selected_metrics(*inputs):
    """Collect selected metrics from category listboxes, but only if the category checkbox is checked."""
    # Split inputs into listbox values and checkbox states
    num_categories = 10
    listbox_values = inputs[:num_categories]
    checkbox_values = inputs[num_categories:]
    
    all_selected_metrics = []
    
    for metrics, checkbox_state in zip(listbox_values, checkbox_values):
        # Only include metrics if the category checkbox is checked AND metrics are selected
        if checkbox_state and metrics:  # checkbox_state is truthy (checked) and metrics exist
            all_selected_metrics.extend(metrics)
    
    return all_selected_metrics


# Helper functions for button-based toggles
def _get_toggle_state_from_buttons(ctx, button_id_false, button_id_true, default_false=True):
    """
    Helper function to determine toggle state from button clicks.
    
    Args:
        ctx: Dash callback context
        button_id_false: ID of button for False state
        button_id_true: ID of button for True state
        default_false: Default state when no button has been clicked
        
    Returns:
        Boolean state based on last clicked button
    """
    if not ctx.triggered:
        return default_false
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == button_id_true:
        return True
    elif triggered_id == button_id_false:
        return False
    else:
        return default_false


@app.callback(
    Output("dynamic-visualization-grid", "children"),
    [Input("scenario-listbox", "value"),
     Input("selected-metrics-store", "data"),
     Input("toggle-states-store", "data")],
    State("data-loaded-store", "data"),
    prevent_initial_call=True
)
def create_dynamic_visualization_grid(selected_scenarios, selected_metrics, toggle_states, data_loaded):
    """Create dynamic grid of visualizations based on selected scenarios and visualization mode."""
    if not data_loaded or not selected_scenarios or not selected_metrics:
        return html.Div(
            "Select scenarios and metrics to view visualizations",
            style={
                "textAlign": "center",
                "color": default_theme.text_light,
                "padding": "40px",
                "fontSize": "18px"
            }
        )
    
    # Get toggle states from store (single source of truth)
    is_table_view = toggle_states.get("is_table_view", False)
    is_percentage = toggle_states.get("is_percentage", False)
    is_metric_view = toggle_states.get("is_metric_view", False)
    
    # Branch based on visualization mode
    if is_metric_view:
        return _create_metric_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage)
    else:
        return _create_scenario_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage)


@app.callback(
    [Output("current-file-display", "children", allow_duplicate=True),
     Output("pm-data-loaded-store", "data")],
    Input("load-pm-button", "n_clicks"),
    prevent_initial_call=True
)
def load_pm_data(n_clicks):
    """Load Pricing Monkey data via browser automation."""
    if n_clicks == 0:
        raise PreventUpdate
    
    try:
        logger.info("Starting Pricing Monkey data loading")
        success = data_service.load_pricing_monkey_data()
        
        if success:
            return "✅ PM Data loaded successfully", True
        else:
            return "❌ Failed to load PM data", False
            
    except Exception as e:
        logger.error(f"Error loading PM data: {e}")
        return f"❌ Error loading PM data: {str(e)}", False


# Callback to update shared toggle states
@app.callback(
    Output("toggle-states-store", "data"),
    [Input("view-mode-graph-btn", "n_clicks"),
     Input("view-mode-table-btn", "n_clicks"),
     Input("percentage-absolute-btn", "n_clicks"),
     Input("percentage-percentage-btn", "n_clicks"),
     Input("viz-mode-scenario-btn", "n_clicks"),
     Input("viz-mode-metric-btn", "n_clicks")],
    State("toggle-states-store", "data"),
    prevent_initial_call=False
)
def update_toggle_states_store(graph_btn, table_btn, abs_btn, pct_btn, scenario_btn, metric_btn, current_states):
    """Update shared toggle states store based on button clicks."""
    ctx = callback_context
    
    # Initialize with current states or defaults
    states = current_states or {
        "is_table_view": False,
        "is_percentage": False,
        "is_metric_view": False
    }
    
    # Only update the specific toggle that was clicked
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if triggered_id in ["view-mode-graph-btn", "view-mode-table-btn"]:
            states["is_table_view"] = _get_toggle_state_from_buttons(ctx, "view-mode-graph-btn", "view-mode-table-btn", default_false=False)
        elif triggered_id in ["percentage-absolute-btn", "percentage-percentage-btn"]:
            states["is_percentage"] = _get_toggle_state_from_buttons(ctx, "percentage-absolute-btn", "percentage-percentage-btn", default_false=False)
        elif triggered_id in ["viz-mode-scenario-btn", "viz-mode-metric-btn"]:
            states["is_metric_view"] = _get_toggle_state_from_buttons(ctx, "viz-mode-scenario-btn", "viz-mode-metric-btn", default_false=False)
    
    return states


# Dynamic callbacks for scenario-specific visualizations
@app.callback(
    Output({"type": "scenario-graph", "scenario": MATCH}, "figure"),
    [Input("selected-metrics-store", "data"),
     Input("toggle-states-store", "data"),
     Input({"type": "range-slider", "scenario": MATCH}, "value")],
    State({"type": "scenario-graph", "scenario": MATCH}, "id"),
    State("data-loaded-store", "data"),
    prevent_initial_call=False
)
def update_scenario_graph(selected_metrics, toggle_states, range_values, graph_id, data_loaded):
    """Update graph for a specific scenario based on selected metrics and range."""
    if not data_loaded or not selected_metrics or not range_values:
        return {
            'data': [],
            'layout': go.Layout(
                title="Select metrics to visualize",
                xaxis_title="Shock Value",
                yaxis_title="Metric Value",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }
    
    try:
        scenario = graph_id["scenario"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get filtered data for this scenario within the range
        shock_ranges = {scenario: range_values}
        df = data_service.get_filtered_data_with_range(
            scenario_headers=[scenario],
            shock_types=[shock_type],  # Filter by shock type
            shock_ranges=shock_ranges,
            metrics=selected_metrics
        )
        
        if df.empty:
            return {
                'data': [],
                'layout': go.Layout(
                    title=f"No data for {scenario}",
                    xaxis_title="Shock Value", 
                    yaxis_title="Metric Value",
                    plot_bgcolor=default_theme.base_bg,
                    paper_bgcolor=default_theme.panel_bg,
                    font_color=default_theme.text_light,
                    height=400
                )
            }
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        
        for i, metric in enumerate(selected_metrics):
            if metric in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['shock_value'],
                    y=df[metric],
                    mode='lines+markers',
                    name=metric,
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title=f"Metrics for {scenario}",
            xaxis_title="Shock Value",
            yaxis_title="Metric Value",
            plot_bgcolor=default_theme.base_bg,
            paper_bgcolor=default_theme.panel_bg,
            font_color=default_theme.text_light,
            xaxis=dict(
                showgrid=True, 
                gridcolor=default_theme.secondary,
                # Let Plotly handle tick spacing automatically
            ),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400,
            margin=dict(l=60, r=20, t=60, b=50),
            legend=dict(
                bgcolor=default_theme.panel_bg,
                bordercolor=default_theme.secondary,
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating scenario graph: {e}")
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Error: {str(e)}",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }


@app.callback(
    [Output({"type": "scenario-table", "scenario": MATCH}, "data"),
     Output({"type": "scenario-table", "scenario": MATCH}, "columns")],
    [Input("selected-metrics-store", "data"),
     Input("toggle-states-store", "data"),
     Input({"type": "range-slider", "scenario": MATCH}, "value")],
    State({"type": "scenario-table", "scenario": MATCH}, "id"),
    State("data-loaded-store", "data"),
    prevent_initial_call=False
)
def update_scenario_table(selected_metrics, toggle_states, range_values, table_id, data_loaded):
    """Update table for a specific scenario based on selected metrics and range."""
    if not data_loaded or not selected_metrics or not range_values:
        return [], []
    
    try:
        scenario = table_id["scenario"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Get filtered data for this scenario within the range
        shock_ranges = {scenario: range_values}
        df = data_service.get_filtered_data_with_range(
            scenario_headers=[scenario],
            shock_types=[shock_type],  # Filter by shock type
            shock_ranges=shock_ranges,
            metrics=selected_metrics
        )
        
        if df.empty:
            return [], []
        
        # Select relevant columns for display
        display_columns = ['shock_value'] + selected_metrics
        display_df = df[display_columns].copy()
        
        # Apply shock value formatting based on percentage toggle
        if is_percentage:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "percentage")
            )
        else:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "absolute_usd")
            )
        
        # Create columns configuration
        columns = []
        for col in display_df.columns:
            column_config = {"name": col, "id": col}
            
            # Format numeric columns
            if display_df[col].dtype in ['float64', 'int64']:
                column_config["type"] = "numeric"
                column_config["format"] = {"specifier": ",.4f"}
            
            columns.append(column_config)
        
        return display_df.to_dict('records'), columns
        
    except Exception as e:
        logger.error(f"Error updating scenario table: {e}")
        return [], []


def _create_scenario_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage):
    """Create scenario-based visualization grid (current behavior - each scenario = one graph)."""
    # Calculate grid layout
    num_scenarios = len(selected_scenarios)
    if num_scenarios == 1:
        columns = 1
    elif num_scenarios <= 4:
        columns = 2
    else:
        columns = 3
    
    grid_children = []
    
    # Determine shock type based on percentage toggle
    shock_type = "percentage" if is_percentage else "absolute_usd"
    
    for i, scenario in enumerate(selected_scenarios):
        # Get shock range for this scenario with specific shock type
        min_shock, max_shock = data_service.get_shock_range_by_scenario(scenario, shock_type)
        
        # Get distinct shock values for tick marks
        shock_values = data_service.get_distinct_shock_values_by_scenario_and_type(scenario, shock_type)
        
        # Create marks dictionary for range slider
        if shock_values:
            marks = _create_density_aware_marks(shock_values, shock_type)
        else:
            marks = None
        
        # Create visualization container for this scenario
        scenario_container = Container(
            id=f"scenario-container-{scenario.replace(' ', '-').replace('.', '-')}",
            children=[
                html.H5(
                    f"Scenario: {scenario}",
                    style={
                        "color": default_theme.text_light,
                        "textAlign": "center",
                        "marginBottom": "15px",
                        "fontSize": "16px",
                        "fontWeight": "500"
                    }
                ),
                
                # Range slider for this scenario
                html.Div([
                    html.P("Shock Range:", style={
                        "color": default_theme.text_light,
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    RangeSlider(
                        id={"type": "range-slider", "scenario": scenario},
                        min=min_shock,
                        max=max_shock,
                        value=[min_shock, max_shock],
                        marks=marks,
                        tooltip=_create_tooltip_config(shock_type),
                        theme=default_theme
                    ).render()
                ], style={"marginBottom": "15px"}),
                
                # Visualization area (graph or table)
                html.Div(
                    id=f"viz-container-{scenario.replace(' ', '-').replace('.', '-')}",
                    children=[
                        Graph(
                            id={"type": "scenario-graph", "scenario": scenario},
                            figure={
                                'data': [],
                                'layout': go.Layout(
                                    title=f"Metrics for {scenario}",
                                    xaxis_title="Shock Value",
                                    yaxis_title="Metric Value",
                                    plot_bgcolor=default_theme.base_bg,
                                    paper_bgcolor=default_theme.panel_bg,
                                    font_color=default_theme.text_light,
                                    height=400
                                )
                            },
                            theme=default_theme,
                            style={"height": "400px", "display": "block" if not is_table_view else "none"}
                        ).render(),
                        html.Div([
                            DataTable(
                                id={"type": "scenario-table", "scenario": scenario},
                                data=[],
                                columns=[],
                                theme=default_theme,
                                page_size=10,
                                style_table={"height": "400px", "overflowY": "auto"}
                            ).render()
                        ], id={"type": "scenario-table-container", "scenario": scenario}, style={"display": "none" if not is_table_view else "block"})
                    ]
                )
            ],
            style={
                "backgroundColor": default_theme.panel_bg,
                "padding": "15px",
                "borderRadius": "5px",
                "marginBottom": "20px"
            }
        )
        
        # Calculate column width based on number of scenarios
        width = 12 // columns if num_scenarios % columns == 0 else 12 // columns
        if i == num_scenarios - 1 and num_scenarios % columns != 0:
            width = 12 - (num_scenarios - 1) * (12 // columns)
        
        grid_children.append((scenario_container, {"width": width}))
    
    return Grid(id="visualization-grid", children=grid_children).render()


def _create_metric_view_grid(selected_scenarios, selected_metrics, is_table_view, is_percentage):
    """Create metric-based visualization grid (new behavior - each metric = one graph)."""
    # Calculate grid layout
    num_metrics = len(selected_metrics)
    if num_metrics == 1:
        columns = 1
    elif num_metrics <= 4:
        columns = 2
    else:
        columns = 3
    
    grid_children = []
    
    # Determine shock type based on percentage toggle
    shock_type = "percentage" if is_percentage else "absolute_usd"
    
    for i, metric in enumerate(selected_metrics):
        # Calculate global shock range across all selected scenarios for this metric
        min_shock, max_shock = _get_global_shock_range_for_metric(selected_scenarios, shock_type)
        
        # Get global shock values across all scenarios for consistent tick marks
        global_shock_values = _get_global_shock_values_for_metric(selected_scenarios, shock_type)
        
        # Create marks dictionary for range slider
        if global_shock_values:
            marks = _create_density_aware_marks(global_shock_values, shock_type)
        else:
            marks = None
        
        # Create visualization container for this metric
        metric_container = Container(
            id=f"metric-container-{metric.replace(' ', '-').replace('.', '-')}",
            children=[
                html.H5(
                    f"Metric: {metric}",
                    style={
                        "color": default_theme.text_light,
                        "textAlign": "center",
                        "marginBottom": "15px",
                        "fontSize": "16px",
                        "fontWeight": "500"
                    }
                ),
                
                # Range slider for this metric (global range)
                html.Div([
                    html.P("Shock Range:", style={
                        "color": default_theme.text_light,
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    RangeSlider(
                        id={"type": "metric-range-slider", "metric": metric},
                        min=min_shock,
                        max=max_shock,
                        value=[min_shock, max_shock],
                        marks=marks,
                        tooltip=_create_tooltip_config(shock_type),
                        theme=default_theme
                    ).render()
                ], style={"marginBottom": "15px"}),
                
                # Visualization area (graph or table)
                html.Div(
                    id=f"metric-viz-container-{metric.replace(' ', '-').replace('.', '-')}",
                    children=[
                        Graph(
                            id={"type": "metric-graph", "metric": metric},
                            figure={
                                'data': [],
                                'layout': go.Layout(
                                    title=f"Scenarios for {metric}",
                                    xaxis_title="Shock Value",
                                    yaxis_title="Metric Value",
                                    plot_bgcolor=default_theme.base_bg,
                                    paper_bgcolor=default_theme.panel_bg,
                                    font_color=default_theme.text_light,
                                    height=400
                                )
                            },
                            theme=default_theme,
                            style={"height": "400px", "display": "block" if not is_table_view else "none"}
                        ).render(),
                        html.Div([
                            DataTable(
                                id={"type": "metric-table", "metric": metric},
                                data=[],
                                columns=[],
                                theme=default_theme,
                                page_size=10,
                                style_table={"height": "400px", "overflowY": "auto"}
                            ).render()
                        ], id={"type": "metric-table-container", "metric": metric}, style={"display": "none" if not is_table_view else "block"})
                    ]
                )
            ],
            style={
                "backgroundColor": default_theme.panel_bg,
                "padding": "15px",
                "borderRadius": "5px",
                "marginBottom": "20px"
            }
        )
        
        # Calculate column width based on number of metrics
        width = 12 // columns if num_metrics % columns == 0 else 12 // columns
        if i == num_metrics - 1 and num_metrics % columns != 0:
            width = 12 - (num_metrics - 1) * (12 // columns)
        
        grid_children.append((metric_container, {"width": width}))
    
    return Grid(id="metric-visualization-grid", children=grid_children).render()


def _get_global_shock_range_for_metric(selected_scenarios, shock_type):
    """Calculate global shock range across all selected scenarios for a given shock type."""
    global_min = float('inf')
    global_max = float('-inf')
    
    for scenario in selected_scenarios:
        min_shock, max_shock = data_service.get_shock_range_by_scenario(scenario, shock_type)
        global_min = min(global_min, min_shock)
        global_max = max(global_max, max_shock)
    
    return global_min, global_max


def _get_global_shock_values_for_metric(selected_scenarios, shock_type):
    """Get unique shock values across all selected scenarios for consistent tick marks."""
    all_shock_values = set()
    
    for scenario in selected_scenarios:
        scenario_shock_values = data_service.get_distinct_shock_values_by_scenario_and_type(scenario, shock_type)
        all_shock_values.update(scenario_shock_values)
    
    return sorted(list(all_shock_values))


# Dynamic callbacks for metric-specific visualizations
@app.callback(
    Output({"type": "metric-graph", "metric": MATCH}, "figure"),
    [Input("scenario-listbox", "value"),
     Input("toggle-states-store", "data"),
     Input({"type": "metric-range-slider", "metric": MATCH}, "value")],
    State({"type": "metric-graph", "metric": MATCH}, "id"),
    State("data-loaded-store", "data"),
    prevent_initial_call=False
)
def update_metric_graph(selected_scenarios, toggle_states, range_values, graph_id, data_loaded):
    """Update graph for a specific metric based on selected scenarios and range."""
    if not data_loaded or not selected_scenarios or not range_values:
        return {
            'data': [],
            'layout': go.Layout(
                title="Select scenarios to visualize",
                xaxis_title="Shock Value",
                yaxis_title="Metric Value",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }
    
    try:
        metric = graph_id["metric"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Create global shock range for this metric across all scenarios
        global_shock_ranges = {}
        for scenario in selected_scenarios:
            global_shock_ranges[scenario] = range_values  # Same range for all scenarios
        
        # Get filtered data for all scenarios within the range
        df = data_service.get_filtered_data_with_range(
            scenario_headers=selected_scenarios,
            shock_types=[shock_type],  # Filter by shock type
            shock_ranges=global_shock_ranges,
            metrics=[metric]
        )
        
        if df.empty:
            return {
                'data': [],
                'layout': go.Layout(
                    title=f"No data for {metric}",
                    xaxis_title="Shock Value", 
                    yaxis_title="Metric Value",
                    plot_bgcolor=default_theme.base_bg,
                    paper_bgcolor=default_theme.panel_bg,
                    font_color=default_theme.text_light,
                    height=400
                )
            }
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        
        # Add one trace per scenario for this metric
        for i, scenario in enumerate(selected_scenarios):
            scenario_df = df[df['scenario_header'] == scenario]
            if not scenario_df.empty and metric in scenario_df.columns:
                fig.add_trace(go.Scatter(
                    x=scenario_df['shock_value'],
                    y=scenario_df[metric],
                    mode='lines+markers',
                    name=scenario,
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title=f"Scenarios for {metric}",
            xaxis_title="Shock Value",
            yaxis_title="Metric Value",
            plot_bgcolor=default_theme.base_bg,
            paper_bgcolor=default_theme.panel_bg,
            font_color=default_theme.text_light,
            xaxis=dict(
                showgrid=True, 
                gridcolor=default_theme.secondary,
            ),
            yaxis=dict(showgrid=True, gridcolor=default_theme.secondary),
            height=400,
            margin=dict(l=60, r=20, t=60, b=50),
            legend=dict(
                bgcolor=default_theme.panel_bg,
                bordercolor=default_theme.secondary,
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating metric graph: {e}")
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Error: {str(e)}",
                plot_bgcolor=default_theme.base_bg,
                paper_bgcolor=default_theme.panel_bg,
                font_color=default_theme.text_light,
                height=400
            )
        }


@app.callback(
    [Output({"type": "metric-table", "metric": MATCH}, "data"),
     Output({"type": "metric-table", "metric": MATCH}, "columns")],
    [Input("scenario-listbox", "value"),
     Input("toggle-states-store", "data"),
     Input({"type": "metric-range-slider", "metric": MATCH}, "value")],
    State({"type": "metric-table", "metric": MATCH}, "id"),
    State("data-loaded-store", "data"),
    prevent_initial_call=False
)
def update_metric_table(selected_scenarios, toggle_states, range_values, table_id, data_loaded):
    """Update table for a specific metric based on selected scenarios and range."""
    if not data_loaded or not selected_scenarios or not range_values:
        return [], []
    
    try:
        metric = table_id["metric"]
        is_percentage = toggle_states.get("is_percentage", False)
        
        # Determine shock type based on percentage toggle
        shock_type = "percentage" if is_percentage else "absolute_usd"
        
        # Create global shock range for this metric across all scenarios
        global_shock_ranges = {}
        for scenario in selected_scenarios:
            global_shock_ranges[scenario] = range_values  # Same range for all scenarios
        
        # Get filtered data for all scenarios within the range
        df = data_service.get_filtered_data_with_range(
            scenario_headers=selected_scenarios,
            shock_types=[shock_type],  # Filter by shock type
            shock_ranges=global_shock_ranges,
            metrics=[metric]
        )
        
        if df.empty:
            return [], []
        
        # Pivot data: shock_value as index, scenarios as columns, metric values as data
        pivot_df = df.pivot_table(
            index='shock_value', 
            columns='scenario_header', 
            values=metric,
            fill_value=np.nan
        )
        
        # Flatten column names to "metric-scenario" format
        pivot_df.columns = [f"{metric}-{scenario}" for scenario in pivot_df.columns]
        
        # Reset index to make shock_value a regular column
        display_df = pivot_df.reset_index()
        
        # Apply shock value formatting based on percentage toggle
        if is_percentage:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "percentage")
            )
        else:
            display_df['shock_value'] = display_df['shock_value'].apply(
                lambda x: format_shock_value_for_display(x, "absolute_usd")
            )
        
        # Create columns configuration
        columns = []
        for col in display_df.columns:
            column_config = {"name": col, "id": col}
            
            # Format numeric columns
            if display_df[col].dtype in ['float64', 'int64']:
                column_config["type"] = "numeric"
                column_config["format"] = {"specifier": ",.4f"}
            
            columns.append(column_config)
        
        return display_df.to_dict('records'), columns
        
    except Exception as e:
        logger.error(f"Error updating metric table: {e}")
        return [], []


# Button style callbacks for visual feedback
@app.callback(
    [Output("view-mode-graph-btn", "style"),
     Output("view-mode-table-btn", "style")],
    [Input("view-mode-graph-btn", "n_clicks"),
     Input("view-mode-table-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_view_mode_button_styles(graph_clicks, table_clicks):
    """Update button styles for view mode toggle."""
    ctx = callback_context
    
    # Default to graph view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "view-mode-graph-btn":
        # Graph selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Table selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )


@app.callback(
    [Output("percentage-absolute-btn", "style"),
     Output("percentage-percentage-btn", "style")],
    [Input("percentage-absolute-btn", "n_clicks"),
     Input("percentage-percentage-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_percentage_button_styles(abs_clicks, pct_clicks):
    """Update button styles for percentage toggle."""
    ctx = callback_context
    
    # Default to absolute view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "percentage-absolute-btn":
        # Absolute selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Percentage selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )


@app.callback(
    [Output("viz-mode-scenario-btn", "style"),
     Output("viz-mode-metric-btn", "style")],
    [Input("viz-mode-scenario-btn", "n_clicks"),
     Input("viz-mode-metric-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_viz_mode_button_styles(scenario_clicks, metric_clicks):
    """Update button styles for visualization mode toggle."""
    ctx = callback_context
    
    # Default to scenario view
    if not ctx.triggered:
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == "viz-mode-scenario-btn":
        # Scenario selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.primary},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.panel_bg}
        )
    else:
        # Metric selected
        return (
            {'borderTopRightRadius': '0', 'borderBottomRightRadius': '0', 'borderRight': 'none', 
             'backgroundColor': default_theme.panel_bg},
            {'borderTopLeftRadius': '0', 'borderBottomLeftRadius': '0', 'backgroundColor': default_theme.primary}
        )


if __name__ == "__main__":
    app.run(debug=True, port=8050) 