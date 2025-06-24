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
    
    # Create table columns
    columns = [
        {"name": "Process Group", "id": "process_group"},
        {"name": "Process", "id": "process"},
        {"name": "Data", "id": "data"},
        {"name": "Type", "id": "data_type"},
        {"name": "Value", "id": "data_value"},
        {"name": "Duration", "id": "duration_ms"},
        {"name": "Timestamp", "id": "ts"},
        {"name": "Status", "id": "status"},
        {"name": "Exception", "id": "exception"}
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
                                    "fontSize": "1.1rem",
                                    "marginBottom": "10px"
                                }
                            ),
                            
                            # Last refresh timestamp
                            html.P(
                                id="observatory-last-refresh",
                                children="",
                                style={
                                    "color": default_theme.text_subtle,
                                    "fontSize": "0.9rem",
                                    "marginBottom": "20px",
                                    "fontStyle": "italic"
                                }
                            ),
                        ]
                    ).render(), {"xs": 12, "md": 8}),
                    
                    # Refresh button section
                    (Container(
                        id="observatory-button-container",
                        children=[
                            html.Div([
                                Button(
                                    id="observatory-refresh-button",
                                    label="Refresh Data",
                                    theme=default_theme,
                                    n_clicks=0,
                                    style={
                                        "width": "48%",
                                        "marginRight": "4%"
                                    }
                                ).render(),
                                Button(
                                    id="observatory-test-exception-button",
                                    label="Test Exception",
                                    theme=default_theme,
                                    n_clicks=0,
                                    style={
                                        "width": "48%",
                                        "backgroundColor": default_theme.danger,
                                        "borderColor": default_theme.danger
                                    }
                                ).render()
                            ], style={
                                "display": "flex",
                                "marginTop": "10px"
                            })
                        ],
                        style={
                            "textAlign": "right"
                        }
                    ).render(), {"xs": 12, "md": 4}),
                    
                    # Process group filter buttons
                    html.Div(
                        id="observatory-filter-buttons",
                        children=[
                            html.Label("Filter by Process Group: ", style={
                                "color": default_theme.text_light,
                                "marginRight": "10px",
                                "fontWeight": "bold"
                            }),
                            # Buttons will be dynamically generated based on available process groups
                            html.Div(
                                id="observatory-filter-button-container",
                                children=[
                                    # Buttons will be populated by callback
                                ],
                                style={
                                    "display": "inline-block"
                                }
                            )
                        ],
                        style={
                            "marginTop": "15px",
                            "padding": "10px",
                            "backgroundColor": default_theme.base_bg,
                            "borderRadius": "3px"
                        }
                    )
                ]
            ).render(),
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
                page_size=1000,  # Show up to 1000 rows without pagination
                style_table={
                    'overflowY': 'auto',
                    'maxHeight': '700px',  # Increased for better scrolling
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
                    'height': 'auto',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                style_data_conditional=[
                    # Set specific widths for each column - adjusted to prevent horizontal scroll
                    {'if': {'column_id': 'process_group'}, 'width': '12%', 'maxWidth': '120px'},
                    {'if': {'column_id': 'process'}, 'width': '15%', 'maxWidth': '150px'},
                    {'if': {'column_id': 'data'}, 'width': '12%', 'maxWidth': '120px'},
                    {'if': {'column_id': 'data_type'}, 'width': '8%', 'maxWidth': '80px'},
                    {'if': {'column_id': 'data_value'}, 'width': '20%', 'maxWidth': '200px'},
                    {'if': {'column_id': 'duration_ms'}, 'width': '10%', 'maxWidth': '100px'},
                    {'if': {'column_id': 'ts'}, 'width': '13%', 'maxWidth': '130px'},
                    {'if': {'column_id': 'status'}, 'width': '5%', 'maxWidth': '50px'},
                    {'if': {'column_id': 'exception'}, 'width': '5%', 'maxWidth': '50px'},  # Now visible
                    # Row styling based on status
                    {
                        'if': {
                            'filter_query': '{status} = ERR',
                            'column_id': 'status'
                        },
                        'backgroundColor': default_theme.danger,
                        'color': 'white',
                    }
                ]
            ).render()
        ],
        style={
            "backgroundColor": default_theme.panel_bg,
            "padding": "20px",
            "borderRadius": "5px"
        }
    ).render()
    
    # Create exception table area
    exception_content = Container(
        id="observatory-exception-content",
        children=[
            html.H3(
                "Exceptions Only",
                style={
                    "color": default_theme.danger,
                    "marginBottom": "15px",
                    "fontSize": "20px"
                }
            ),
            DataTable(
                id="observatory-exception-table",
                data=test_data,  # Will be populated by callback
                columns=columns,  # Same columns as main table
                theme=default_theme,
                page_size=1000,  # Show up to 1000 rows without pagination
                style_table={
                    'overflowY': 'auto',
                    'maxHeight': '600px',  # Increased for better scrolling
                    'width': '100%'
                },
                style_header={
                    'backgroundColor': default_theme.danger,
                    'fontWeight': 'bold',
                    'color': 'white',
                    'borderBottom': f'2px solid {default_theme.danger}'
                },
                style_cell={
                    'backgroundColor': default_theme.base_bg,
                    'color': default_theme.text_light,
                    'border': f'1px solid {default_theme.secondary}',
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                style_data_conditional=[
                    # Set specific widths for each column - adjusted to prevent horizontal scroll
                    {'if': {'column_id': 'process_group'}, 'width': '12%', 'maxWidth': '120px'},
                    {'if': {'column_id': 'process'}, 'width': '15%', 'maxWidth': '150px'},
                    {'if': {'column_id': 'data'}, 'width': '12%', 'maxWidth': '120px'},
                    {'if': {'column_id': 'data_type'}, 'width': '8%', 'maxWidth': '80px'},
                    {'if': {'column_id': 'data_value'}, 'width': '20%', 'maxWidth': '200px'},
                    {'if': {'column_id': 'duration_ms'}, 'width': '10%', 'maxWidth': '100px'},
                    {'if': {'column_id': 'ts'}, 'width': '13%', 'maxWidth': '130px'},
                    {'if': {'column_id': 'status'}, 'width': '5%', 'maxWidth': '50px'},
                    {'if': {'column_id': 'exception'}, 'width': '5%', 'maxWidth': '50px'},  # Now visible
                    # Row styling based on status
                    {
                        'if': {
                            'filter_query': '{status} = ERR',
                            'column_id': 'status'
                        },
                        'backgroundColor': default_theme.danger,
                        'color': 'white',
                    }
                ]
            ).render()
        ],
        style={
            "backgroundColor": default_theme.panel_bg,
            "padding": "20px",
            "borderRadius": "5px",
            "marginTop": "20px"
        }
    ).render()
    
    # Return the full layout
    return html.Div([
        # Add auto-refresh interval (5 seconds)
        dcc.Interval(
            id="observatory-auto-refresh",
            interval=5000,  # 5 seconds
            n_intervals=0
        ),
        
        # Hidden store for filter state
        dcc.Store(id="observatory-filter-state", data="all"),
        
        # Main content
        header,
        content,
        exception_content
    ], style={
        "padding": "20px",
        "backgroundColor": default_theme.base_bg,
        "minHeight": "100vh"
    })


# Also need to import html from dash
from dash import html, dcc 