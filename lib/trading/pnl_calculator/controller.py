"""P&L Controller for Dashboard Integration

This controller acts as a thin wrapper around the P&L service,
focusing on data transformation for UI display.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import pandas as pd
from pathlib import Path

from .service import PnLService
from .storage import PnLStorage
from .watcher import PnLFileWatcher
from .models import Trade
from lib.monitoring.decorators import monitor

logger = logging.getLogger(__name__)


class PnLController:
    """Controller for P&L dashboard functionality.
    
    This controller manages the interaction between the P&L service and
    the dashboard UI, handling data transformation and formatting.
    """
    
    def __init__(self, 
                 db_path: Optional[Path] = None,
                 trades_dir: Optional[Path] = None,
                 prices_dir: Optional[Path] = None):
        """Initialize the P&L controller.
        
        Args:
            db_path: Path to SQLite database (defaults to data/output/pnl/pnl_tracker.db)
            trades_dir: Directory to watch for trade CSV files
            prices_dir: Directory to watch for market price CSV files
        """
        # Use default paths if not provided
        if db_path is None:
            db_path = Path("data/output/pnl/pnl_tracker.db")
        if trades_dir is None:
            trades_dir = Path("data/input/trade_ledger")
        if prices_dir is None:
            prices_dir = Path("data/input/market_prices")
        
        # Store directories for later use
        self.trades_dir = trades_dir
        self.prices_dir = prices_dir
            
        # Create storage instance and service
        self.storage = PnLStorage(str(db_path))  # Convert Path to string
        self.service = PnLService(self.storage)
        
        # Create wrappers for callbacks that match expected signature
        def trade_callback_wrapper(file_path: str, file_type: str):
            self.service.process_trade_file(file_path)
            
        def price_callback_wrapper(file_path: str, file_type: str):
            self.service.process_market_price_file(file_path)
        
        # Create file watcher
        self.watcher = PnLFileWatcher(
            trade_callback=trade_callback_wrapper,
            price_callback=price_callback_wrapper
        )
        # Update watcher directories
        self.watcher.trade_dir = trades_dir
        self.watcher.price_dir = prices_dir
        
        # Track watcher status
        self.watcher_started = False
        
        logger.info(f"PnL controller initialized with db_path={db_path}")
    
    @monitor()
    def start_file_watchers(self) -> None:
        """Start the file watchers for trade and price updates."""
        self.watcher.start()
        self.watcher_started = True
    
    @monitor()
    def stop_file_watchers(self) -> None:
        """Stop the file watchers."""
        self.watcher.stop()
        self.watcher_started = False
    
    @monitor()
    def get_position_summary(self) -> List[Dict[str, Any]]:
        """Get current position summary formatted for UI display.
        
        Returns:
            List of position dictionaries with formatted fields for display
        """
        try:
            # Get position summary from service
            positions_df = self.service.get_position_summary()
            
            if positions_df.empty:
                return []
            
            # Transform for UI display
            ui_positions = []
            for _, row in positions_df.iterrows():
                # Calculate total P&L
                realized_pnl = row.get('realized_pnl', 0) or 0
                unrealized_pnl = row.get('unrealized_pnl', 0) or 0
                total_pnl = realized_pnl + unrealized_pnl
                
                ui_position = {
                    'instrument': row['instrument'],
                    'net_position': row.get('net_position', 0),
                    'avg_price': f"{row.get('avg_price', 0):.4f}",
                    'last_price': f"{row.get('last_price', 0):.4f}",
                    'realized_pnl': realized_pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'total_pnl': total_pnl,
                    # Add color coding
                    'realized_color': 'green' if realized_pnl >= 0 else 'red',
                    'unrealized_color': 'green' if unrealized_pnl >= 0 else 'red',
                    'total_color': 'green' if total_pnl >= 0 else 'red'
                }
                ui_positions.append(ui_position)
            
            # Sort by absolute total P&L (largest first)
            ui_positions.sort(key=lambda x: abs(x['total_pnl']), reverse=True)
            
            return ui_positions
            
        except Exception as e:
            logger.error(f"Error getting position summary: {e}")
            return []
    
    @monitor()
    def get_daily_pnl_summary(self) -> List[Dict[str, Any]]:
        """Get daily P&L summary formatted for UI display.
        
        Returns:
            List of daily P&L dictionaries with formatted fields
        """
        try:
            # Get EOD P&L data from storage
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                trade_date,
                COUNT(DISTINCT instrument) as instrument_count,
                COUNT(*) as position_count,
                SUM(realized_pnl) as total_realized_pnl,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(realized_pnl + unrealized_pnl) as total_pnl
            FROM eod_pnl
            GROUP BY trade_date
            ORDER BY trade_date DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            # Transform for UI display
            ui_daily_pnl = []
            for row in rows:
                ui_day = {
                    'date': row['trade_date'],
                    'realized_pnl': row['total_realized_pnl'] or 0,
                    'unrealized_pnl': row['total_unrealized_pnl'] or 0,
                    'total_pnl': row['total_pnl'] or 0,
                    'trade_count': row['position_count'],
                    # Add color coding
                    'realized_color': 'green' if row['total_realized_pnl'] >= 0 else 'red',
                    'unrealized_color': 'green' if row['total_unrealized_pnl'] >= 0 else 'red',
                    'total_color': 'green' if row['total_pnl'] >= 0 else 'red'
                }
                ui_daily_pnl.append(ui_day)
            
            return ui_daily_pnl
            
        except Exception as e:
            logger.error(f"Error getting daily P&L summary: {e}")
            return []
    
    @monitor()
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade history formatted for UI display.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries with formatted fields
        """
        try:
            # Get processed trades from storage
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                trade_id,
                instrument_name,
                market_trade_time,
                quantity,
                price
            FROM processed_trades
            ORDER BY market_trade_time DESC
            LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            # Transform for UI display
            ui_trades = []
            for row in rows:
                ui_trade = {
                    'trade_id': row['trade_id'],
                    'instrument': row['instrument_name'],
                    'timestamp': row['market_trade_time'],
                    'side': 'BUY' if row['quantity'] > 0 else 'SELL',
                    'quantity': abs(row['quantity']),
                    'price': f"{row['price']:.4f}",
                    'value': abs(row['quantity'] * row['price'])
                }
                ui_trades.append(ui_trade)
            
            return ui_trades
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    @monitor()
    def get_pnl_chart_data(self) -> Dict[str, Any]:
        """Get P&L data formatted for charting.
        
        Returns:
            Dictionary with chart data including dates, cumulative P&L, etc.
        """
        try:
            daily_pnl = self.get_daily_pnl_summary()
            
            if not daily_pnl:
                return {
                    'dates': [],
                    'cumulative_pnl': [],
                    'daily_pnl': [],
                    'realized_pnl': [],
                    'unrealized_pnl': []
                }
            
            # Sort by date for proper charting
            daily_pnl.sort(key=lambda x: x['date'])
            
            dates = []
            cumulative_pnl = []
            daily_pnl_values = []
            realized_pnl = []
            unrealized_pnl = []
            
            cumulative = 0
            for day in daily_pnl:
                dates.append(day['date'])
                daily_pnl_values.append(day['total_pnl'])
                realized_pnl.append(day['realized_pnl'])
                unrealized_pnl.append(day['unrealized_pnl'])
                cumulative += day['total_pnl']
                cumulative_pnl.append(cumulative)
            
            return {
                'dates': dates,
                'cumulative_pnl': cumulative_pnl,
                'daily_pnl': daily_pnl_values,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl
            }
            
        except Exception as e:
            logger.error(f"Error getting P&L chart data: {e}")
            return {
                'dates': [],
                'cumulative_pnl': [],
                'daily_pnl': [],
                'realized_pnl': [],
                'unrealized_pnl': []
            }
    
    @monitor()
    def get_watcher_status(self) -> Dict[str, Any]:
        """Get file watcher status for UI display.
        
        Returns:
            Dictionary with watcher status information
        """
        return {
            'trades_watcher_active': self.watcher_started and self.watcher._running,
            'prices_watcher_active': self.watcher_started and self.watcher._running,
            'trades_dir': str(self.trades_dir),
            'prices_dir': str(self.prices_dir)
        }
    
    @monitor()
    def refresh_pnl(self) -> bool:
        """Manually trigger P&L recalculation.
        
        Returns:
            True if refresh was successful
        """
        try:
            # Process any existing files
            if hasattr(self.watcher, 'process_existing_files'):
                self.watcher.process_existing_files()
            
            # Recalculate all P&L for today
            as_of = datetime.now()
            self.service._recalculate_all_pnl(as_of)
            
            return True
        except Exception as e:
            logger.error(f"Error refreshing P&L: {e}")
            return False
    
    @monitor()
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard header.
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            positions = self.get_position_summary()
            daily_pnl = self.get_daily_pnl_summary()
            
            # Calculate totals
            total_realized = sum(p['realized_pnl'] for p in positions)
            total_unrealized = sum(p['unrealized_pnl'] for p in positions)
            total_pnl = total_realized + total_unrealized
            
            # Get today's P&L
            today = date.today().isoformat()
            today_pnl = next((d for d in daily_pnl if d['date'] == today), None)
            today_total = today_pnl['total_pnl'] if today_pnl else 0
            
            return {
                'total_pnl': total_pnl,
                'total_pnl_color': 'green' if total_pnl >= 0 else 'red',
                'total_realized': total_realized,
                'total_realized_color': 'green' if total_realized >= 0 else 'red',
                'total_unrealized': total_unrealized,
                'total_unrealized_color': 'green' if total_unrealized >= 0 else 'red',
                'today_pnl': today_total,
                'today_pnl_color': 'green' if today_total >= 0 else 'red',
                'position_count': len(positions),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {
                'total_pnl': 0,
                'total_pnl_color': 'black',
                'total_realized': 0,
                'total_realized_color': 'black',
                'total_unrealized': 0,
                'total_unrealized_color': 'black',
                'today_pnl': 0,
                'today_pnl_color': 'black',
                'position_count': 0,
                'last_update': 'Error'
            } 