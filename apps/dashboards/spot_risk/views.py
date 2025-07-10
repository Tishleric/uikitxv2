"""Views module for Spot Risk dashboard"""

from dash import html, dcc
import dash_daq as daq
from lib.components.basic import Container, Button, Loading, Toggle, ComboBox, RadioButton, RangeSlider, Checkbox
from lib.components.advanced import DataTable
from lib.components.themes import default_theme

def get_column_definitions():
    """Get column definitions grouped by category
    
    Returns:
        dict: Column definitions grouped by category
    """
    return {
        'base': [
            {'id': 'key', 'name': 'Key', 'type': 'text'},
            {'id': 'position', 'name': 'Position', 'type': 'numeric', 'format': {'specifier': '.0f'}},
            {'id': 'strike', 'name': 'Strike', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'id': 'itype', 'name': 'Type', 'type': 'text'},
            {'id': 'expiry_date', 'name': 'Expiry', 'type': 'text'},
            {'id': 'midpoint_price', 'name': 'Mid Price', 'type': 'numeric', 'format': {'specifier': '.6f'}}
        ],
        '1st': [
            {'id': 'delta_F', 'name': 'Delta (F)', 'type': 'numeric', 'format': {'specifier': '.4f'}},
            {'id': 'delta_y', 'name': 'Delta (y)', 'type': 'numeric', 'format': {'specifier': '.4f'}},
            {'id': 'vega_y', 'name': 'Vega (y)', 'type': 'numeric', 'format': {'specifier': '.4f'}},
            {'id': 'theta_F', 'name': 'Theta (F)', 'type': 'numeric', 'format': {'specifier': '.4f'}}
        ],
        '2nd': [
            {'id': 'gamma_F', 'name': 'Gamma (F)', 'type': 'numeric', 'format': {'specifier': '.6f'}},
            {'id': 'gamma_y', 'name': 'Gamma (y)', 'type': 'numeric', 'format': {'specifier': '.6f'}},
            {'id': 'volga_price', 'name': 'Volga', 'type': 'numeric', 'format': {'specifier': '.6f'}},
            {'id': 'vanna_F_price', 'name': 'Vanna (F)', 'type': 'numeric', 'format': {'specifier': '.6f'}},
            {'id': 'charm_F', 'name': 'Charm (F)', 'type': 'numeric', 'format': {'specifier': '.6f'}}
        ],
        '3rd': [
            {'id': 'speed_F', 'name': 'Speed (F)', 'type': 'numeric', 'format': {'specifier': '.8f'}},
            {'id': 'color_F', 'name': 'Color (F)', 'type': 'numeric', 'format': {'specifier': '.8f'}},
            {'id': 'ultima', 'name': 'Ultima', 'type': 'numeric', 'format': {'specifier': '.8f'}},
            {'id': 'zomma', 'name': 'Zomma', 'type': 'numeric', 'format': {'specifier': '.8f'}}
        ],
        'cross': [
            # Placeholder for cross-asset Greeks when implemented
        ],
        'other': [
            {'id': 'implied_vol', 'name': 'Implied Vol', 'type': 'numeric', 'format': {'specifier': '.4f'}},
            {'id': 'vega_price', 'name': 'Vega ($)', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'id': 'greek_calc_success', 'name': 'Calc Status', 'type': 'text'},
            {'id': 'greek_calc_error', 'name': 'Error Message', 'type': 'text'},
            {'id': 'model_version', 'name': 'Model', 'type': 'text'}
        ]
    }

def create_spot_risk_content(controller=None):
    """Create the spot risk dashboard content"""
    
    # Get timestamp from controller if available
    timestamp_text = ''
    if controller:
        try:
            timestamp = controller.get_timestamp()
            if timestamp:
                timestamp_text = f'Data from: {timestamp}'
        except Exception:
            timestamp_text = 'No data loaded'
    
    # Create header section with title and controls
    header_section = Container(
        id='spot-risk-header',
        style={'marginBottom': '30px'},
        children=[
            # Title row
            Container(
                id='spot-risk-title-row',
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'space-between',
                    'marginBottom': '20px'
                },
                children=[
                    # Title
                    html.H1(
                        'Spot Risk Analysis',
                        style={
                            'color': default_theme.primary,
                            'margin': '0',
                            'fontSize': '28px',
                            'fontWeight': 'bold'
                        }
                    ),
                    # Timestamp display
                    html.Div(
                        timestamp_text,
                        id='spot-risk-timestamp', 
                        style={
                            'color': default_theme.text_subtle,
                            'fontSize': '14px',
                            'fontStyle': 'italic'
                        }
                    )
                ]
            ),
            
            # Controls section
            Container(
                id='spot-risk-controls-row',
                style={
                    'display': 'flex',
                    'gap': '20px',
                    'alignItems': 'center'
                },
                children=[
                    # Manual refresh button
                    Button(
                        id='spot-risk-refresh-btn',
                        label='Refresh Data',
                        style={
                            'backgroundColor': default_theme.primary,
                            'color': default_theme.base_bg,
                            'border': 'none',
                            'padding': '8px 16px',
                            'borderRadius': '4px',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'cursor': 'pointer'
                        }
                    ).render(),
                    
                    # Loading indicator
                    Loading(
                        id='spot-risk-loading',
                        type='circle',
                        children=[
                            html.Div(id='spot-risk-refresh-status', style={'display': 'none'})
                        ]
                    ).render(),
                    
                    # Auto-refresh controls
                    Container(
                        id='spot-risk-auto-refresh-section',
                        style={
                            'display': 'flex',
                            'alignItems': 'center',
                            'gap': '10px',
                            'paddingLeft': '20px',
                            'borderLeft': f'1px solid {default_theme.secondary}'
                        },
                        children=[
                            html.Label(
                                'Auto-refresh:',
                                style={
                                    'color': default_theme.text_light,
                                    'fontSize': '14px',
                                    'marginRight': '5px'
                                }
                            ),
                            Toggle(
                                id='spot-risk-auto-refresh-toggle',
                                value=False
                            ).render(),
                            html.Label(
                                'Interval (min):',
                                style={
                                    'color': default_theme.text_light,
                                    'fontSize': '14px',
                                    'marginLeft': '10px',
                                    'marginRight': '5px'
                                }
                            ),
                            dcc.Input(
                                id='spot-risk-refresh-interval-input',
                                type='number',
                                value=5,
                                min=1,
                                max=60,
                                style={
                                    'width': '60px',
                                    'padding': '4px 8px',
                                    'borderRadius': '4px',
                                    'border': f'1px solid {default_theme.secondary}',
                                    'backgroundColor': default_theme.panel_bg,
                                    'color': default_theme.text_light,
                                    'fontSize': '14px'
                                }
                            )
                        ]
                    )
                ]
            )
        ]
    )
    
    # Create control panel section (Phase 3 filters)
    # Get expiry options from controller
    expiry_options = []
    if controller:
        try:
            expiries = controller.get_unique_expiries()
            expiry_options = [{'label': exp, 'value': exp} for exp in expiries]
        except Exception:
            expiry_options = []
    
    # Add "All" option at the beginning
    if expiry_options:
        expiry_options.insert(0, {'label': 'All Expiries', 'value': 'ALL'})
    
    # Get strike range from controller
    strike_min, strike_max = 100.0, 120.0  # Default values
    if controller:
        try:
            strike_min, strike_max = controller.get_strike_range()
        except Exception:
            pass
    
    control_panel = Container(
        id='spot-risk-control-panel',
        style={
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '8px',
            'padding': '20px',
            'marginBottom': '20px',
            'border': f'1px solid {default_theme.secondary}'
        },
        children=[
            # Filters section
            html.H3(
                'Filters',
                style={
                    'color': default_theme.text_light,
                    'fontSize': '18px',
                    'marginBottom': '20px',
                    'fontWeight': 'bold'
                }
            ),
            
            # Filter controls grid
            Container(
                id='spot-risk-filter-grid',
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
                    'gap': '20px'
                },
                children=[
                    # Expiry filter
                    html.Div([
                        html.Label(
                            'Expiry Date:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        ComboBox(
                            id='spot-risk-expiry-filter',
                            options=expiry_options,
                            value='ALL',
                            placeholder='Select expiry...',
                            style={
                                'width': '100%'
                            }
                        ).render()
                    ]),
                    
                    # Type filter
                    html.Div([
                        html.Label(
                            'Option Type:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        RadioButton(
                            id='spot-risk-type-filter',
                            options=[
                                {'label': 'All', 'value': 'ALL'},
                                {'label': 'Calls', 'value': 'C'},
                                {'label': 'Puts', 'value': 'P'},
                                {'label': 'Futures', 'value': 'F'}
                            ],
                            value='ALL',
                            inline=True
                        ).render()
                    ]),
                    
                    # Strike range filter
                    html.Div([
                        html.Label(
                            'Strike Range:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        RangeSlider(
                            id='spot-risk-strike-filter',
                            min=strike_min,
                            max=strike_max,
                            step=0.25,  # Standard strike price increment
                            value=[strike_min, strike_max],
                            marks={
                                strike_min: f'{strike_min:.2f}',
                                strike_max: f'{strike_max:.2f}'
                            },
                            tooltip={"placement": "bottom", "always_visible": False}
                        ).render(),
                        # Display current range values
                        html.Div(
                            id='spot-risk-strike-range-display',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginTop': '5px',
                                'textAlign': 'center'
                            }
                        )
                    ])
                ]
            )
        ]
    )
    
    # Create Greek groups section (Phase 4)
    greek_groups = Container(
        id='spot-risk-greek-groups',
        style={
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '8px',
            'padding': '20px',
            'marginBottom': '20px',
            'border': f'1px solid {default_theme.secondary}'
        },
        children=[
            html.H5(
                'Greek Groups',
                style={
                    'color': default_theme.primary,
                    'marginBottom': '20px',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }
            ),
            # Greek groups grid
            html.Div(
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                    'gap': '20px'
                },
                children=[
                    # Base information (always on)
                    html.Div([
                        Checkbox(
                            id='spot-risk-base-info',
                            options=[{
                                'label': 'Base Information',
                                'value': 'base',
                                'disabled': True
                            }],
                            value=['base'],  # Always checked
                            inline=True,
                            style={'marginBottom': '5px'}
                        ).render(),
                        html.Div(
                            'Key, Position, Strike, Type, Expiry, Price',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginLeft': '25px'
                            }
                        )
                    ]),
                    
                    # 1st Order Greeks
                    html.Div([
                        Checkbox(
                            id='spot-risk-1st-order',
                            options=[{
                                'label': '1st Order Greeks',
                                'value': '1st'
                            }],
                            value=['1st'],  # Default checked
                            inline=True,
                            style={'marginBottom': '5px'}
                        ).render(),
                        html.Div(
                            'Delta (F/y), Vega, Theta',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginLeft': '25px'
                            }
                        )
                    ]),
                    
                    # 2nd Order Greeks
                    html.Div([
                        Checkbox(
                            id='spot-risk-2nd-order',
                            options=[{
                                'label': '2nd Order Greeks',
                                'value': '2nd'
                            }],
                            value=[],  # Default unchecked
                            inline=True,
                            style={'marginBottom': '5px'}
                        ).render(),
                        html.Div(
                            'Gamma (F/y), Volga, Vanna, Charm',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginLeft': '25px'
                            }
                        )
                    ]),
                    
                    # 3rd Order Greeks
                    html.Div([
                        Checkbox(
                            id='spot-risk-3rd-order',
                            options=[{
                                'label': '3rd Order Greeks',
                                'value': '3rd'
                            }],
                            value=[],  # Default unchecked
                            inline=True,
                            style={'marginBottom': '5px'}
                        ).render(),
                        html.Div(
                            'Speed, Color, Ultima, Zomma',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginLeft': '25px'
                            }
                        )
                    ]),
                    
                    # Cross Greeks
                    html.Div([
                        Checkbox(
                            id='spot-risk-cross-greeks',
                            options=[{
                                'label': 'Cross Greeks',
                                'value': 'cross'
                            }],
                            value=[],  # Default unchecked
                            inline=True,
                            style={'marginBottom': '5px'}
                        ).render(),
                        html.Div(
                            'Cross-asset sensitivities',
                            style={
                                'color': default_theme.text_subtle,
                                'fontSize': '12px',
                                'marginLeft': '25px'
                            }
                        )
                    ])
                ]
            )
        ]
    ).render()
    
    # Create view controls section (Phase 5)
    view_controls = Container(
        id='spot-risk-view-controls',
        style={
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '8px',
            'padding': '20px',
            'marginBottom': '20px',
            'border': f'1px solid {default_theme.secondary}'
        },
        children=[
            html.H5(
                'View Options',
                style={
                    'color': default_theme.primary,
                    'marginBottom': '20px',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }
            ),
            # View controls grid
            html.Div(
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
                    'gap': '20px',
                    'alignItems': 'center'
                },
                children=[
                    # View mode toggle
                    html.Div([
                        html.Label(
                            'View Mode:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        html.Div(
                            style={
                                'display': 'flex',
                                'gap': '0'
                            },
                            children=[
                                Button(
                                    id='spot-risk-table-view-btn',
                                    label='Table',
                                    style={
                                        'backgroundColor': default_theme.primary,
                                        'color': default_theme.base_bg,
                                        'border': f'1px solid {default_theme.primary}',
                                        'padding': '8px 20px',
                                        'borderRadius': '4px 0 0 4px',
                                        'fontSize': '14px',
                                        'fontWeight': 'bold',
                                        'cursor': 'pointer',
                                        'minWidth': '80px'
                                    }
                                ).render(),
                                Button(
                                    id='spot-risk-graph-view-btn',
                                    label='Graph',
                                    style={
                                        'backgroundColor': default_theme.panel_bg,
                                        'color': default_theme.text_light,
                                        'border': f'1px solid {default_theme.secondary}',
                                        'borderLeft': 'none',
                                        'padding': '8px 20px',
                                        'borderRadius': '0 4px 4px 0',
                                        'fontSize': '14px',
                                        'fontWeight': 'normal',
                                        'cursor': 'pointer',
                                        'minWidth': '80px'
                                    }
                                ).render()
                            ]
                        )
                    ]),
                    
                    # Model selection
                    html.Div([
                        html.Label(
                            'Model Selection:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        ComboBox(
                            id='spot-risk-model-selector',
                            options=[
                                {'label': 'Bachelier V1', 'value': 'bachelier_v1'},
                                {'label': 'Bachelier V2 (Coming Soon)', 'value': 'bachelier_v2', 'disabled': True},
                                {'label': 'Black-Scholes (Coming Soon)', 'value': 'black_scholes', 'disabled': True}
                            ],
                            value='bachelier_v1',
                            clearable=False,
                            style={
                                'width': '100%'
                            }
                        ).render()
                    ]),
                    
                    # Greek space selection
                    html.Div([
                        html.Label(
                            'Greek Space:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        html.Div(
                            style={
                                'display': 'flex',
                                'gap': '0'
                            },
                            children=[
                                Button(
                                    id='spot-risk-f-space-btn',
                                    label='F-Space',
                                    style={
                                        'backgroundColor': default_theme.primary,
                                        'color': default_theme.base_bg,
                                        'border': f'1px solid {default_theme.primary}',
                                        'padding': '8px 20px',
                                        'borderRadius': '4px 0 0 4px',
                                        'fontSize': '14px',
                                        'fontWeight': 'bold',
                                        'cursor': 'pointer',
                                        'minWidth': '80px'
                                    }
                                ).render(),
                                Button(
                                    id='spot-risk-y-space-btn',
                                    label='Y-Space',
                                    style={
                                        'backgroundColor': default_theme.panel_bg,
                                        'color': default_theme.text_light,
                                        'border': f'1px solid {default_theme.secondary}',
                                        'borderLeft': 'none',
                                        'padding': '8px 20px',
                                        'borderRadius': '0 4px 4px 0',
                                        'fontSize': '14px',
                                        'fontWeight': 'normal',
                                        'cursor': 'pointer',
                                        'minWidth': '80px'
                                    }
                                ).render()
                            ]
                        )
                    ]),
                    
                    # Export button
                    html.Div([
                        html.Label(
                            'Export Data:',
                            style={
                                'color': default_theme.text_light,
                                'fontSize': '14px',
                                'marginBottom': '8px',
                                'display': 'block',
                                'fontWeight': '500'
                            }
                        ),
                        Button(
                            id='spot-risk-export-btn',
                            label='Export to CSV',
                            style={
                                'backgroundColor': default_theme.accent,
                                'color': default_theme.base_bg,
                                'border': 'none',
                                'padding': '8px 16px',
                                'borderRadius': '4px',
                                'fontSize': '14px',
                                'fontWeight': 'bold',
                                'cursor': 'pointer',
                                'width': '100%'
                            }
                        ).render()
                    ])
                ]
            )
        ]
    ).render()
    
    # Create data display section (Phase 5-6)
    data_display = Container(
        id='spot-risk-data-display',
        style={
            'backgroundColor': default_theme.panel_bg,
            'borderRadius': '8px',
            'padding': '10px',  # Reduced padding for more table width
            'border': f'1px solid {default_theme.secondary}',
            'minHeight': '400px',
            'overflow': 'visible'  # Ensure content can expand
        },
        children=[
            # Loading wrapper for data table
            Loading(
                id='spot-risk-table-loading',
                type='circle',
                children=[
                    # DataTable container
                    html.Div(
                        id='spot-risk-table-container',
                        style={'display': 'block'},  # Will be toggled by callbacks
                        children=[
                            # No data message (will be hidden when data loads)
                            html.Div(
                                id='spot-risk-no-data',
                                children=[
                                    html.P(
                                        'No positions found. Refresh data to check for new positions.',
                                        style={
                                            'color': default_theme.text_subtle,
                                            'textAlign': 'center',
                                            'padding': '40px',
                                            'fontSize': '16px'
                                        }
                                    )
                                ],
                                style={'display': 'block'}  # Will be toggled by callbacks
                            ),
                            # DataTable (initially hidden)
                            html.Div(
                                id='spot-risk-table-wrapper',
                                style={'display': 'none'},  # Will be toggled by callbacks
                                children=[
                                    DataTable(
                                        id='spot-risk-data-table',
                                        columns=[],  # Will be populated by callbacks
                                        data=[],  # Will be populated by callbacks
                                        page_size=20,
                                        style_table={
                                            'overflowX': 'visible',  # Changed from 'auto' to prevent scroll
                                            'width': '100%',  # Changed from minWidth to width
                                            'tableLayout': 'auto'  # Let table size naturally
                                        },
                                        style_header={
                                            'backgroundColor': default_theme.secondary,
                                            'color': default_theme.text_light,
                                            'fontWeight': 'bold',
                                            'textAlign': 'center',
                                            'padding': '10px',
                                            'border': f'1px solid {default_theme.secondary}'
                                        },
                                        style_cell={
                                            'backgroundColor': default_theme.base_bg,
                                            'color': default_theme.text_light,
                                            'border': f'1px solid {default_theme.secondary}',
                                            'padding': '8px',
                                            'textAlign': 'center',
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'minWidth': '80px'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': default_theme.panel_bg
                                            },
                                            {
                                                'if': {'state': 'selected'},
                                                'backgroundColor': default_theme.primary,
                                                'border': f'1px solid {default_theme.primary}'
                                            }
                                        ],
                                        theme=default_theme
                                    ).render()
                                ]
                            )
                        ]
                    ),
                    # Graph view container (sibling of table container)
                    html.Div(
                        id='spot-risk-graph-container',
                        style={'display': 'none'},  # Will be toggled by callbacks
                        children=[
                            # Graph view controls
                            html.Div(
                                style={
                                    'backgroundColor': default_theme.secondary,
                                    'padding': '15px',
                                    'borderRadius': '8px',
                                    'marginBottom': '20px',
                                    'display': 'flex',
                                    'justifyContent': 'space-between',
                                    'alignItems': 'center'
                                },
                                children=[
                                    html.H5(
                                        'Greek Profile Graphs',
                                        style={
                                            'color': default_theme.text_light,
                                            'margin': '0',
                                            'fontSize': '18px',
                                            'fontWeight': '600'
                                        }
                                    ),
                                    html.Div(
                                        id='spot-risk-graph-info',
                                        style={
                                            'color': default_theme.text_light,
                                            'fontSize': '14px'
                                        }
                                    )
                                ]
                            ),
                            # Dynamic graph grid container
                            html.Div(
                                id='spot-risk-graphs-grid',
                                style={
                                    'display': 'grid',
                                    'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
                                    'gap': '20px'
                                },
                                children=[]  # Will be populated by callbacks
                            ),
                            # Legend/Info section
                            html.Div(
                                style={
                                    'marginTop': '20px',
                                    'padding': '15px',
                                    'backgroundColor': default_theme.secondary,
                                    'borderRadius': '8px'
                                },
                                children=[
                                    html.Div(
                                        style={
                                            'display': 'flex',
                                            'gap': '30px',
                                            'flexWrap': 'wrap',
                                            'fontSize': '12px',
                                            'color': default_theme.text_subtle
                                        },
                                        children=[
                                            html.Div([
                                                html.Span('● ', style={'color': default_theme.primary}),
                                                'Greek Profile (Taylor Series)'
                                            ]),
                                            html.Div([
                                                html.Span('▲ ', style={'color': default_theme.accent, 'fontSize': '16px'}),
                                                'Position Marker (size ∝ position)'
                                            ]),
                                            html.Div([
                                                html.Span('│ ', style={'color': default_theme.danger}),
                                                'ATM Strike (δ ≈ 0.5)'
                                            ])
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ).render()
        ]
    )
    
    # Main layout
    return Container(
        id='spot-risk-container',
        style={
            'padding': '10px',  # Reduced padding to give more width
            'backgroundColor': default_theme.base_bg,
            'minHeight': '100vh',
            'width': '100%',
            'maxWidth': 'none'  # Ensure no max width constraint
        },
        children=[
            header_section,
            control_panel,
            greek_groups,
            view_controls,
            data_display,
            
            # Hidden stores for state management
            dcc.Store(id='spot-risk-data-store'),
            dcc.Store(id='spot-risk-filter-store'),
            dcc.Store(id='spot-risk-display-store'),
            dcc.Store(id='spot-risk-greek-space-store', data='F'),  # Default to F-space
            dcc.Interval(
                id='spot-risk-refresh-interval',
                interval=5 * 60 * 1000,  # 5 minutes
                disabled=True
            ),
            # Download component for CSV export
            dcc.Download(id='spot-risk-download-csv')
        ]
    ).render() 
    
    # Create data display section placeholder 