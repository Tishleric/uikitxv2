"""P&L Dashboard V2 - Controller for backend integration."""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from lib.trading.pnl_calculator.unified_service import UnifiedPnLService
from lib.trading.pnl_calculator.data_aggregator import PnLDataAggregator

logger = logging.getLogger(__name__)


class PnLDashboardController:
    """Controller for P&L Dashboard V2."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one controller instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the controller (only runs once due to singleton)."""
        if self._initialized:
            return
            
        # Configuration
        self.db_path = "data/output/pnl/pnl_tracker.db"  # Use the database with data
        self.trade_ledger_dir = "data/input/trade_ledger"
        self.price_directories = [
            "data/input/market_prices/futures",
            "data/input/market_prices/options"
        ]
        
        # Initialize services
        try:
            self.service = UnifiedPnLService(
                db_path=self.db_path,
                trade_ledger_dir=self.trade_ledger_dir,
                price_directories=self.price_directories
            )
            
            self.aggregator = PnLDataAggregator(self.service)
            
            # Start file watchers
            self.service.start_watchers()
            logger.info("P&L Dashboard Controller initialized successfully")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize P&L Dashboard Controller: {e}")
            raise
    
    def get_positions_data(self) -> Dict:
        """Get formatted positions data for display."""
        try:
            positions = self.service.get_open_positions()
            positions_df = self.aggregator.format_positions_for_display(positions)
            
            return {
                'data': positions_df.to_dict('records'),
                'count': len(positions_df)
            }
        except Exception as e:
            logger.error(f"Error getting positions data: {e}")
            return {'data': [], 'count': 0}
    
    def get_trades_data(self, limit: int = 500) -> List[Dict]:
        """Get formatted trade history data."""
        try:
            trades = self.service.get_trade_history(limit=limit)
            trades_df = self.aggregator.format_trades_for_display(trades)
            
            return trades_df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting trades data: {e}")
            return []
    
    def get_daily_pnl_data(self) -> List[Dict]:
        """Get formatted daily P&L history."""
        try:
            daily_pnl = self.service.get_daily_pnl_history()
            daily_df = self.aggregator.format_daily_pnl_for_display(daily_pnl)
            
            return daily_df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting daily P&L data: {e}")
            return []
    
    def get_summary_metrics(self) -> Dict:
        """Get summary metrics for dashboard cards."""
        try:
            return self.aggregator.get_summary_metrics()
        except Exception as e:
            logger.error(f"Error getting summary metrics: {e}")
            return {
                'total_historic_pnl': "$0.00",
                'total_realized_pnl': "$0.00",
                'total_unrealized_pnl': "$0.00",
                'todays_realized_pnl': "$0.00",
                'todays_unrealized_pnl': "$0.00",
                'todays_total_pnl': "$0.00",
                'open_positions': 0
            }
    
    def get_chart_data(self) -> Dict:
        """Get data for P&L chart."""
        try:
            return self.aggregator.prepare_chart_data()
        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return {
                'dates': [],
                'cumulative_realized': [],
                'cumulative_unrealized': [],
                'cumulative_total': []
            }
    
    def stop(self):
        """Stop file watchers when shutting down."""
        try:
            if hasattr(self, 'service'):
                self.service.stop_watchers()
                logger.info("P&L Dashboard Controller stopped")
        except Exception as e:
            logger.error(f"Error stopping controller: {e}") 