"""P&L Dashboard Application

Main module for the P&L tracking dashboard integrated into UIKitXv2.
"""

import logging
from dash import html, dcc

# Import wrapped components
from lib.components.basic import Container, Button, Tabs
from lib.components.advanced import DataTable, Graph, Grid
from lib.components.themes import default_theme

# Import controller and callbacks
from lib.trading.pnl_calculator.controller import PnLController

logger = logging.getLogger(__name__)

# Initialize controller at module level
controller = PnLController()


def create_summary_card(title: str, value: str, color: str = 'white', subtitle: str | None = None) -> html.Div:
    """Create a summary statistics card.
    
    Args:
        title: Card title
        value: Main value to display
        color: Text color for the value
        subtitle: Optional subtitle text
        
    Returns:
        html.Div component with styled card
    """
    card_content = [
        html.H6(title, style={
            'color': default_theme.text_subtle,
            'fontSize': '14px',
            'marginBottom': '5px',
            'fontWeight': '400'
        }),
        html.H3(value, style={
            'color': color,
            'fontSize': '24px',
            'fontWeight': '600',
            'marginBottom': '0'
        })
    ]
    
    if subtitle:
        card_content.append(html.P(subtitle, style={
            'color': default_theme.text_subtle,
            'fontSize': '12px',
            'marginTop': '5px',
            'marginBottom': '0'
        }))
    
    return html.Div(
        card_content,
        style={
            'backgroundColor': default_theme.panel_bg,
            'padding': '20px',
            'borderRadius': '8px',
            'border': f'1px solid {default_theme.secondary}',
            'minHeight': '100px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center'
        }
    )


def create_pnl_content():
    """Create the P&L dashboard content.
    
    Returns:
        Rendered Dash components for the P&L dashboard layout
    """
    logger.info("Creating P&L dashboard content")
    
    # Summary stats section
    summary_section = Container(
        id="pnl-summary-section",
        children=[
            html.H4("P&L Summary", style={'color': default_theme.text_light, 'marginBottom': '20px'}),
            html.Div(
                id="pnl-summary-cards",
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                    'gap': '15px',
                    'marginBottom': '30px'
                }
            )
        ]
    )
    
    # Control buttons
    controls_section = Container(
        id="pnl-controls-section",
        children=[
            html.Div([
                Button(
                    id="pnl-refresh-button",
                    label="Refresh P&L",
                    style={'marginRight': '10px'}
                ).render(),
                html.Span(
                    id="pnl-last-update",
                    style={
                        'color': default_theme.text_subtle,
                        'fontSize': '14px',
                        'marginLeft': '20px'
                    }
                ),
                html.Span(
                    id="pnl-watcher-status",
                    style={
                        'color': default_theme.text_subtle,
                        'fontSize': '14px',
                        'marginLeft': '20px',
                        'float': 'right'
                    }
                )
            ], style={'marginBottom': '20px'})
        ]
    )
    
    # Create tabs for different views
    tabs_content = Tabs(
        id="pnl-tabs",
        tabs=[
            ("Positions", Container(
                id="pnl-positions-container",
                children=[
                    DataTable(
                        id="pnl-positions-table",
                        columns=[
                            {'name': 'Instrument', 'id': 'instrument'},
                            {'name': 'Net Position', 'id': 'net_position', 'type': 'numeric'},
                            {'name': 'Avg Price', 'id': 'avg_price'},
                            {'name': 'Last Trade Price', 'id': 'last_price'},
                            {'name': 'Realized P&L', 'id': 'realized_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Unrealized P&L', 'id': 'unrealized_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Total P&L', 'id': 'total_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
                        ],
                        data=[],
                        style_data_conditional=[],
                        page_size=20
                    )
                ]
            )),
            ("Daily P&L", Container(
                id="pnl-daily-container", 
                children=[
                    DataTable(
                        id="pnl-daily-table",
                        columns=[
                            {'name': 'Date', 'id': 'date'},
                            {'name': 'Trade Count', 'id': 'trade_count', 'type': 'numeric'},
                            {'name': 'Realized P&L', 'id': 'realized_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Unrealized P&L', 'id': 'unrealized_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Total P&L', 'id': 'total_pnl', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
                        ],
                        data=[],
                        style_data_conditional=[],
                        page_size=20
                    )
                ]
            )),
            ("P&L Chart", Container(
                id="pnl-chart-container",
                children=[
                    Graph(
                        id="pnl-cumulative-chart",
                        figure={
                            'data': [],
                            'layout': {
                                'title': 'Cumulative P&L',
                                'xaxis': {'title': 'Date'},
                                'yaxis': {'title': 'P&L ($)'},
                                'height': 400
                            }
                        }
                    )
                ]
            )),
            ("Trade History", Container(
                id="pnl-trades-container",
                children=[
                    DataTable(
                        id="pnl-trades-table",
                        columns=[
                            {'name': 'Trade ID', 'id': 'trade_id'},
                            {'name': 'Instrument', 'id': 'instrument'},
                            {'name': 'Timestamp', 'id': 'timestamp'},
                            {'name': 'Side', 'id': 'side'},
                            {'name': 'Quantity', 'id': 'quantity', 'type': 'numeric'},
                            {'name': 'Price', 'id': 'price'},
                            {'name': 'Value', 'id': 'value', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
                        ],
                        data=[],
                        style_data_conditional=[],
                        page_size=50
                    )
                ]
            ))
        ]
    )
    
    # Auto-refresh interval (20 seconds)
    refresh_interval = dcc.Interval(
        id='pnl-interval-component',
        interval=20*1000,  # 20 seconds in milliseconds
        n_intervals=0
    )
    
    # Combine all sections
    return Container(
        id="pnl-main-container",
        children=[
            refresh_interval,
            summary_section,
            controls_section,
            tabs_content
        ],
        style={'padding': '20px'}
    ).render() 