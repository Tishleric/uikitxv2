"""
Price Update Trigger for TYU5 P&L Calculations

Monitors for price updates in the market_prices database and triggers
TYU5 P&L recalculation when prices change.
"""

import logging
from datetime import datetime
from typing import Optional, Set
import threading
import time

from lib.monitoring.decorators import monitor

logger = logging.getLogger(__name__)


class PriceUpdateTrigger:
    """Monitors price updates and triggers P&L recalculation."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize price update trigger.
        
        Args:
            check_interval: Seconds between price update checks
        """
        self.check_interval = check_interval
        self.last_check_time = None
        self.last_price_update = None
        self.monitoring = False
        self.monitor_thread = None
        self._tyu5_service = None  # Lazy load to avoid circular import
        
    @property
    def tyu5_service(self):
        """Lazy load TYU5Service to avoid circular import."""
        if self._tyu5_service is None:
            from lib.trading.pnl_integration.tyu5_service import TYU5Service
            # Initialize TYU5 without Greeks/attribution for speed
            self._tyu5_service = TYU5Service(enable_attribution=False)
        return self._tyu5_service
    
    @monitor()
    def check_for_updates(self) -> bool:
        """
        Check if prices have been updated since last check.
        
        Returns:
            True if prices were updated
        """
        try:
            # Query market_prices table for most recent update
            from lib.trading.market_prices.storage import MarketPriceStorage
            storage = MarketPriceStorage()
            
            # Get the most recent price update timestamp
            with storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(created_at) as last_update
                    FROM market_prices
                """)
                result = cursor.fetchone()
                
            if result and result['last_update']:
                new_update_time = datetime.fromisoformat(result['last_update'])
                
                # First run - initialize last update time
                if self.last_price_update is None:
                    self.last_price_update = new_update_time
                    logger.info(f"Initialized price monitor. Last update: {new_update_time}")
                    return False
                
                # Check if prices have been updated
                if new_update_time > self.last_price_update:
                    logger.info(f"Price update detected: {self.last_price_update} -> {new_update_time}")
                    self.last_price_update = new_update_time
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking for price updates: {e}")
            return False
    
    @monitor()
    def trigger_pnl_calculation(self):
        """Trigger TYU5 P&L calculation after price update."""
        try:
            logger.info("Triggering TYU5 P&L calculation due to price update...")
            excel_path = self.tyu5_service.calculate_pnl()
            
            if excel_path:
                logger.info(f"TYU5 calculation completed: {excel_path}")
            else:
                logger.warning("TYU5 calculation returned no output file")
                
        except Exception as e:
            logger.error(f"Failed to trigger TYU5 calculation: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop running in separate thread."""
        logger.info(f"Starting price update monitor (interval: {self.check_interval}s)")
        
        while self.monitoring:
            try:
                # Check for updates
                if self.check_for_updates():
                    self.trigger_pnl_calculation()
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                
            # Sleep for the interval
            time.sleep(self.check_interval)
            
        logger.info("Price update monitor stopped")
    
    def start(self):
        """Start monitoring for price updates."""
        if self.monitoring:
            logger.warning("Price monitor already running")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="PriceUpdateMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Price update monitor started")
    
    def stop(self):
        """Stop monitoring for price updates."""
        if not self.monitoring:
            return
            
        logger.info("Stopping price update monitor...")
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        logger.info("Price update monitor stopped") 