"""P&L Dashboard V2 - View Components."""

import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import dash_table

from lib.components import Container, DataTable, Graph
from lib.components.themes import default_theme

logger = logging.getLogger(__name__)


def create_summary_card(title: str, value_id: str, default_value: str = "$0.00") -> html.Div:
    """Create a summary metric card."""
    return html.Div([
        html.H6(title, className="text-muted mb-2"),
        html.H3(id=value_id, children=default_value, className="mb-0")
    ], style={
        'backgroundColor': default_theme.panel_bg,
        'padding': '20px',
        'borderRadius': '8px',
        'border': f'1px solid {default_theme.secondary}',
        'textAlign': 'center'
    })


def create_summary_cards():
    """Create summary metric cards for the dashboard header."""
    return dbc.Row([
        dbc.Col([
            create_summary_card("Total Historic P&L", "pnl-v2-total-historic")
        ], width=3),
        
        dbc.Col([
            create_summary_card("Today's Realized P&L", "pnl-v2-today-realized")
        ], width=3),
        
        dbc.Col([
            create_summary_card("Today's Unrealized P&L", "pnl-v2-today-unrealized")
        ], width=3),
        
        dbc.Col([
            create_summary_card("Open Positions", "pnl-v2-open-positions-count", "0")
        ], width=3)
    ], className="mb-4")


def create_open_positions_tab(positions_df):
    """Create the open positions tab."""
    if positions_df.empty:
        return html.Div("No open positions", className="text-center")
    
    # Format numerical columns
    for col in ['quantity', 'avg_cost', 'last_price', 'unrealized_pnl', 
                'realized_pnl', 'total_pnl']:
        if col in positions_df.columns:
            if col in ['quantity']:
                positions_df[col] = positions_df[col].apply(lambda x: f"{x:,.0f}")
            else:
                positions_df[col] = positions_df[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else "-"
                )
    
    return dash_table.DataTable(
        id='positions-table',
        columns=[
            {"name": "Instrument", "id": "instrument"},
            {"name": "Quantity", "id": "quantity"},
            {"name": "Avg Cost", "id": "avg_cost"},
            {"name": "Last Price", "id": "last_price"},
            {"name": "Unrealized P&L", "id": "unrealized_pnl"},
            {"name": "Realized P&L", "id": "realized_pnl"},
            {"name": "Total P&L", "id": "total_pnl"},
        ],
        data=positions_df.to_dict('records'),
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'column_id': 'unrealized_pnl'},
                'color': 'green',
                'filter_query': '{unrealized_pnl} contains "$" && !{unrealized_pnl} contains "-"'
            },
            {
                'if': {'column_id': 'unrealized_pnl'},
                'color': 'red',
                'filter_query': '{unrealized_pnl} contains "-"'
            },
            {
                'if': {'column_id': 'total_pnl'},
                'color': 'green',
                'filter_query': '{total_pnl} contains "$" && !{total_pnl} contains "-"'
            },
            {
                'if': {'column_id': 'total_pnl'},
                'color': 'red',
                'filter_query': '{total_pnl} contains "-"'
            }
        ],
        style_table={'overflowX': 'auto'},
        # Remove pagination - show all rows
        page_action='none',
    )


def create_trades_tab():
    """Create the trade ledger tab content."""
    # Create the DataTable using wrapped component
    trades_table = DataTable(
        id='pnl-v2-trades-datatable',
        columns=[
            {"name": "Date", "id": "Date"},
            {"name": "Time", "id": "Time"},
            {"name": "Symbol", "id": "Symbol"},
            {"name": "Type", "id": "Type"},
            {"name": "Quantity", "id": "Quantity", "type": "numeric"},
            {"name": "Price", "id": "Price", "type": "numeric", "format": {"specifier": ",.5f"}},
            {"name": "SOD", "id": "SOD"},
            {"name": "Expired", "id": "Expired"}
        ],
        data=[],
        style_cell={'textAlign': 'center'},
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        page_size=50,
        theme=default_theme
    ).render()
    
    return Container(
        id="pnl-v2-trades-container",
        children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Trade History", className="mb-3"),
                    html.Div(id="pnl-v2-trades-table", children=[trades_table])
                ])
            ])
        ]
    ).render()


def create_daily_pnl_tab():
    """Create the daily P&L history tab content."""
    # Create the DataTable using wrapped component
    daily_table = DataTable(
        id='pnl-v2-daily-datatable',
        columns=[
            {"name": "Date", "id": "Date"},
            {"name": "SOD Realized", "id": "SOD Realized", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "SOD Unrealized", "id": "SOD Unrealized", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "EOD Realized", "id": "EOD Realized", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "EOD Unrealized", "id": "EOD Unrealized", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Daily Realized Δ", "id": "Daily Realized Δ", "type": "numeric", "format": {"specifier": "$,.2f"}},
            {"name": "Daily Unrealized Δ", "id": "Daily Unrealized Δ", "type": "numeric", "format": {"specifier": "$,.2f"}}
        ],
        data=[],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Daily Realized Δ', 'filter_query': '{Daily Realized Δ} < 0'},
                'color': 'red'
            },
            {
                'if': {'column_id': 'Daily Realized Δ', 'filter_query': '{Daily Realized Δ} > 0'},
                'color': 'green'
            },
            {
                'if': {'column_id': 'Daily Unrealized Δ', 'filter_query': '{Daily Unrealized Δ} < 0'},
                'color': 'red'
            },
            {
                'if': {'column_id': 'Daily Unrealized Δ', 'filter_query': '{Daily Unrealized Δ} > 0'},
                'color': 'green'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold'
        },
        theme=default_theme
    ).render()
    
    return Container(
        id="pnl-v2-daily-container",
        children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Daily P&L History", className="mb-3"),
                    html.Div(id="pnl-v2-daily-table", children=[daily_table])
                ])
            ])
        ]
    ).render()


def create_chart_tab():
    """Create the P&L chart tab content."""
    # Create the Graph using wrapped component
    chart = Graph(
        id='pnl-v2-chart',
        figure=create_empty_chart(),
        config={'displayModeBar': False},
        theme=default_theme
    ).render()
    
    return Container(
        id="pnl-v2-chart-container",
        children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Cumulative P&L Chart", className="mb-3"),
                    chart
                ])
            ])
        ]
    ).render()


def create_empty_chart():
    """Create an empty chart figure."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines+markers',
        name='Total P&L',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines',
        name='Realized P&L',
        line=dict(color='green', width=2, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=[],
        y=[],
        mode='lines',
        name='Unrealized P&L',
        line=dict(color='orange', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title='Cumulative P&L Over Time',
        xaxis_title='Date',
        yaxis_title='P&L ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig 