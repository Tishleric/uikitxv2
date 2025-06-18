"""Simple Observatory Dashboard Views"""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# Import wrapped components from lib/components
from lib.components import Container, DataTable, Button, Grid
from lib.components.themes import default_theme


def create_observatory_content():
    """
    Create simple Observatory dashboard content that can be embedded in main app.
    This follows the same pattern as ActantPnL dashboard.
    """
    # No mock data - will be populated from database
    test_data = []
    
    # Define the main columns as requested
    columns = [
        {"name": "Process", "id": "process", "type": "text"},
        {"name": "Data", "id": "data", "type": "text"},  # Input variable name
        {"name": "Data Type", "id": "data_type", "type": "text"},  # input/output
        {"name": "Data Value", "id": "data_value", "type": "text"},  # Actual value
        {"name": "Timestamp", "id": "timestamp", "type": "text"},
        {"name": "Status", "id": "status", "type": "text"},
        {"name": "Exception", "id": "exception", "type": "text"}
    ]
    
    # Create header
    header = Container(
        id="observatory-header",
        children=[
            Grid(
                id="header-grid",
                children=[
                    # Title section
                    (Container(
                        id="observatory-title-container",
                        children=[
                            html.H2(
                                "Observatory Dashboard",
                                style={
                                    "color": default_theme.text_light,
                                    "marginBottom": "5px",
                                    "fontSize": "24px"
                                }
                            ),
                            html.P(
                                "Monitor system performance and traces",
                                style={
                                    "color": default_theme.text_subtle,
                                    "fontSize": "14px"
                                }
                            )
                        ]
                    ).render(), {"xs": 12, "md": 8}),
                    
                    # Refresh button section
                    (Container(
                        id="observatory-button-container",
                        children=[
                            Button(
                                id="observatory-refresh-button",
                                label="Refresh Data",
                                theme=default_theme,
                                n_clicks=0,
                                style={
                                    "width": "100%",
                                    "marginTop": "10px"
                                }
                            ).render()
                        ],
                        style={
                            "textAlign": "right"
                        }
                    ).render(), {"xs": 12, "md": 4})
                ]
            ).render()
        ],
        style={
            "backgroundColor": default_theme.panel_bg,
            "padding": "20px",
            "borderRadius": "5px",
            "marginBottom": "20px"
        }
    ).render()
    
    # Create main content area with DataTable
    content = Container(
        id="observatory-content",
        children=[
            DataTable(
                id="observatory-table",
                data=test_data,
                columns=columns,
                theme=default_theme,
                page_size=10,
                style_table={
                    'overflowX': 'auto',
                    'width': '100%'
                },
                style_header={
                    'backgroundColor': default_theme.panel_bg,
                    'fontWeight': 'bold',
                    'color': default_theme.text_light,
                    'borderBottom': f'2px solid {default_theme.secondary}'
                },
                style_cell={
                    'backgroundColor': default_theme.base_bg,
                    'color': default_theme.text_light,
                    'border': f'1px solid {default_theme.secondary}',
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                }
            ).render()
        ],
        style={
            "backgroundColor": default_theme.panel_bg,
            "padding": "20px",
            "borderRadius": "5px"
        }
    ).render()
    
    # Return the full layout
    return html.Div([
        header,
        content
    ], style={
        "padding": "20px",
        "backgroundColor": default_theme.base_bg,
        "minHeight": "100vh"
    })


# Also need to import html from dash
from dash import html 