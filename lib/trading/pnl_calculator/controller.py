"""P&L Controller for Dashboard Integration

This controller acts as a thin wrapper around the P&L service,
focusing on data transformation for UI display.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path
import pytz

from .service import PnLService
from .storage import PnLStorage
from .watcher import PnLFileWatcher
from .trade_file_watcher import TradeFileWatcher
from .trade_preprocessor import TradePreprocessor
from .models import Trade
from .closed_position_tracker import ClosedPositionTracker
from lib.monitoring.decorators import monitor

logger = logging.getLogger(__name__)


def get_current_trading_day() -> date:
    """Get current trading day based on 5pm EST cutoff.
    
    Trading day runs from 5pm EST to 5pm EST.
    After 5pm, we're in the next trading day.
    
    Returns:
        date: Current trading day
    """
    # Get current time in EST
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    
    # If after 5pm EST, return tomorrow
    if now_est.hour >= 17:
        return (now_est + timedelta(days=1)).date()
    else:
        return now_est.date()


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
        
        # CTO_INTEGRATION: Create TradePreprocessor with position tracking enabled
        # This ensures trades are transformed to CTO format and stored in cto_trades table
        self.trade_preprocessor = TradePreprocessor(
            output_dir="data/output/trade_ledger_processed",
            enable_position_tracking=True,
            storage=self.storage
        )
        
        # Initialize closed position tracker
        self.closed_position_tracker = ClosedPositionTracker(str(db_path))
        
        # CTO_INTEGRATION: Use TradeFileWatcher instead of PnLFileWatcher for proper CTO processing
        # TradeFileWatcher uses TradePreprocessor which populates both processed_trades AND cto_trades
        self.trade_watcher = TradeFileWatcher(
            input_dir=str(trades_dir),
            output_dir="data/output/trade_ledger_processed"
        )
        # Replace the preprocessor in the watcher with our configured one
        self.trade_watcher.preprocessor = self.trade_preprocessor
        
        # Keep the original price watcher for market prices
        def price_callback_wrapper(file_path: str, file_type: str):
            self.service.process_market_price_file(file_path)
        
        # Create price file watcher (keep original functionality)
        self.watcher = PnLFileWatcher(
            trade_callback=lambda fp, ft: None,  # Trades handled by TradeFileWatcher
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
        # CTO_INTEGRATION: Start TradeFileWatcher for trades (populates cto_trades)
        self.trade_watcher.start()
        
        # Start price watcher
        self.watcher.start()
        self.watcher_started = True
        
        # Process any existing price files that were added while the system was down
        logger.info("Processing existing files on startup...")
        self.watcher.process_existing_files()
    
    @monitor()
    def stop_file_watchers(self) -> None:
        """Stop the file watchers."""
        # Stop trade watcher
        self.trade_watcher.stop()
        
        # Stop price watcher
        self.watcher.stop()
        self.watcher_started = False
    
    @monitor()
    def rebuild_database(self) -> None:
        """Drop and recreate all database tables, then reprocess all files.
        
        WARNING: This will delete all existing P&L data!
        """
        logger.warning("Rebuilding P&L database - all data will be deleted!")
        
        # Stop watchers if running
        if self.watcher_started:
            self.stop_file_watchers()
            
        # Drop and recreate tables
        self.storage.drop_and_recreate_tables()
        
        # Clear the service's processed files set
        self.service._processed_files.clear()
        
        # Start watchers and process existing files
        self.start_file_watchers()
        
        logger.info("Database rebuild complete")
    
    @monitor()
    def get_position_summary(self) -> List[Dict[str, Any]]:
        """Get current position summary formatted for UI display.
        
        Returns:
            List of position dictionaries with formatted fields for display
        """
        try:
            # Get current trading day
            trading_day = get_current_trading_day()
            trading_day_str = trading_day.isoformat()
            
            # Query positions from database (similar to daily P&L approach)
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            # Get the latest position and aggregate P&L for each instrument
            query = """
            WITH latest_positions AS (
                SELECT 
                    instrument_name,
                    closing_position as position,
                    CASE 
                        WHEN closing_position > 0 THEN COALESCE(avg_buy_price, 0)
                        WHEN closing_position < 0 THEN COALESCE(avg_sell_price, 0)
                        ELSE 0
                    END as avg_price,
                    unrealized_pnl,
                    trade_date,
                    ROW_NUMBER() OVER (PARTITION BY instrument_name ORDER BY trade_date DESC) as rn
                FROM eod_pnl
            ),
            realized_totals AS (
                SELECT 
                    instrument_name,
                    SUM(realized_pnl) as total_realized_pnl
                FROM eod_pnl
                GROUP BY instrument_name
            )
            SELECT 
                lp.instrument_name,
                lp.position,
                lp.avg_price,
                COALESCE(rt.total_realized_pnl, 0) as realized_pnl,
                lp.unrealized_pnl
            FROM latest_positions lp
            LEFT JOIN realized_totals rt ON lp.instrument_name = rt.instrument_name
            WHERE lp.rn = 1
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # If no EOD data, try latest snapshots for the day
            if not rows:
                snapshot_query = """
                SELECT 
                    instrument_name,
                    position,
                    avg_cost as avg_price,
                    market_price as last_price,
                    realized_pnl,
                    unrealized_pnl
                FROM pnl_snapshots
                WHERE DATE(snapshot_timestamp) = ?
                ORDER BY snapshot_timestamp DESC
                """
                cursor.execute(snapshot_query, (trading_day_str,))
                
                # Get latest snapshot per instrument
                seen_instruments = set()
                rows = []
                for row in cursor.fetchall():
                    if row['instrument_name'] not in seen_instruments:
                        rows.append(row)
                        seen_instruments.add(row['instrument_name'])
            
            conn.close()
            
            # Transform for UI display
            ui_positions = []
            for row in rows:
                # Get last trade price
                last_trade_price = self.storage.get_last_trade_price(
                    row['instrument_name'], 
                    trading_day
                )
                
                # Calculate total P&L
                realized_pnl = row['realized_pnl'] or 0
                unrealized_pnl = row['unrealized_pnl'] or 0
                
                # If we have a last trade price but no unrealized P&L, recalculate
                if last_trade_price and unrealized_pnl == 0 and row['position'] != 0:
                    avg_price = float(row['avg_price']) if row['avg_price'] else 0
                    if avg_price > 0:
                        unrealized_pnl = (last_trade_price - avg_price) * row['position']
                
                total_pnl = realized_pnl + unrealized_pnl
                
                # Skip zero positions
                if row['position'] == 0 and realized_pnl == 0 and unrealized_pnl == 0:
                    continue
                
                ui_position = {
                    'instrument': row['instrument_name'],
                    'net_position': row['position'],
                    'avg_price': f"{row['avg_price']:.4f}" if row['avg_price'] and row['avg_price'] != 0 else "0.0000",
                    'last_price': f"{last_trade_price:.4f}" if last_trade_price else "N/A",
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
    def update_closed_positions(self, trade_date: Optional[date] = None) -> None:
        """Update closed position quantities for the specified date.
        
        Args:
            trade_date: Date to calculate closed positions for (default: current trading day)
        """
        if trade_date is None:
            trade_date = get_current_trading_day()
            
        logger.info(f"Updating closed positions for {trade_date}")
        self.closed_position_tracker.update_positions_table_with_closed_quantities(trade_date)
    
    @monitor()
    def get_positions_with_closed(self) -> List[Dict[str, Any]]:
        """Get all positions including closed quantities.
        
        Returns:
            List of position dictionaries with closed_quantity field
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            instrument_name,
            position_quantity,
            closed_quantity,
            avg_cost,
            total_realized_pnl,
            unrealized_pnl,
            last_market_price,
            last_updated,
            is_option,
            option_strike,
            option_expiry
        FROM positions
        ORDER BY instrument_name
        """
        
        cursor.execute(query)
        positions = []
        
        for row in cursor.fetchall():
            positions.append({
                'symbol': row['instrument_name'],
                'open_position': row['position_quantity'],
                'closed_position': row['closed_quantity'],
                'avg_cost': row['avg_cost'],
                'realized_pnl': row['total_realized_pnl'],
                'unrealized_pnl': row['unrealized_pnl'],
                'last_price': row['last_market_price'],
                'last_updated': row['last_updated'],
                'is_option': row['is_option'],
                'strike': row['option_strike'],
                'expiry': row['option_expiry']
            })
        
        conn.close()
        return positions
    
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
                COUNT(DISTINCT instrument_name) as instrument_count,
                SUM(trades_count) as total_trades_count,  -- Sum actual trade counts
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
                    'trade_count': row['total_trades_count'] or 0,  # Use summed trade counts
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
                trade_timestamp,
                quantity,
                price,
                side,
                source_file
            FROM processed_trades
            ORDER BY source_file DESC, trade_timestamp DESC
            LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            # Transform for UI display with file grouping
            ui_trades = []
            current_file = None
            
            for row in rows:
                # Add header row when source file changes
                if current_file != row['source_file']:
                    current_file = row['source_file']
                    header_row = {
                        'trade_id': '',
                        'instrument': f"--- {current_file} ---",
                        'timestamp': '',
                        'side': '',
                        'quantity': '',
                        'price': '',
                        'value': '',
                        'is_header': True
                    }
                    ui_trades.append(header_row)
                
                # Add normal trade row
                ui_trade = {
                    'trade_id': row['trade_id'],
                    'instrument': row['instrument_name'],
                    'timestamp': row['trade_timestamp'],
                    'side': 'BUY' if row['side'] == 'B' else 'SELL',
                    'quantity': abs(row['quantity']),
                    'price': f"{row['price']:.4f}",
                    'value': abs(row['quantity'] * row['price']),
                    'is_header': False
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
            'trades_watcher_active': self.watcher_started and self.trade_watcher._running,
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
            # Process any existing trade files using preprocessor
            self.trade_preprocessor.process_all_files(str(self.trades_dir))
            
            # Process any existing price files
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
            
            # Calculate totals from positions (these are current active positions)
            total_realized = sum(p['realized_pnl'] for p in positions)
            total_unrealized = sum(p['unrealized_pnl'] for p in positions)
            total_pnl = total_realized + total_unrealized
            
            # Calculate today's P&L by summing all daily P&L
            # (since we're aggregating trades from multiple dates into one "trading day")
            today_total = sum(d['total_pnl'] for d in daily_pnl)
            
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
            return {}
    
    @monitor()
    def get_data_diagnostic(self, trade_date: Optional[date] = None) -> Dict[str, Any]:
        """Diagnostic method to check what data exists for a given date.
        
        Args:
            trade_date: Date to check (defaults to current trading day)
            
        Returns:
            Dictionary with diagnostic information
        """
        try:
            if trade_date is None:
                trade_date = get_current_trading_day()
            
            trade_date_str = trade_date.isoformat()
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            # Check processed trades
            cursor.execute(
                "SELECT COUNT(*) as count FROM processed_trades WHERE trade_date = ?",
                (trade_date_str,)
            )
            trade_count = cursor.fetchone()['count']
            
            # Check EOD P&L
            cursor.execute(
                "SELECT COUNT(*) as count FROM eod_pnl WHERE trade_date = ?",
                (trade_date_str,)
            )
            eod_count = cursor.fetchone()['count']
            
            # Check snapshots
            cursor.execute(
                "SELECT COUNT(*) as count FROM pnl_snapshots WHERE DATE(snapshot_timestamp) = ?",
                (trade_date_str,)
            )
            snapshot_count = cursor.fetchone()['count']
            
            # Get sample trades
            cursor.execute(
                """SELECT instrument_name, price, quantity, side, trade_timestamp 
                FROM processed_trades 
                WHERE trade_date = ? 
                LIMIT 5""",
                (trade_date_str,)
            )
            sample_trades = cursor.fetchall()
            
            conn.close()
            
            return {
                'trade_date': trade_date_str,
                'current_time': datetime.now().isoformat(),
                'processed_trades_count': trade_count,
                'eod_pnl_count': eod_count,
                'snapshot_count': snapshot_count,
                'sample_trades': sample_trades
            }
            
        except Exception as e:
            logger.error(f"Error in data diagnostic: {e}")
            return {'error': str(e)} 