"""Data aggregator for preparing P&L data for UI display."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class PnLDataAggregator:
    """Aggregates and formats P&L data for UI consumption."""
    
    def __init__(self, unified_service):
        """
        Initialize data aggregator.
        
        Args:
            unified_service: UnifiedPnLService instance
        """
        self.service = unified_service
        
    def format_positions_for_display(self, positions: List[Dict]) -> pd.DataFrame:
        """
        Format positions data for UI display.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            DataFrame with formatted positions
        """
        if not positions:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'Instrument', 'Position', 'Avg Price', 'Last Price',
                'Realized P&L', 'Unrealized P&L', 'Total P&L'
            ])
            
        # Convert to DataFrame
        df = pd.DataFrame(positions)
        
        # Calculate total_pnl if not present
        if 'total_pnl' not in df.columns:
            df['total_pnl'] = df['total_realized_pnl'].fillna(0) + df['unrealized_pnl'].fillna(0)
        
        # Rename columns for display
        column_mapping = {
            'instrument_name': 'Instrument',
            'position_quantity': 'Position',
            'avg_cost': 'Avg Price',
            'last_market_price': 'Last Price',
            'total_realized_pnl': 'Realized P&L',
            'unrealized_pnl': 'Unrealized P&L',
            'total_pnl': 'Total P&L'
        }
        
        # Ensure all required columns exist before selecting
        for col in column_mapping.keys():
            if col not in df.columns:
                if col == 'last_market_price':
                    # Use avg_cost as fallback if no market price
                    df[col] = df['avg_cost'] if 'avg_cost' in df.columns else 0
                else:
                    df[col] = 0
        
        # Select and rename columns
        display_columns = list(column_mapping.keys())
        df = df[display_columns].rename(columns=column_mapping)
        
        # Format numeric columns
        numeric_columns = ['Position', 'Avg Price', 'Last Price', 
                          'Realized P&L', 'Unrealized P&L', 'Total P&L']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(5)
                
        return df
        
    def format_trades_for_display(self, trades: List[Dict]) -> pd.DataFrame:
        """
        Format trade history for UI display.
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            DataFrame with formatted trades
        """
        if not trades:
            return pd.DataFrame(columns=[
                'Date', 'Time', 'Symbol', 'Type', 'Quantity', 
                'Price', 'SOD', 'Expired'
            ])
            
        df = pd.DataFrame(trades)
        
        # Create display columns
        df['Date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
        df['Time'] = df['trade_time']
        df['Symbol'] = df['bloomberg_symbol']
        df['Type'] = df['instrument_type']
        df['Quantity'] = df['quantity']
        df['Price'] = df['price'].round(5)
        df['SOD'] = df['is_sod'].map({1: 'Yes', 0: 'No'})
        df['Expired'] = df['is_expired'].map({1: 'Yes', 0: 'No'})
        
        # Select display columns
        display_columns = ['Date', 'Time', 'Symbol', 'Type', 
                          'Quantity', 'Price', 'SOD', 'Expired']
        
        return df[display_columns]
        
    def format_daily_pnl_for_display(self, daily_pnl: List[Dict]) -> pd.DataFrame:
        """
        Format daily P&L history for UI display.
        
        Args:
            daily_pnl: List of daily P&L records
            
        Returns:
            DataFrame with formatted daily P&L
        """
        if not daily_pnl:
            return pd.DataFrame(columns=[
                'Date', 'SOD Realized', 'SOD Unrealized',
                'EOD Realized', 'EOD Unrealized', 
                'Daily Realized Δ', 'Daily Unrealized Δ'
            ])
            
        df = pd.DataFrame(daily_pnl)
        
        # Format date
        df['Date'] = pd.to_datetime(df['trading_date']).dt.strftime('%Y-%m-%d')
        
        # Rename columns
        column_mapping = {
            'sod_realized': 'SOD Realized',
            'sod_unrealized': 'SOD Unrealized',
            'eod_realized': 'EOD Realized',
            'eod_unrealized': 'EOD Unrealized',
            'daily_realized_change': 'Daily Realized Δ',
            'daily_unrealized_change': 'Daily Unrealized Δ'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Format numeric columns
        numeric_columns = ['SOD Realized', 'SOD Unrealized', 
                          'EOD Realized', 'EOD Unrealized',
                          'Daily Realized Δ', 'Daily Unrealized Δ']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
                
        # Select display columns in order
        display_columns = ['Date'] + numeric_columns
        
        return df[display_columns]
        
    def get_summary_metrics(self) -> Dict[str, any]:
        """
        Get summary metrics for the dashboard cards.
        
        Returns:
            Dictionary with formatted summary metrics
        """
        # Get total historic P&L
        historic_pnl = self.service.get_total_historic_pnl()
        
        # Get today's P&L
        todays_pnl = self.service.get_todays_pnl()
        
        # Get position count
        positions = self.service.get_open_positions()
        open_position_count = len([p for p in positions if p.get('position_quantity', 0) != 0])
        
        return {
            'total_historic_pnl': f"${historic_pnl['total_pnl']:,.2f}",
            'total_realized_pnl': f"${historic_pnl['total_realized']:,.2f}",
            'total_unrealized_pnl': f"${historic_pnl['total_unrealized']:,.2f}",
            'todays_realized_pnl': f"${todays_pnl['realized']:,.2f}",
            'todays_unrealized_pnl': f"${todays_pnl['unrealized']:,.2f}",
            'todays_total_pnl': f"${todays_pnl['total']:,.2f}",
            'open_positions': open_position_count
        }
        
    def prepare_chart_data(self) -> Dict[str, List]:
        """
        Prepare data for P&L chart visualization.
        
        Returns:
            Dictionary with chart data
        """
        daily_pnl = self.service.get_daily_pnl_history()
        
        if not daily_pnl:
            return {
                'dates': [],
                'cumulative_realized': [],
                'cumulative_unrealized': [],
                'cumulative_total': []
            }
            
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(daily_pnl)
        df['trading_date'] = pd.to_datetime(df['trading_date'])
        df = df.sort_values('trading_date')
        
        # Calculate cumulative P&L
        df['cumulative_realized'] = df['eod_realized'].cumsum()
        df['cumulative_unrealized'] = df['eod_unrealized']
        df['cumulative_total'] = df['cumulative_realized'] + df['cumulative_unrealized']
        
        return {
            'dates': df['trading_date'].dt.strftime('%Y-%m-%d').tolist(),
            'cumulative_realized': df['cumulative_realized'].round(2).tolist(),
            'cumulative_unrealized': df['cumulative_unrealized'].round(2).tolist(),
            'cumulative_total': df['cumulative_total'].round(2).tolist()
        } 