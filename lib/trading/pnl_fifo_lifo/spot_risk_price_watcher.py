"""
Spot Risk Price Watcher for PnL System

Purpose: Monitor spot risk CSV files and update current prices in trades.db
"""

import sqlite3
import pandas as pd
import logging
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from .data_manager import update_current_price

logger = logging.getLogger(__name__)


class SpotRiskFileHandler(FileSystemEventHandler):
    """Handle spot risk CSV file events."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.symbol_translator = SymbolTranslator()
        
    def on_created(self, event):
        """Handle new file creation."""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.csv'):
            filepath = Path(event.src_path)
            if filepath.name.startswith('bav_analysis_'):
                self._process_file(filepath)
                
    def _process_file(self, filepath: Path):
        """Process a spot risk CSV file."""
        try:
            # Check if already processed
            if self._is_file_processed(filepath):
                logger.debug(f"Skipping already processed file: {filepath.name}")
                return
                
            # Wait for file to be fully written
            if not self._wait_for_file_ready(filepath):
                logger.warning(f"File not ready after timeout: {filepath.name}")
                return
                
            logger.info(f"Processing spot risk file: {filepath.name}")
            
            # Extract timestamp from filename
            timestamp = self._extract_timestamp(filepath.name)
            if not timestamp:
                logger.error(f"Could not extract timestamp from filename: {filepath.name}")
                return
                
            # Read and process CSV
            df = pd.read_csv(filepath, skiprows=[1])  # Skip type row
            df.columns = df.columns.str.lower()
            
            # Extract prices
            prices = self._extract_prices(df)
            logger.info(f"Extracted {len(prices)} prices from {filepath.name}")
            
            # Update database
            if prices:
                self._update_database(prices, timestamp)
                
            # Mark as processed
            self._mark_file_processed(filepath, len(prices))
            
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}", exc_info=True)
            
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
        
    def _extract_timestamp(self, filename: str) -> Optional[datetime]:
        """Extract datetime from filename: bav_analysis_YYYYMMDD_HHMMSS.csv"""
        pattern = r'bav_analysis_(\d{8})_(\d{6})\.csv'
        match = re.search(pattern, filename)
        
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            return datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
        return None
        
    def _extract_prices(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract prices from dataframe using adjtheor or bid/ask midpoint."""
        prices = {}
        
        for _, row in df.iterrows():
            # Get instrument key
            instrument = row.get('key', row.get('instrument'))
            if not instrument:
                continue
                
            # Extract price - prefer adjtheor
            price = None
            adjtheor = row.get('adjtheor')
            
            if pd.notna(adjtheor) and str(adjtheor).upper() != 'INVALID':
                try:
                    price = float(adjtheor)
                except (ValueError, TypeError):
                    pass
                    
            # Fall back to bid/ask midpoint
            if price is None:
                bid = row.get('bid')
                ask = row.get('ask')
                
                if pd.notna(bid) and pd.notna(ask):
                    try:
                        price = (float(bid) + float(ask)) / 2
                    except (ValueError, TypeError):
                        pass
                elif pd.notna(ask):
                    try:
                        price = float(ask)
                    except (ValueError, TypeError):
                        pass
                elif pd.notna(bid):
                    try:
                        price = float(bid)
                    except (ValueError, TypeError):
                        pass
                        
            if price is not None:
                # Translate symbol to Bloomberg format
                bloomberg_symbol = self.symbol_translator.translate(instrument)
                if bloomberg_symbol:
                    prices[bloomberg_symbol] = price
                else:
                    logger.debug(f"Could not translate symbol: {instrument}")
                    
        return prices
        
    def _update_database(self, prices: Dict[str, float], timestamp: datetime):
        """Update prices in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            success_count = 0
            for symbol, price in prices.items():
                if update_current_price(conn, symbol, price, timestamp):
                    success_count += 1
                    
            logger.info(f"Updated {success_count}/{len(prices)} prices in database")
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
    
    def _is_file_processed(self, filepath: Path) -> bool:
        """Check if file has already been processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check processed_files table
        cursor.execute("""
            SELECT 1 FROM processed_files 
            WHERE file_path = ? AND last_modified = ?
        """, (str(filepath), filepath.stat().st_mtime))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
        
    def _mark_file_processed(self, filepath: Path, price_count: int):
        """Mark file as processed in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO processed_files 
            (file_path, processed_at, trade_count, last_modified)
            VALUES (?, ?, ?, ?)
        """, (
            str(filepath),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            price_count,  # Using price count instead of trade count
            filepath.stat().st_mtime
        ))
        
        conn.commit()
        conn.close()


class SymbolTranslator:
    """Translate ActantRisk symbols to Bloomberg format."""
    
    def __init__(self):
        # Month codes for futures
        self.month_codes = {
            'JAN': 'F', 'FEB': 'G', 'MAR': 'H', 'APR': 'J',
            'MAY': 'K', 'JUN': 'M', 'JUL': 'N', 'AUG': 'Q',
            'SEP': 'U', 'OCT': 'V', 'NOV': 'X', 'DEC': 'Z'
        }
        
        # Product mapping (update as needed)
        self.product_map = {
            'ZN': 'TY',  # 10-year Treasury Note
            'ZF': 'FV',  # 5-year Treasury Note
            'ZT': 'TU',  # 2-year Treasury Note
            'ZB': 'US',  # 30-year Treasury Bond
            # Add more mappings as needed
        }
        
    def translate(self, actant_symbol: str) -> Optional[str]:
        """
        Translate ActantRisk symbol to Bloomberg format.
        
        Examples:
            Future: XCME.ZN.SEP25 -> TYU5 Comdty
            Option: XCME.ZN.16JUL25.111.750.C -> TYU5C 111.750 Comdty
        """
        try:
            if not actant_symbol:
                return None
                
            parts = actant_symbol.split('.')
            
            if len(parts) < 3:
                return None
                
            # Extract components
            exchange = parts[0]  # XCME
            product = parts[1]   # ZN
            
            # Map product code
            bb_product = self.product_map.get(product, product)
            
            # Future format
            if len(parts) == 3:
                expiry = parts[2]  # SEP25
                month_str = expiry[:3]
                year_str = expiry[-1]  # Last digit for Bloomberg
                
                month_code = self.month_codes.get(month_str.upper())
                if not month_code:
                    return None
                    
                return f"{bb_product}{month_code}{year_str} Comdty"
                
            # Option format
            elif len(parts) >= 6:
                expiry_date = parts[2]  # 16JUL25
                strike = parts[3] + '.' + parts[4]  # 111.750
                call_put = parts[5]  # C or P
                
                # Parse expiry
                if len(expiry_date) >= 5:
                    month_str = expiry_date[-5:-2]
                    year_str = expiry_date[-1]
                    
                    month_code = self.month_codes.get(month_str.upper())
                    if not month_code:
                        return None
                        
                    return f"{bb_product}{month_code}{year_str}{call_put} {strike} Comdty"
                    
            return None
            
        except Exception as e:
            logger.debug(f"Error translating symbol {actant_symbol}: {e}")
            return None


class SpotRiskPriceWatcher:
    """Main watcher class for spot risk files."""
    
    def __init__(self, db_path: str, input_dir: str):
        self.db_path = db_path
        self.input_dir = Path(input_dir)
        self.observer = None
        self.handler = SpotRiskFileHandler(db_path)
        
    def start(self):
        """Start watching for files."""
        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {self.input_dir}")
            
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.input_dir), recursive=True)
        self.observer.start()
        logger.info(f"Started watching: {self.input_dir}")
        
    def stop(self):
        """Stop watching."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching")
            
    def run_forever(self):
        """Run the watcher continuously."""
        try:
            self.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop() 