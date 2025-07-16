"""TYU5 Service - Orchestrates P&L calculations

This service monitors data stores and triggers TYU5 calculations
when new data arrives.
"""

import logging
from datetime import datetime, date
from typing import Optional, Callable
from pathlib import Path
import threading
import time

from .tyu5_adapter import TYU5Adapter

logger = logging.getLogger(__name__)


class TYU5Service:
    """Service to manage TYU5 P&L calculations."""
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 output_dir: Optional[str] = None):
        """Initialize the service.
        
        Args:
            db_path: Path to SQLite database
            output_dir: Directory for output files (defaults to data/output/pnl)
        """
        self.adapter = TYU5Adapter(db_path)
        self.output_dir = Path(output_dir or "data/output/pnl")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitoring state
        self._monitoring = False
        self._monitor_thread = None
        self._last_calculation_time = None
        
    def calculate_pnl(self, 
                     trade_date: Optional[date] = None,
                     output_format: str = "excel") -> str:
        """Run P&L calculation for a specific date.
        
        Args:
            trade_date: Date to calculate (None for all)
            output_format: Output format ("excel" or "csv")
            
        Returns:
            Path to output file
        """
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = trade_date.strftime("%Y%m%d") if trade_date else "all"
        
        if output_format == "excel":
            output_file = self.output_dir / f"tyu5_pnl_{date_str}_{timestamp}.xlsx"
        else:
            output_file = self.output_dir / f"tyu5_pnl_{date_str}_{timestamp}.csv"
            
        # Run calculation
        logger.info(f"Starting TYU5 calculation for {trade_date or 'all dates'}")
        
        success = self.adapter.run_calculation(
            output_file=str(output_file),
            trade_date=trade_date
        )
        
        if success:
            self._last_calculation_time = datetime.now()
            logger.info(f"Calculation complete. Output: {output_file}")
            return str(output_file)
        else:
            logger.error("Calculation failed")
            return ""
            
    def print_summary(self, trade_date: Optional[date] = None):
        """Print calculation summary to console.
        
        Args:
            trade_date: Date to summarize (None for all)
        """
        # Get data
        excel_data = self.adapter.prepare_excel_data(trade_date)
        summary = self.adapter.get_calculation_summary(excel_data)
        
        # Print summary
        print("\n" + "="*60)
        print("TYU5 P&L CALCULATION SUMMARY")
        print("="*60)
        
        if 'error' in summary:
            print(f"ERROR: {summary['error']}")
            return
            
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Unique Symbols: {summary['unique_symbols']}")
        print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"  - Buys: {summary['total_buys']}")
        print(f"  - Sells: {summary['total_sells']}")
        print(f"  - Futures: {summary['futures_count']}")
        print(f"  - Options: {summary['options_count']}")
        print(f"Market Prices Loaded: {summary['prices_loaded']}")
        print("="*60)
        
    def start_monitoring(self, 
                        check_interval: int = 60,
                        callback: Optional[Callable] = None):
        """Start monitoring for new data.
        
        Args:
            check_interval: Seconds between checks
            callback: Optional callback when calculation completes
        """
        if self._monitoring:
            logger.warning("Monitoring already active")
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval, callback),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started monitoring with {check_interval}s interval")
        
    def stop_monitoring(self):
        """Stop monitoring for new data."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped monitoring")
        
    def _monitor_loop(self, interval: int, callback: Optional[Callable]):
        """Monitor loop that checks for new data.
        
        Args:
            interval: Seconds between checks
            callback: Optional callback function
        """
        last_check = {}
        
        while self._monitoring:
            try:
                # Check for new data (simplified for now)
                # In production, this would check row counts or timestamps
                
                # For now, just run calculation if we haven't in a while
                if self._last_calculation_time is None or \
                   (datetime.now() - self._last_calculation_time).seconds > interval:
                    
                    logger.info("Running scheduled calculation")
                    output_file = self.calculate_pnl()
                    
                    if output_file and callback:
                        callback(output_file)
                        
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                
            time.sleep(interval)
            
    def test_connection(self) -> bool:
        """Test database connection and data availability.
        
        Returns:
            True if connection successful and data available
        """
        try:
            # Try to get some data
            excel_data = self.adapter.prepare_excel_data()
            
            has_trades = not excel_data['Trades_Input'].empty
            has_prices = not excel_data['Market_Prices'].empty
            
            logger.info(f"Connection test: Trades={has_trades}, Prices={has_prices}")
            
            return has_trades or has_prices
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False 