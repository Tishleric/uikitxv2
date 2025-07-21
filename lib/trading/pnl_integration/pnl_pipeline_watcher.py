#!/usr/bin/env python3
"""
PNL Pipeline Watcher - Monitors for changes and triggers TYU5 pipeline.

This watcher monitors:
1. Trade ledger CSV files for creation/modification
2. Market prices database for updates

When changes are detected, it triggers the full TYU5 pipeline.
"""

import logging
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Set, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

logger = logging.getLogger(__name__)


class SpotRiskHandler(FileSystemEventHandler):
    """Handles spot risk CSV file events for FULLPNL updates."""
    
    def __init__(self, trigger_callback):
        """
        Initialize the handler.
        
        Args:
            trigger_callback: Function to call when CSV is created/modified
        """
        self.trigger_callback = trigger_callback
        self.processed_files: Set[str] = set()
        self.debounce_time = 10  # seconds
        self.last_event_time = 0
        
    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.csv'):
            self._handle_csv_event(event.src_path, "created")
            
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith('.csv'):
            self._handle_csv_event(event.src_path, "modified")
            
    def _handle_csv_event(self, file_path: str, event_type: str):
        """Handle CSV file events with debouncing."""
        try:
            file_path_obj = Path(file_path)
            file_key = f"{file_path_obj.name}:{file_path_obj.stat().st_mtime}"
            
            # Check if already processed
            if file_key in self.processed_files:
                return
                
            # Add debouncing for rapid file changes
            current_time = time.time()
            if current_time - self.last_event_time < self.debounce_time:
                logger.debug(f"Debouncing spot risk event: {file_path_obj.name}")
                return
                
            self.processed_files.add(file_key)
            self.last_event_time = current_time
            
            logger.info(f"Spot risk CSV {event_type}: {file_path_obj.name}")
            self.trigger_callback("spot_risk")
            
        except Exception as e:
            logger.error(f"Error handling spot risk event for {file_path}: {e}")


class PNLPipelineHandler(FileSystemEventHandler):
    """Handles file system events for trade ledger files."""
    
    def __init__(self, trigger_callback):
        """
        Initialize the handler.
        
        Args:
            trigger_callback: Function to call when a change is detected
        """
        self.trigger_callback = trigger_callback
        self.processed_files: Set[str] = set()
        self.debounce_seconds = 10  # Wait 10 seconds before triggering
        self.pending_trigger = False
        self.last_event_time = None
        self.trigger_thread = None
        
    def _is_trade_ledger_file(self, file_path: Path) -> bool:
        """Check if file is a trade ledger file."""
        name = file_path.name.lower()
        return (name.startswith('trades_') and 
                name.endswith('.csv') and
                file_path.exists() and
                file_path.stat().st_size > 0)
    
    def _debounced_trigger(self):
        """Trigger the callback after debounce period."""
        while self.pending_trigger:
            # Wait for debounce period
            time.sleep(self.debounce_seconds)
            
            # Check if enough time has passed since last event
            if self.last_event_time and (time.time() - self.last_event_time) >= self.debounce_seconds:
                self.pending_trigger = False
                logger.info("Debounce period complete, triggering pipeline")
                try:
                    self.trigger_callback('trade_ledger')
                except Exception as e:
                    logger.error(f"Error in trigger callback: {e}")
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self._is_trade_ledger_file(file_path):
            logger.info(f"New trade ledger file detected: {file_path.name}")
            self._trigger_update()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self._is_trade_ledger_file(file_path):
            # Check if we've already processed this exact file state
            file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
            if file_key not in self.processed_files:
                logger.info(f"Trade ledger file modified: {file_path.name}")
                self.processed_files.add(file_key)
                self._trigger_update()
    
    def _trigger_update(self):
        """Trigger an update with debouncing."""
        self.last_event_time = time.time()
        
        if not self.pending_trigger:
            self.pending_trigger = True
            # Start debounce thread
            self.trigger_thread = threading.Thread(target=self._debounced_trigger)
            self.trigger_thread.daemon = True
            self.trigger_thread.start()
        else:
            logger.debug("Update already pending, resetting debounce timer")


class MarketPriceMonitor:
    """Monitors market prices database for updates."""
    
    def __init__(self, db_path: str, trigger_callback):
        """
        Initialize the market price monitor.
        
        Args:
            db_path: Path to market prices database
            trigger_callback: Function to call when prices are updated
        """
        self.db_path = db_path
        self.trigger_callback = trigger_callback
        self.last_update_time = None
        self.check_interval = 10  # Check every 10 seconds
        self.monitoring = False
        self.monitor_thread = None
        
    def start(self):
        """Start monitoring market prices."""
        if self.monitoring:
            logger.warning("Market price monitor already running")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Market price monitor started")
        
    def stop(self):
        """Stop monitoring market prices."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Market price monitor stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop."""
        import sqlite3
        
        while self.monitoring:
            try:
                # Check for updates
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get the most recent update timestamp from both tables
                cursor.execute("""
                    SELECT MAX(last_update) as last_update FROM (
                        SELECT MAX(last_updated) as last_update FROM futures_prices
                        UNION ALL
                        SELECT MAX(last_updated) as last_update FROM options_prices
                    )
                """)
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    new_update_time = datetime.fromisoformat(result[0])
                    
                    # First run - initialize
                    if self.last_update_time is None:
                        self.last_update_time = new_update_time
                        logger.info(f"Market price monitor initialized. Last update: {new_update_time}")
                    
                    # Check if prices have been updated
                    elif new_update_time > self.last_update_time:
                        logger.info(f"Market price update detected: {self.last_update_time} -> {new_update_time}")
                        self.last_update_time = new_update_time
                        self.trigger_callback('market_prices')
                        
            except Exception as e:
                logger.error(f"Error checking market prices: {e}")
                
            # Wait before next check
            time.sleep(self.check_interval)


class PNLPipelineWatcher:
    """Main watcher service for PNL pipeline triggers."""
    
    def __init__(self, 
                 trade_ledger_dir: str = "data/input/trade_ledger",
                 market_prices_db: str = "data/output/market_prices/market_prices.db",
                 spot_risk_dir: str = "data/output/spot_risk"):
        """
        Initialize the pipeline watcher.
        
        Args:
            trade_ledger_dir: Directory containing trade ledger files
            market_prices_db: Path to market prices database
            spot_risk_dir: Directory to monitor for spot risk CSV files
        """
        self.trade_ledger_dir = Path(trade_ledger_dir)
        self.market_prices_db = Path(market_prices_db)
        self.spot_risk_dir = Path(spot_risk_dir)
        
        # Create directories if needed
        self.trade_ledger_dir.mkdir(parents=True, exist_ok=True)
        self.spot_risk_dir.mkdir(parents=True, exist_ok=True)
        
        # File watcher components
        self.trade_observer = Observer()  # For trade ledger
        self.spot_observer = Observer()   # For spot risk
        
        self.trade_handler = PNLPipelineHandler(self._trigger_pipeline)
        self.spot_risk_handler = SpotRiskHandler(self._trigger_fullpnl_only)
        
        # Market price monitor
        self.price_monitor = MarketPriceMonitor(str(self.market_prices_db), self._trigger_pipeline)
        
        # Pipeline control
        self.pipeline_lock = threading.Lock()
        self.last_pipeline_run = None
        self.last_fullpnl_run = None
        self.is_running = False
    
    def _trigger_fullpnl_only(self, source: str):
        """Trigger only FULLPNL update (for spot risk changes).
        
        Args:
            source: What triggered the update ('spot_risk')
        """
        with self.pipeline_lock:
            # Prevent concurrent runs
            if self.last_fullpnl_run and (time.time() - self.last_fullpnl_run) < 5:
                logger.debug("FULLPNL update too recent, skipping")
                return
                
            logger.info(f"Triggering FULLPNL update (source: {source})")
            self.last_fullpnl_run = time.time()
            
            # Run in a separate thread
            thread = threading.Thread(target=self._run_fullpnl_only, args=(source,))
            thread.daemon = True
            thread.start()
    
    def _run_fullpnl_only(self, source: str):
        """Run only FULLPNL table update."""
        try:
            logger.info(f"Running FULLPNL update triggered by: {source}")
            
            from .fullpnl_builder import FULLPNLBuilder
            fullpnl_builder = FULLPNLBuilder()
            success = fullpnl_builder.build_fullpnl()
            
            if success:
                logger.info("FULLPNL update completed successfully")
            else:
                logger.error("FULLPNL update failed")
                
        except Exception as e:
            logger.error(f"Error running FULLPNL update: {e}")
            import traceback
            traceback.print_exc()
        
    def start(self):
        """Start watching for changes."""
        if self.is_running:
            logger.warning("Pipeline watcher already running")
            return
            
        logger.info(f"Starting PNL Pipeline Watcher")
        logger.info(f"  - Watching trade ledgers: {self.trade_ledger_dir}")
        logger.info(f"  - Monitoring market prices: {self.market_prices_db}")
        logger.info(f"  - Watching spot risk: {self.spot_risk_dir}")
        
        # Start file watcher for trade ledgers
        self.trade_observer.schedule(self.trade_handler, str(self.trade_ledger_dir), recursive=False)
        self.trade_observer.start()
        
        # Start file watcher for spot risk
        self.spot_observer.schedule(self.spot_risk_handler, str(self.spot_risk_dir), recursive=False)
        self.spot_observer.start()
        
        # Start market price monitor
        if self.market_prices_db.exists():
            self.price_monitor.start()
        else:
            logger.warning(f"Market prices database not found: {self.market_prices_db}")
            
        self.is_running = True
        logger.info("PNL Pipeline Watcher started successfully")
        
        # Process existing files on startup
        self._process_existing_files()
        
    def stop(self):
        """Stop watching for changes."""
        if not self.is_running:
            return
            
        logger.info("Stopping PNL Pipeline Watcher...")
        
        # Stop file observers
        self.trade_observer.stop()
        self.trade_observer.join(timeout=5)
        
        self.spot_observer.stop()
        self.spot_observer.join(timeout=5)
        
        # Stop price monitor
        self.price_monitor.stop()
        
        self.is_running = False
        logger.info("PNL Pipeline Watcher stopped")
        
    def _process_existing_files(self):
        """Check for existing trade ledger files on startup."""
        logger.info("Checking for existing trade ledger files...")
        
        # Find all trade ledger files
        files = list(self.trade_ledger_dir.glob("trades_*.csv"))
        if files:
            logger.info(f"Found {len(files)} existing trade ledger files")
            # Mark them as processed to avoid immediate trigger
            for file_path in files:
                file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
                self.trade_handler.processed_files.add(file_key)
        else:
            logger.info("No existing trade ledger files found")
            
    def _trigger_pipeline(self, source: str):
        """Trigger the TYU5 pipeline.
        
        Args:
            source: What triggered the pipeline ('trade_ledger' or 'market_prices')
        """
        with self.pipeline_lock:
            # Prevent concurrent runs
            if self.last_pipeline_run and (time.time() - self.last_pipeline_run) < 5:
                logger.debug("Pipeline run too recent, skipping")
                return
                
            logger.info(f"Triggering TYU5 pipeline (source: {source})")
            self.last_pipeline_run = time.time()
            
            # Run in a separate thread to avoid blocking watchers
            thread = threading.Thread(target=self._run_pipeline, args=(source,))
            thread.daemon = True
            thread.start()
            
    def _run_pipeline(self, source: str):
        """Run the TYU5 pipeline."""
        try:
            # Import and run the pipeline inline to avoid circular dependencies
            import sys
            from pathlib import Path
            
            # Add scripts directory to path if needed
            scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            # Now we can import and run
            from run_tyu5_pipeline_direct import run_tyu5_pipeline
            
            logger.info(f"Running TYU5 pipeline triggered by: {source}")
            success = run_tyu5_pipeline()
            
            if success:
                logger.info("TYU5 pipeline completed successfully")
            else:
                logger.error("TYU5 pipeline failed")
                
        except Exception as e:
            logger.error(f"Error running TYU5 pipeline: {e}")
            import traceback
            traceback.print_exc() 