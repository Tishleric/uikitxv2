"""Unified P&L service that orchestrates all components for the UI."""

import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pytz

from .storage import PnLStorage
from .position_manager import PositionManager
from .service import PnLService
from .trade_preprocessor import TradePreprocessor
from .price_watcher import PriceFileWatcher
from .trade_file_watcher import TradeFileWatcher

logger = logging.getLogger(__name__)


class UnifiedPnLService:
    """Unified service for P&L tracking dashboard."""
    
    def __init__(self, 
                 db_path: str,
                 trade_ledger_dir: str,
                 price_directories: List[str]):
        """
        Initialize unified P&L service.
        
        Args:
            db_path: Path to SQLite database
            trade_ledger_dir: Directory containing trade ledger files
            price_directories: List of directories to watch for price files
        """
        self.chicago_tz = pytz.timezone('America/Chicago')
        
        # Initialize storage
        self.storage = PnLStorage(db_path)
        
        # Initialize components
        self.position_manager = PositionManager(self.storage)
        self.price_processor = PnLService(self.storage)  # Use PnLService for market prices
        self.pnl_service = PnLService(self.storage)  # Use PnLService for market prices
        self.trade_preprocessor = TradePreprocessor(
            output_dir=None,  # We'll use default output directory
            enable_position_tracking=True,
            storage=self.storage
        )
        
        # Initialize file watchers (but don't start them yet)
        self.trade_watcher = None
        self.price_watcher = None
        self.trade_ledger_dir = trade_ledger_dir
        self.price_directories = price_directories
        self._watchers_started = False
        
        # Initialize TYU5 unified API for advanced features
        try:
            from lib.trading.pnl_integration.unified_pnl_api import UnifiedPnLAPI
            self.unified_api = UnifiedPnLAPI(db_path)
            self._tyu5_enabled = True
            logger.info("TYU5 unified API enabled - advanced features available")
        except ImportError:
            logger.warning("TYU5 unified API not available - advanced features disabled")
            self.unified_api = None
            self._tyu5_enabled = False
        
    def start_watchers(self):
        """Start file watchers for real-time updates."""
        if self._watchers_started:
            logger.warning("Watchers already started")
            return
            
        try:
            # Start trade file watcher
            self.trade_watcher.start()
            
            # Start price file watcher
            def price_callback(file_path: Path):
                """Process price file when detected."""
                try:
                    # Use PnLService to process market price files (populates market_prices table)
                    self.pnl_service.process_market_price_file(str(file_path))
                except Exception as e:
                    logger.error(f"Error processing price file {file_path}: {e}")
                    
            self.price_watcher.start()
            
            self._watchers_started = True
            logger.info("File watchers started successfully")
            
        except Exception as e:
            logger.error(f"Error starting watchers: {e}")
            raise
            
    def stop_watchers(self):
        """Stop file watchers."""
        if self.trade_watcher:
            self.trade_watcher.stop()
        if self.price_watcher:
            self.price_watcher.stop()
        self._watchers_started = False
        logger.info("File watchers stopped")
        
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions with current market prices.
        
        Returns:
            List of position dictionaries with fields:
            - instrument: Symbol
            - position: Quantity
            - avg_price: Average cost
            - last_price: Latest market price
            - realized_pnl: Realized P&L
            - unrealized_pnl: Unrealized P&L
            - total_pnl: Total P&L
        """
        # Update positions with latest market prices
        self.position_manager.update_market_prices()
        
        # Get updated positions
        return self.position_manager.get_positions()
        
    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get full trade history.
        
        Args:
            limit: Optional limit on number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id,
                trade_id,
                instrument_name,
                trade_date,
                trade_timestamp,
                quantity,
                price,
                side,
                source_file,
                processed_at
            FROM processed_trades
            ORDER BY trade_timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        
        trades = []
        for row in cursor.fetchall():
            trade = dict(zip(columns, row))
            # Add computed fields for UI
            trade['bloomberg_symbol'] = trade['instrument_name']  # Already translated
            trade['instrument_type'] = 'OPTION' if 'O' in trade['instrument_name'] else 'FUTURE'
            trade['is_sod'] = False  # TODO: check timestamp for midnight
            trade['is_expired'] = trade['price'] == 0.0
            trade['trade_time'] = str(trade['trade_timestamp']).split()[1] if trade['trade_timestamp'] else ''
            trades.append(trade)
            
        return trades
        
    def get_daily_pnl_history(self) -> List[Dict]:
        """
        Get daily P&L history with SOD/EOD snapshots.
        
        Returns:
            List of daily P&L records with fields:
            - date: Trading date
            - sod_realized: Start of day realized P&L
            - sod_unrealized: Start of day unrealized P&L  
            - eod_realized: End of day realized P&L
            - eod_unrealized: End of day unrealized P&L
            - daily_realized_change: Change in realized P&L
            - daily_unrealized_change: Change in unrealized P&L
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        # Get SOD and EOD snapshots paired by date
        query = """
            WITH daily_snapshots AS (
                SELECT 
                    DATE(snapshot_timestamp) as trading_date,
                    SUM(CASE WHEN snapshot_type = 'SOD' THEN total_realized_pnl ELSE 0 END) as sod_realized,
                    SUM(CASE WHEN snapshot_type = 'SOD' THEN unrealized_pnl ELSE 0 END) as sod_unrealized,
                    SUM(CASE WHEN snapshot_type = 'EOD' THEN total_realized_pnl ELSE 0 END) as eod_realized,
                    SUM(CASE WHEN snapshot_type = 'EOD' THEN unrealized_pnl ELSE 0 END) as eod_unrealized
                FROM position_snapshots
                GROUP BY DATE(snapshot_timestamp)
            )
            SELECT 
                trading_date,
                sod_realized,
                sod_unrealized,
                eod_realized,
                eod_unrealized,
                (eod_realized - sod_realized) as daily_realized_change,
                (eod_unrealized - sod_unrealized) as daily_unrealized_change
            FROM daily_snapshots
            ORDER BY trading_date DESC
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        
        daily_pnl = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            daily_pnl.append(record)
            
        return daily_pnl
        
    def get_total_historic_pnl(self) -> Dict[str, float]:
        """
        Get total historic P&L to date.
        
        Returns:
            Dictionary with:
            - total_realized: Total realized P&L
            - total_unrealized: Total unrealized P&L
            - total_pnl: Combined total
        """
        positions = self.get_open_positions()
        
        total_realized = sum(p.get('realized_pnl', 0) for p in positions)
        total_unrealized = sum(p.get('unrealized_pnl', 0) for p in positions)
        
        return {
            'total_realized': round(total_realized, 5),
            'total_unrealized': round(total_unrealized, 5),
            'total_pnl': round(total_realized + total_unrealized, 5)
        }
        
    def get_todays_pnl(self) -> Dict[str, float]:
        """
        Get today's P&L (realized and unrealized).
        
        Returns:
            Dictionary with:
            - realized: Today's realized P&L
            - unrealized: Today's unrealized P&L
            - total: Today's total P&L
        """
        now = datetime.now(self.chicago_tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's realized P&L from positions
        # Since we track cumulative realized P&L in positions table,
        # we need to calculate today's realized by looking at position changes
        positions = self.get_open_positions()
        
        # For now, we'll use the total realized P&L
        # TODO: Implement proper daily realized P&L tracking
        todays_realized = sum(p.get('total_realized_pnl', 0) for p in positions)
        todays_unrealized = sum(p.get('unrealized_pnl', 0) for p in positions)
        
        return {
            'realized': round(todays_realized, 5),
            'unrealized': round(todays_unrealized, 5),
            'total': round(todays_realized + todays_unrealized, 5)
        }
        
    # ===== TYU5 Advanced Features =====
    
    def get_positions_with_lots(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get positions with lot-level detail from TYU5 data.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of position dictionaries with lot details
        """
        if not self._tyu5_enabled:
            logger.warning("TYU5 features not available")
            return self.get_open_positions()  # Fallback to basic positions
            
        return self.unified_api.get_positions_with_lots(symbol)
        
    def get_portfolio_greeks(self) -> Dict[str, float]:
        """Get aggregated portfolio-level Greeks.
        
        Returns:
            Dictionary with total portfolio Greeks
        """
        if not self._tyu5_enabled:
            return {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_vega': 0.0,
                'total_theta': 0.0,
                'total_speed': 0.0,
                'option_count': 0,
                'last_update': None
            }
            
        return self.unified_api.get_portfolio_greeks()
        
    def get_greek_exposure(self, as_of: Optional[datetime] = None) -> List[Dict]:
        """Get current Greek exposure across all positions.
        
        Args:
            as_of: Optional timestamp (defaults to latest)
            
        Returns:
            List of dictionaries with Greek values by position
        """
        if not self._tyu5_enabled:
            return []
            
        df = self.unified_api.get_greek_exposure(as_of)
        return df.to_dict('records') if not df.empty else []
        
    def get_risk_scenarios(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get risk scenario analysis.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of scenario dictionaries
        """
        if not self._tyu5_enabled:
            return []
            
        df = self.unified_api.get_risk_scenarios(symbol)
        return df.to_dict('records') if not df.empty else []
        
    def get_comprehensive_position_view(self, symbol: str) -> Dict:
        """Get comprehensive view of a position including all advanced features.
        
        Args:
            symbol: Position symbol
            
        Returns:
            Dictionary with complete position information
        """
        if not self._tyu5_enabled:
            # Return basic position info
            positions = [p for p in self.get_open_positions() if p['instrument'] == symbol]
            return positions[0] if positions else None
            
        return self.unified_api.get_comprehensive_position_view(symbol)
        
    def get_portfolio_summary_enhanced(self) -> Dict:
        """Get comprehensive portfolio summary with TYU5 features.
        
        Returns:
            Dictionary with enhanced portfolio-level metrics
        """
        basic_summary = {
            'positions': self.get_open_positions(),
            'todays_pnl': self.get_todays_pnl()
        }
        
        if not self._tyu5_enabled:
            return basic_summary
            
        # Add TYU5 enhanced data
        enhanced_summary = self.unified_api.get_portfolio_summary()
        enhanced_summary['basic'] = basic_summary
        
        return enhanced_summary 