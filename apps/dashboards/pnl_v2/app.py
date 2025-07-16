"""P&L Dashboard V2 - Main application layout."""

import logging
from pathlib import Path
from dash import html, dcc
import dash_bootstrap_components as dbc

from lib.components import Container
from lib.components.themes import default_theme
from .views import (
    create_trades_tab, 
    create_daily_pnl_tab, 
    create_chart_tab,
    create_summary_cards
)

logger = logging.getLogger(__name__)


def create_pnl_v2_layout():
    """Create the main layout for P&L Tracking V2 dashboard."""
    
    return Container(
        id="pnl-v2-main-container",
        children=[
            # Header
            dbc.Row([
                dbc.Col([
                    html.H2("P&L Tracking Dashboard", className="mb-0"),
                    html.Small("Real-time profit and loss tracking", className="text-muted")
                ])
            ], className="mb-4"),
            
            # Summary Cards Row
            html.Div(id="pnl-v2-summary-cards", children=create_summary_cards()),
            
            # Main Content Tabs
            html.Div([
                dbc.Tabs([
                    dbc.Tab(
                        label="Open Positions", 
                        value="positions",
                        children=[
                            html.Div(id='pnl-v2-positions-content')
                        ]
                    ),
                    dbc.Tab(
                        label="Trade Ledger", 
                        tab_id="pnl-v2-tab-trades",
                        children=create_trades_tab()
                    ),
                    dbc.Tab(
                        label="Daily P&L History",
                        tab_id="pnl-v2-tab-daily",
                        children=create_daily_pnl_tab()
                    ),
                    dbc.Tab(
                        label="P&L Chart",
                        tab_id="pnl-v2-tab-chart",
                        children=create_chart_tab()
                    )
                ], id="pnl-v2-tabs", active_tab="pnl-v2-tab-positions")
            ], style={
                'backgroundColor': default_theme.panel_bg,
                'padding': '20px',
                'borderRadius': '8px',
                'border': f'1px solid {default_theme.secondary}',
                'marginTop': '20px'
            }),
            
            # Auto-refresh interval (5 seconds)
            dcc.Interval(
                id='pnl-v2-interval-component',
                interval=5000,  # 5 seconds in milliseconds
                n_intervals=0
            ),
            
            # Store components for data
            dcc.Store(id='pnl-v2-positions-store', data={}),
            dcc.Store(id='pnl-v2-trades-store', data={}),
            dcc.Store(id='pnl-v2-daily-store', data={}),
            dcc.Store(id='pnl-v2-summary-store', data={})
        ]
    ).render() 