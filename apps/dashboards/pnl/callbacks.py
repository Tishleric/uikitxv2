"""P&L Dashboard Callbacks

This module contains all callback functions for P&L dashboard interactivity.
"""

import logging
from typing import List, Dict, Any, Tuple
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from .app import controller, create_summary_card
from lib.components.themes import default_theme
from lib.monitoring.decorators import monitor

logger = logging.getLogger(__name__)


@callback(
    [Output("pnl-summary-cards", "children"),
     Output("pnl-last-update", "children"),
     Output("pnl-watcher-status", "children")],
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_summary_stats(n_intervals: int, n_clicks: int) -> Tuple[List[html.Div], str, str]:
    """Update summary statistics cards.
    
    Args:
        n_intervals: Number of interval updates
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Tuple of (summary cards, last update time, watcher status)
    """
    try:
        # Get summary stats from controller
        stats = controller.get_summary_stats()
        
        # Create summary cards
        cards = [
            create_summary_card(
                "Total P&L",
                f"${stats['total_pnl']:,.2f}",
                color=stats['total_pnl_color']
            ),
            create_summary_card(
                "Today's P&L", 
                f"${stats['today_pnl']:,.2f}",
                color=stats['today_pnl_color']
            ),
            create_summary_card(
                "Realized P&L",
                f"${stats['total_realized']:,.2f}",
                color=stats['total_realized_color']
            ),
            create_summary_card(
                "Unrealized P&L",
                f"${stats['total_unrealized']:,.2f}",
                color=stats['total_unrealized_color']
            ),
            create_summary_card(
                "Active Positions",
                str(stats['position_count']),
                color=default_theme.text_light
            )
        ]
        
        # Get watcher status
        watcher_status = controller.get_watcher_status()
        watcher_text = "File Watchers: "
        if watcher_status.get('trades_watcher_active'):
            watcher_text += "✓ Trades "
        else:
            watcher_text += "✗ Trades "
            
        if watcher_status.get('prices_watcher_active'):
            watcher_text += "✓ Prices"
        else:
            watcher_text += "✗ Prices"
        
        return cards, f"Last Update: {stats['last_update']}", watcher_text
        
    except Exception as e:
        logger.error(f"Error updating summary stats: {e}")
        return [], "Error updating stats", "Watcher status unknown"


@callback(
    [Output("pnl-positions-table", "data"),
     Output("pnl-positions-table", "style_data_conditional")],
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_positions_table(n_intervals: int, n_clicks: int) -> Tuple[List[Dict], List[Dict]]:
    """Update positions table data.
    
    Args:
        n_intervals: Number of interval updates
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Tuple of (table data, conditional styles)
    """
    try:
        # Get positions from controller
        positions = controller.get_position_summary()
        
        # Create conditional styles for P&L coloring
        style_conditions = []
        
        # Style for realized P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{realized_pnl} < 0',
                    'column_id': 'realized_pnl'
                },
                'color': default_theme.danger
            },
            {
                'if': {
                    'filter_query': '{realized_pnl} >= 0',
                    'column_id': 'realized_pnl'
                },
                'color': default_theme.success
            }
        ])
        
        # Style for unrealized P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{unrealized_pnl} < 0',
                    'column_id': 'unrealized_pnl'
                },
                'color': default_theme.danger
            },
            {
                'if': {
                    'filter_query': '{unrealized_pnl} >= 0',
                    'column_id': 'unrealized_pnl'
                },
                'color': default_theme.success
            }
        ])
        
        # Style for total P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{total_pnl} < 0',
                    'column_id': 'total_pnl'
                },
                'color': default_theme.danger,
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{total_pnl} >= 0',
                    'column_id': 'total_pnl'
                },
                'color': default_theme.success,
                'fontWeight': 'bold'
            }
        ])
        
        return positions, style_conditions
        
    except Exception as e:
        logger.error(f"Error updating positions table: {e}")
        return [], []


@callback(
    [Output("pnl-daily-table", "data"),
     Output("pnl-daily-table", "style_data_conditional")],
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_daily_table(n_intervals: int, n_clicks: int) -> Tuple[List[Dict], List[Dict]]:
    """Update daily P&L table data.
    
    Args:
        n_intervals: Number of interval updates
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Tuple of (table data, conditional styles)
    """
    try:
        # Get daily P&L from controller
        daily_pnl = controller.get_daily_pnl_summary()
        
        # Create conditional styles
        style_conditions = []
        
        # Style for realized P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{realized_pnl} < 0',
                    'column_id': 'realized_pnl'
                },
                'color': default_theme.danger
            },
            {
                'if': {
                    'filter_query': '{realized_pnl} >= 0',
                    'column_id': 'realized_pnl'
                },
                'color': default_theme.success
            }
        ])
        
        # Style for unrealized P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{unrealized_pnl} < 0',
                    'column_id': 'unrealized_pnl'
                },
                'color': default_theme.danger
            },
            {
                'if': {
                    'filter_query': '{unrealized_pnl} >= 0',
                    'column_id': 'unrealized_pnl'
                },
                'color': default_theme.success
            }
        ])
        
        # Style for total P&L
        style_conditions.extend([
            {
                'if': {
                    'filter_query': '{total_pnl} < 0',
                    'column_id': 'total_pnl'
                },
                'color': default_theme.danger,
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{total_pnl} >= 0',
                    'column_id': 'total_pnl'
                },
                'color': default_theme.success,
                'fontWeight': 'bold'
            }
        ])
        
        return daily_pnl, style_conditions
        
    except Exception as e:
        logger.error(f"Error updating daily table: {e}")
        return [], []


@callback(
    Output("pnl-cumulative-chart", "figure"),
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_pnl_chart(n_intervals: int, n_clicks: int) -> Dict[str, Any]:
    """Update P&L chart.
    
    Args:
        n_intervals: Number of interval updates
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Plotly figure dictionary
    """
    try:
        # Get chart data from controller
        chart_data = controller.get_pnl_chart_data()
        
        if not chart_data['dates']:
            # Return empty chart
            return {
                'data': [],
                'layout': {
                    'title': 'Cumulative P&L',
                    'xaxis': {'title': 'Date'},
                    'yaxis': {'title': 'P&L ($)'},
                    'height': 400,
                    'plot_bgcolor': default_theme.base_bg,
                    'paper_bgcolor': default_theme.panel_bg,
                    'font': {'color': default_theme.text_light}
                }
            }
        
        # Create traces
        traces = []
        
        # Cumulative P&L line
        traces.append(go.Scatter(
            x=chart_data['dates'],
            y=chart_data['cumulative_pnl'],
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(
                color=default_theme.primary,
                width=3
            ),
            marker=dict(size=6)
        ))
        
        # Daily P&L bars
        traces.append(go.Bar(
            x=chart_data['dates'],
            y=chart_data['daily_pnl'],
            name='Daily P&L',
            marker_color=[
                default_theme.success if val >= 0 else default_theme.danger
                for val in chart_data['daily_pnl']
            ],
            yaxis='y2',
            opacity=0.6
        ))
        
        # Create layout
        layout = {
            'title': {
                'text': 'P&L Performance',
                'font': {'color': default_theme.text_light}
            },
            'xaxis': {
                'title': 'Date',
                'gridcolor': default_theme.secondary,
                'linecolor': default_theme.secondary,
                'tickfont': {'color': default_theme.text_light},
                'titlefont': {'color': default_theme.text_light}
            },
            'yaxis': {
                'title': 'Cumulative P&L ($)',
                'gridcolor': default_theme.secondary,
                'linecolor': default_theme.secondary,
                'tickfont': {'color': default_theme.text_light},
                'titlefont': {'color': default_theme.text_light},
                'side': 'left'
            },
            'yaxis2': {
                'title': 'Daily P&L ($)',
                'overlaying': 'y',
                'side': 'right',
                'gridcolor': default_theme.secondary,
                'linecolor': default_theme.secondary,
                'tickfont': {'color': default_theme.text_light},
                'titlefont': {'color': default_theme.text_light}
            },
            'height': 400,
            'plot_bgcolor': default_theme.base_bg,
            'paper_bgcolor': default_theme.panel_bg,
            'font': {'color': default_theme.text_light},
            'showlegend': True,
            'legend': {
                'bgcolor': default_theme.panel_bg,
                'bordercolor': default_theme.secondary,
                'font': {'color': default_theme.text_light}
            },
            'hovermode': 'x unified'
        }
        
        return {'data': traces, 'layout': layout}
        
    except Exception as e:
        logger.error(f"Error updating P&L chart: {e}")
        return {
            'data': [],
            'layout': {
                'title': 'Error loading chart',
                'plot_bgcolor': default_theme.base_bg,
                'paper_bgcolor': default_theme.panel_bg,
                'font': {'color': default_theme.text_light}
            }
        }


@callback(
    [Output("pnl-trades-table", "data"),
     Output("pnl-trades-table", "style_data_conditional")],
    [Input("pnl-interval-component", "n_intervals"),
     Input("pnl-refresh-button", "n_clicks")],
    prevent_initial_call=False
)
@monitor()
def update_trades_table(n_intervals: int, n_clicks: int) -> Tuple[List[Dict], List[Dict]]:
    """Update trades history table with styling.
    
    Args:
        n_intervals: Number of interval updates  
        n_clicks: Number of manual refresh clicks
        
    Returns:
        Tuple of (trade data, conditional styles)
    """
    try:
        # Get trade history from controller
        trades = controller.get_trade_history(limit=100)
        
        # Create conditional styles for header rows
        style_conditions = []
        
        # Style header rows
        for i, trade in enumerate(trades):
            if trade.get('is_header', False):
                style_conditions.append({
                    'if': {'row_index': i},
                    'backgroundColor': default_theme.secondary,
                    'color': default_theme.text_light,
                    'fontWeight': 'bold',
                    'fontSize': '14px',
                    'borderBottom': f'2px solid {default_theme.primary}'
                })
        
        return trades, style_conditions
        
    except Exception as e:
        logger.error(f"Error updating trades table: {e}")
        return [], []


# Start file watchers when module loads
try:
    controller.start_file_watchers()
    logger.info("P&L file watchers started successfully")
except Exception as e:
    logger.error(f"Failed to start P&L file watchers: {e}")


def register_callbacks(app):
    """Register all P&L dashboard callbacks with the main app.
    
    This function is called from the main app during startup to register
    all callbacks before the dashboard is loaded.
    
    Args:
        app: Dash application instance
    """
    # Import the Dash module to ensure callbacks are registered
    import apps.dashboards.pnl.callbacks
    logger.info("P&L dashboard callbacks registered with main app") 