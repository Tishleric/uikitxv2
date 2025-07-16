"""Callbacks for P&L Dashboard V2."""

from dash import callback, Output, Input
from dash import html
import logging
import plotly.graph_objects as go

from .controller import PnLDashboardController

logger = logging.getLogger(__name__)

# Initialize controller (singleton)
controller = PnLDashboardController()


def register_pnl_v2_callbacks():
    """Register all callbacks for P&L Dashboard V2."""
    
    @callback(
        [
            Output('pnl-v2-total-historic', 'children'),
            Output('pnl-v2-today-realized', 'children'),
            Output('pnl-v2-today-unrealized', 'children'),
            Output('pnl-v2-open-positions-count', 'children')
        ],
        Input('pnl-v2-interval-component', 'n_intervals')
    )
    def update_summary_cards(n_intervals):
        """Update summary metric cards."""
        metrics = controller.get_summary_metrics()
        
        return (
            metrics['total_historic_pnl'],
            metrics['todays_realized_pnl'],
            metrics['todays_unrealized_pnl'],
            str(metrics['open_positions'])
        )
    
    @callback(
        Output('pnl-v2-positions-content', 'children'),
        Input('pnl-v2-refresh-interval', 'n_intervals')
    )
    def update_positions_content(n_intervals):
        """Update positions tab content."""
        from .controller import controller
        from .views import create_open_positions_tab
        
        try:
            positions_df = controller.get_open_positions()
            return create_open_positions_tab(positions_df)
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            return html.Div(f"Error loading positions: {str(e)}", className="text-danger")
    
    @callback(
        Output('pnl-v2-trades-datatable', 'data'),
        Input('pnl-v2-interval-component', 'n_intervals')
    )
    def update_trades_table(n_intervals):
        """Update trade history table."""
        return controller.get_trades_data(limit=500)
    
    @callback(
        Output('pnl-v2-daily-datatable', 'data'),
        Input('pnl-v2-interval-component', 'n_intervals')
    )
    def update_daily_pnl_table(n_intervals):
        """Update daily P&L history table."""
        return controller.get_daily_pnl_data()
    
    @callback(
        Output('pnl-v2-chart', 'figure'),
        Input('pnl-v2-interval-component', 'n_intervals')
    )
    def update_pnl_chart(n_intervals):
        """Update P&L chart."""
        chart_data = controller.get_chart_data()
        
        # Create figure
        fig = go.Figure()
        
        # Add total P&L trace
        fig.add_trace(go.Scatter(
            x=chart_data['dates'],
            y=chart_data['cumulative_total'],
            mode='lines+markers',
            name='Total P&L',
            line=dict(color='blue', width=2),
            hovertemplate='%{x}<br>Total: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add realized P&L trace
        fig.add_trace(go.Scatter(
            x=chart_data['dates'],
            y=chart_data['cumulative_realized'],
            mode='lines',
            name='Realized P&L',
            line=dict(color='green', width=2, dash='dash'),
            hovertemplate='%{x}<br>Realized: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add unrealized P&L trace
        fig.add_trace(go.Scatter(
            x=chart_data['dates'],
            y=chart_data['cumulative_unrealized'],
            mode='lines',
            name='Unrealized P&L',
            line=dict(color='orange', width=2, dash='dot'),
            hovertemplate='%{x}<br>Unrealized: $%{y:,.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Cumulative P&L Over Time',
            xaxis_title='Date',
            yaxis_title='P&L ($)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig 