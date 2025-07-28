"""
Trade Ledger File Watcher for PnL System

Purpose: Monitor trade ledger CSV files and feed new trades into the PnL FIFO/LIFO system
"""

import sqlite3
import pandas as pd
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from .data_manager import get_trading_day
from .pnl_engine import process_new_trade

# Import RosettaStone for symbol translation
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from lib.trading.market_prices.rosetta_stone import RosettaStone

logger = logging.getLogger(__name__)


class TradeLedgerFileHandler(FileSystemEventHandler):
    """Handle trade ledger CSV file events."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.translator = RosettaStone()
        
    def on_created(self, event):
        """Handle new file creation."""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.csv'):
            filepath = Path(event.src_path)
            if filepath.name.startswith('trades_'):
                self._process_file(filepath, from_line=0)
    
    def on_modified(self, event):
        """Handle file modification - process only new lines."""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith('.csv'):
            filepath = Path(event.src_path)
            if filepath.name.startswith('trades_'):
                self._process_modified_file(filepath)
                
    def _process_modified_file(self, filepath: Path):
        """Process only new lines in a modified file."""
        try:
            # Get last processed line
            last_line = self._get_last_processed_line(filepath)
            
            # If file has never been processed, process from beginning
            if last_line == -1:
                self._process_file(filepath, from_line=0)
                return
            
            # Check if there are new lines
            total_lines = sum(1 for _ in open(filepath)) - 1  # Subtract header
            if total_lines <= last_line:
                logger.debug(f"No new lines in {filepath.name}")
                return
            
            # Process only new lines
            new_lines_count = total_lines - last_line
            logger.info(f"Processing {new_lines_count} new lines in {filepath.name}")
            self._process_file(filepath, from_line=last_line)
            
        except Exception as e:
            logger.error(f"Error processing modified file {filepath}: {e}", exc_info=True)
                
    def _process_file(self, filepath: Path, from_line: int = 0):
        """Process a trade ledger CSV file starting from specified line."""
        try:
            # Wait for file to be fully written
            if not self._wait_for_file_ready(filepath):
                logger.warning(f"File not ready after timeout: {filepath.name}")
                return
                
            logger.info(f"Processing trade ledger file: {filepath.name} from line {from_line}")
            
            # Read CSV starting from specified line
            if from_line == 0:
                # Read entire file
                df = pd.read_csv(filepath)
            else:
                # Read only new lines
                df = pd.read_csv(filepath, skiprows=range(1, from_line + 1))
            
            if df.empty:
                logger.info(f"No new trades to process in {filepath.name}")
                return
            
            # Parse datetime and create sequenceId
            df['marketTradeTime'] = pd.to_datetime(df['marketTradeTime'])
            df['trading_day'] = df['marketTradeTime'].apply(get_trading_day)
            df['date'] = df['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the max sequence number for proper sequencing
            max_seq_query = """
                SELECT MAX(CAST(SUBSTR(sequenceId, INSTR(sequenceId, '-') + 1) AS INTEGER))
                FROM (
                    SELECT sequenceId FROM trades_fifo
                    UNION ALL
                    SELECT sequenceId FROM trades_lifo
                )
            """
            result = cursor.execute(max_seq_query).fetchone()
            start_seq = (result[0] or 0) + 1
            
            # Process each trade
            trade_count = 0
            for idx, row in df.iterrows():
                # Translate symbol to Bloomberg format
                bloomberg_symbol = self._translate_symbol(row['instrumentName'])
                if not bloomberg_symbol:
                    logger.warning(f"Could not translate symbol: {row['instrumentName']}")
                    bloomberg_symbol = row['instrumentName']  # Fallback to original
                
                trade = {
                    'transactionId': row['tradeId'],
                    'symbol': bloomberg_symbol,
                    'price': row['price'],
                    'quantity': row['quantity'],
                    'buySell': row['buySell'],
                    'sequenceId': f"{row['date']}-{start_seq + trade_count}",
                    'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'fullPartial': 'full'
                }
                
                # Process through both FIFO and LIFO
                for method in ['fifo', 'lifo']:
                    realized = process_new_trade(conn, trade, method, 
                                               row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
                    if realized:
                        logger.debug(f"{method.upper()}: {len(realized)} realizations for trade {row['tradeId']}")
                
                trade_count += 1
            
            # Update file tracking with new line count
            total_lines_processed = from_line + trade_count
            self._update_file_tracking(filepath, total_lines_processed)
            logger.info(f"Processed {trade_count} trades from {filepath.name}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}", exc_info=True)
            
    def _translate_symbol(self, actant_symbol: str) -> Optional[str]:
        """Translate ActantTrades symbol to Bloomberg format."""
        try:
            # Handle futures contracts (XCMEFFDPS...)
            if actant_symbol.startswith('XCMEFFDPS'):
                # Parse futures symbol: XCMEFFDPSX20250919U0ZN
                import re
                match = re.match(r'XCMEFFDPSX(\d{8})([A-Z])(\d)([A-Z]{2})', actant_symbol)
                if match:
                    date_str, month_code, _, series = match.groups()
                    
                    # Map to Bloomberg futures format
                    # For now, default to TYU5 format (10-year treasury)
                    # This should be enhanced with proper futures mapping
                    year = date_str[3]  # Get single digit year from YYYY
                    
                    # Common futures mappings
                    futures_map = {
                        'ZN': 'TY',  # 10-year Treasury Note
                        'TU': 'TU',  # 2-year
                        'FV': 'FV',  # 5-year
                        'US': 'US',  # Ultra Bond
                    }
                    
                    bloomberg_base = futures_map.get(series, 'TY')  # Default to TY
                    bloomberg_symbol = f"{bloomberg_base}{month_code}{year} Comdty"
                    logger.debug(f"Translated futures {actant_symbol} to {bloomberg_symbol}")
                    return bloomberg_symbol
            
            # Handle options using RosettaStone
            result = self.translator.translate(actant_symbol, 'actanttrades', 'bloomberg')
            return result
            
        except Exception as e:
            logger.debug(f"Translation error for {actant_symbol}: {e}")
            return None
            
    def _wait_for_file_ready(self, filepath: Path, timeout: int = 10) -> bool:
        """Wait for file to be fully written."""
        last_size = -1
        stable_count = 0
        
        for _ in range(timeout):
            try:
                current_size = filepath.stat().st_size
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:
                        return True
                else:
                    stable_count = 0
                last_size = current_size
                time.sleep(1)
            except OSError:
                time.sleep(1)
                
        return False
        
    def _get_last_processed_line(self, filepath: Path) -> int:
        """Get the last processed line number for a file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have line tracking for this file
        cursor.execute("""
            SELECT trade_count FROM processed_files 
            WHERE file_path = ?
        """, (str(filepath),))
        
        result = cursor.fetchone()
        conn.close()
        
        # Return -1 if never processed, otherwise return line count
        return result[0] if result and result[0] >= 0 else -1
        
    def _update_file_tracking(self, filepath: Path, lines_processed: int):
        """Update file tracking with line count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO processed_files 
            (file_path, processed_at, trade_count, last_modified)
            VALUES (?, ?, ?, ?)
        """, (
            str(filepath),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            lines_processed,  # Now represents line count, not trade count
            filepath.stat().st_mtime
        ))
        
        conn.commit()
        conn.close()


class TradeLedgerWatcher:
    """Main watcher class for trade ledger files."""
    
    def __init__(self, db_path: str, watch_dir: str):
        self.db_path = db_path
        self.watch_dir = Path(watch_dir)
        self.observer = None
        self.handler = TradeLedgerFileHandler(db_path)
        
    def start(self):
        """Start watching for files."""
        if not self.watch_dir.exists():
            raise ValueError(f"Watch directory does not exist: {self.watch_dir}")
            
        # Process any existing unprocessed files first
        self._process_existing_files()
        
        # Start watching for new files
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        logger.info(f"Started watching: {self.watch_dir}")
        
    def stop(self):
        """Stop watching."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching")
            
    def _process_existing_files(self):
        """Process any existing unprocessed files in the directory."""
        logger.info("Checking for existing unprocessed files...")
        
        for filepath in sorted(self.watch_dir.glob('trades_*.csv')):
            # Check if file has been processed (-1 means never processed)
            if self.handler._get_last_processed_line(filepath) == -1:
                logger.info(f"Found unprocessed file: {filepath.name}")
                self.handler._process_file(filepath)
                
    def run_forever(self):
        """Run the watcher continuously."""
        try:
            self.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop() 