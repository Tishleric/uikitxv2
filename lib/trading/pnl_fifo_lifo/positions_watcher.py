"""
Positions Watcher Module

Purpose: Monitor trades.db and spot_risk.db for changes and update POSITIONS table
"""

import sqlite3
import logging
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Set, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .positions_aggregator import PositionsAggregator
from .config import DB_NAME

logger = logging.getLogger(__name__)


class DatabaseChangeHandler(FileSystemEventHandler):
    """Handle database file modification events."""
    
    def __init__(self, db_type: str, callback):
        """
        Initialize handler.
        
        Args:
            db_type: 'trades' or 'spot_risk'
            callback: Function to call when database changes
        """
        self.db_type = db_type
        self.callback = callback
        self.last_modified = None
        
    def on_modified(self, event):
        """Handle file modification event."""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            # Debounce rapid changes
            current_time = time.time()
            if self.last_modified and (current_time - self.last_modified) < 1.0:
                return
                
            self.last_modified = current_time
            logger.debug(f"{self.db_type} database modified")
            self.callback(self.db_type)


class PositionsWatcher:
    """Main watcher for positions table updates."""
    
    def __init__(self, trades_db_path: Optional[str] = None, 
                 spot_risk_db_path: Optional[str] = None,
                 update_interval: float = 5.0):
        """
        Initialize positions watcher.
        
        Args:
            trades_db_path: Path to trades.db (default: lib/trading/pnl_fifo_lifo/trades.db)
            spot_risk_db_path: Path to spot_risk.db (default: data/output/spot_risk/spot_risk.db)
            update_interval: Minimum seconds between full updates
        """
        self.trades_db_path = trades_db_path or DB_NAME
        self.spot_risk_db_path = spot_risk_db_path or "data/output/spot_risk/spot_risk.db"
        self.update_interval = update_interval
        
        self.aggregator = PositionsAggregator(self.trades_db_path, self.spot_risk_db_path)
        self.observers = []
        self.pending_symbols: Set[str] = set()
        self.update_lock = threading.Lock()
        self.last_full_update = 0
        self.running = False
        
    def start(self):
        """Start watching databases."""
        self.running = True
        
        # Initial full update
        logger.info("Performing initial positions update...")
        self.aggregator.update_all_positions()
        
        # Set up file watchers
        self._setup_watchers()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("Positions watcher started")
        
    def stop(self):
        """Stop watching."""
        self.running = False
        
        for observer in self.observers:
            if observer.is_alive():
                observer.stop()
                observer.join()
                
        logger.info("Positions watcher stopped")
        
    def _setup_watchers(self):
        """Set up file system watchers for database files."""
        # Watch trades database
        if Path(self.trades_db_path).exists():
            trades_dir = Path(self.trades_db_path).parent
            trades_handler = DatabaseChangeHandler('trades', self._on_database_change)
            
            trades_observer = Observer()
            trades_observer.schedule(trades_handler, str(trades_dir), recursive=False)
            trades_observer.start()
            self.observers.append(trades_observer)
            
            logger.info(f"Watching trades database: {self.trades_db_path}")
        
        # Watch spot risk database
        if Path(self.spot_risk_db_path).exists():
            spot_risk_dir = Path(self.spot_risk_db_path).parent
            spot_risk_handler = DatabaseChangeHandler('spot_risk', self._on_database_change)
            
            spot_risk_observer = Observer()
            spot_risk_observer.schedule(spot_risk_handler, str(spot_risk_dir), recursive=False)
            spot_risk_observer.start()
            self.observers.append(spot_risk_observer)
            
            logger.info(f"Watching spot risk database: {self.spot_risk_db_path}")
            
    def _on_database_change(self, db_type: str):
        """Handle database change notification."""
        # For now, trigger full update on any change
        # Future enhancement: detect which symbols changed
        with self.update_lock:
            self.pending_symbols.add('*')  # '*' indicates full update needed
            
    def _update_loop(self):
        """Background thread to process pending updates."""
        while self.running:
            try:
                # Check for pending updates
                if self.pending_symbols:
                    with self.update_lock:
                        symbols_to_update = self.pending_symbols.copy()
                        self.pending_symbols.clear()
                    
                    # Perform updates
                    if '*' in symbols_to_update:
                        # Full update requested
                        current_time = time.time()
                        if current_time - self.last_full_update >= self.update_interval:
                            logger.info("Performing full positions update...")
                            self.aggregator.update_all_positions()
                            self.last_full_update = current_time
                    else:
                        # Update specific symbols
                        for symbol in symbols_to_update:
                            self.aggregator.update_position(symbol)
                            
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Wait longer on error
                
    def update_symbol(self, symbol: str):
        """Manually trigger update for a specific symbol."""
        with self.update_lock:
            self.pending_symbols.add(symbol)
            
    def update_all(self):
        """Manually trigger full update."""
        with self.update_lock:
            self.pending_symbols.add('*')
            
    def run_forever(self):
        """Run the watcher continuously."""
        try:
            self.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    """Main entry point for running positions watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Positions table watcher')
    parser.add_argument('--trades-db', help='Path to trades.db')
    parser.add_argument('--spot-risk-db', help='Path to spot_risk.db')
    parser.add_argument('--update-interval', type=float, default=5.0,
                       help='Minimum seconds between full updates')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run watcher
    watcher = PositionsWatcher(
        trades_db_path=args.trades_db,
        spot_risk_db_path=args.spot_risk_db,
        update_interval=args.update_interval
    )
    
    watcher.run_forever()


if __name__ == '__main__':
    main() 