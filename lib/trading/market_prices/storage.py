"""
Storage layer for market price data.

DEPRECATED: This module is being replaced by a new pricing infrastructure.
The market_prices.db has been removed as part of PnL system migration.

Handles database operations for futures and options prices with row-level tracking.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Tuple
from contextlib import contextmanager

from lib.monitoring.decorators import monitor
import pytz

# Constants
# DB_FILE_NAME = 'market_prices.db'  # REMOVED: market_prices.db deprecated
CHICAGO_TZ = pytz.timezone('America/Chicago')

logger = logging.getLogger(__name__)


class MarketPriceStorage:
    """
    Handles database storage for market price data.
    
    DEPRECATED: This class is being replaced by a new pricing infrastructure.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize storage with database path.
        
        Args:
            db_path: Path to database file (no longer has a default - must be explicitly provided)
        """
        if db_path is None:
            raise ValueError("db_path must be provided - market_prices.db has been removed")
            
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_database()
        
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    @monitor()
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Futures prices table - ACTIVE VERSION with Current_Price
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS futures_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date DATE NOT NULL,
                    symbol TEXT NOT NULL,
                    Current_Price REAL,
                    Flash_Close REAL,
                    prior_close REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, symbol)
                )
            """)
            
            # Options prices table - ACTIVE VERSION with Current_Price
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS options_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date DATE NOT NULL,
                    symbol TEXT NOT NULL,
                    Current_Price REAL,
                    Flash_Close REAL,
                    prior_close REAL,
                    expire_dt DATE,
                    moneyness REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, symbol)
                )
            """)
            
            # File processing tracker
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_file_tracker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_timestamp TIMESTAMP NOT NULL,
                    window_type TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    processed_rows INTEGER NOT NULL,
                    processing_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_completed_at TIMESTAMP,
                    UNIQUE(source_file)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_futures_trade_date 
                ON futures_prices(trade_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_options_trade_date 
                ON options_prices(trade_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_tracker_timestamp 
                ON price_file_tracker(file_timestamp)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    @monitor()
    def is_file_processed(self, filename: str) -> bool:
        """
        Check if a file has already been processed.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file has been processed, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM price_file_tracker WHERE source_file = ?",
                (filename,)
            )
            count = cursor.fetchone()[0]
            return count > 0
    
    @monitor()
    def record_file_processing(self, filename: str, file_type: str, 
                             file_timestamp: datetime, window_type: str,
                             total_rows: int) -> int:
        """
        Record that we're starting to process a file.
        
        Args:
            filename: Name of the file
            file_type: 'futures' or 'options'
            file_timestamp: Timestamp extracted from filename
            window_type: '2pm', '4pm', or '3pm'
            total_rows: Total number of rows in the file
            
        Returns:
            ID of the tracker record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO price_file_tracker 
                (source_file, file_type, file_timestamp, window_type, 
                 total_rows, processed_rows)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (filename, file_type, file_timestamp, window_type, total_rows))
            conn.commit()
            tracker_id = cursor.lastrowid
            if tracker_id is None:
                raise ValueError("Failed to create tracker record")
            return tracker_id
    
    @monitor()
    def update_file_processing_progress(self, tracker_id: int, processed_rows: int):
        """Update processing progress for a file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE price_file_tracker 
                SET processed_rows = ?
                WHERE id = ?
            """, (processed_rows, tracker_id))
            conn.commit()
    
    @monitor()
    def complete_file_processing(self, tracker_id: int):
        """Mark file processing as complete."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE price_file_tracker 
                SET processing_completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (tracker_id,))
            conn.commit()
    
    @monitor()
    def update_futures_flash_close(self, trade_date: date, symbol: str, price: float):
        """
        Update Flash_Close price for a futures contract.
        
        Args:
            trade_date: The trading date
            symbol: Bloomberg symbol (with U5 suffix)
            price: Flash close price from PX_LAST
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO futures_prices (trade_date, symbol, Flash_Close)
                VALUES (?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    Flash_Close = excluded.Flash_Close,
                    last_updated = CURRENT_TIMESTAMP
            """, (trade_date, symbol, price))
            conn.commit()
    
    @monitor()
    def insert_futures_prior_close(self, trade_date: date, symbol: str, prior_close: float):
        """
        Insert prior close for next trading day.
        
        Args:
            trade_date: The next trading date
            symbol: Bloomberg symbol (with U5 suffix)
            prior_close: Settlement price from PX_SETTLE
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO futures_prices (trade_date, symbol, prior_close)
                VALUES (?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    prior_close = excluded.prior_close,
                    last_updated = CURRENT_TIMESTAMP
            """, (trade_date, symbol, prior_close))
            conn.commit()
    
    @monitor()
    def update_options_flash_close(self, trade_date: date, symbol: str, price: float,
                                   expire_dt: Optional[date] = None, 
                                   moneyness: Optional[float] = None):
        """
        Update Flash_Close price for an option.
        
        Args:
            trade_date: The trading date
            symbol: Bloomberg symbol
            price: Flash close price from PX_LAST
            expire_dt: Expiration date
            moneyness: Moneyness value
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO options_prices 
                (trade_date, symbol, Flash_Close, expire_dt, moneyness)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    Flash_Close = excluded.Flash_Close,
                    expire_dt = CASE WHEN excluded.expire_dt IS NOT NULL THEN excluded.expire_dt ELSE expire_dt END,
                    moneyness = CASE WHEN excluded.moneyness IS NOT NULL THEN excluded.moneyness ELSE moneyness END,
                    last_updated = CURRENT_TIMESTAMP
            """, (trade_date, symbol, price, expire_dt, moneyness))
            conn.commit()
    
    @monitor()
    def insert_options_prior_close(self, trade_date: date, symbol: str, prior_close: float,
                                 expire_dt: Optional[date] = None,
                                 moneyness: Optional[float] = None):
        """
        Insert prior close for next trading day.
        
        Args:
            trade_date: The next trading date
            symbol: Bloomberg symbol
            prior_close: Settlement price from PX_SETTLE
            expire_dt: Expiration date
            moneyness: Moneyness value
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO options_prices 
                (trade_date, symbol, prior_close, expire_dt, moneyness)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    prior_close = excluded.prior_close,
                    expire_dt = CASE WHEN excluded.expire_dt IS NOT NULL THEN excluded.expire_dt ELSE expire_dt END,
                    moneyness = CASE WHEN excluded.moneyness IS NOT NULL THEN excluded.moneyness ELSE moneyness END,
                    last_updated = CURRENT_TIMESTAMP
            """, (trade_date, symbol, prior_close, expire_dt, moneyness))
            conn.commit()
    
    @monitor()
    def get_futures_prices(self, trade_date: date, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Get futures prices for a specific trade date.
        
        Args:
            trade_date: Trading date to query
            symbols: Optional list of symbols to filter
            
        Returns:
            List of price records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if symbols:
                placeholders = ','.join(['?' for _ in symbols])
                query = f"""
                    SELECT * FROM futures_prices 
                    WHERE trade_date = ? AND symbol IN ({placeholders})
                    ORDER BY symbol
                """
                params = [trade_date] + symbols
            else:
                query = """
                    SELECT * FROM futures_prices 
                    WHERE trade_date = ?
                    ORDER BY symbol
                """
                params = [trade_date]
                
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @monitor()
    def get_options_prices(self, trade_date: date, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Get options prices for a specific trade date.
        
        Args:
            trade_date: Trading date to query
            symbols: Optional list of symbols to filter
            
        Returns:
            List of price records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if symbols:
                placeholders = ','.join(['?' for _ in symbols])
                query = f"""
                    SELECT * FROM options_prices 
                    WHERE trade_date = ? AND symbol IN ({placeholders})
                    ORDER BY symbol
                """
                params = [trade_date] + symbols
            else:
                query = """
                    SELECT * FROM options_prices 
                    WHERE trade_date = ?
                    ORDER BY symbol
                """
                params = [trade_date]
                
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @monitor()
    def get_processing_summary(self) -> Dict:
        """Get summary of processed files."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count by file type and window
            cursor.execute("""
                SELECT 
                    file_type,
                    window_type,
                    COUNT(*) as file_count,
                    SUM(processed_rows) as total_rows,
                    MIN(file_timestamp) as earliest,
                    MAX(file_timestamp) as latest
                FROM price_file_tracker
                WHERE processing_completed_at IS NOT NULL
                GROUP BY file_type, window_type
            """)
            
            summary = {
                'by_type_and_window': [dict(row) for row in cursor.fetchall()]
            }
            
            # Get latest prices count
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM futures_prices WHERE Flash_Close IS NOT NULL")
            summary['futures_with_flash_close'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM options_prices WHERE Flash_Close IS NOT NULL")
            summary['options_with_flash_close'] = cursor.fetchone()[0]
            
            return summary
    
    @monitor()
    def update_current_prices_futures(self, updates: List[Dict]) -> bool:
        """
        Update Current_Price for futures.
        
        Args:
            updates: List of dicts with trade_date, symbol, Current_Price, last_updated
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for update in updates:
                    # Try to update existing row first
                    cursor.execute("""
                        UPDATE futures_prices
                        SET Current_Price = ?, last_updated = ?
                        WHERE trade_date = ? AND symbol = ?
                    """, (
                        update['Current_Price'],
                        update['last_updated'],
                        update['trade_date'],
                        update['symbol']
                    ))
                    
                    # If no row was updated, insert new row
                    if cursor.rowcount == 0:
                        cursor.execute("""
                            INSERT INTO futures_prices 
                            (trade_date, symbol, Current_Price, last_updated)
                            VALUES (?, ?, ?, ?)
                        """, (
                            update['trade_date'],
                            update['symbol'],
                            update['Current_Price'],
                            update['last_updated']
                        ))
                        
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating futures current prices: {e}")
            return False
            
    @monitor()
    def update_current_prices_options(self, updates: List[Dict]) -> bool:
        """
        Update Current_Price for options.
        
        Args:
            updates: List of dicts with trade_date, symbol, Current_Price, expire_dt, last_updated
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for update in updates:
                    # Try to update existing row first
                    cursor.execute("""
                        UPDATE options_prices
                        SET Current_Price = ?, last_updated = ?
                        WHERE trade_date = ? AND symbol = ?
                    """, (
                        update['Current_Price'],
                        update['last_updated'],
                        update['trade_date'],
                        update['symbol']
                    ))
                    
                    # If no row was updated, insert new row
                    if cursor.rowcount == 0:
                        cursor.execute("""
                            INSERT INTO options_prices 
                            (trade_date, symbol, Current_Price, expire_dt, last_updated)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            update['trade_date'],
                            update['symbol'],
                            update['Current_Price'],
                            update.get('expire_dt'),
                            update['last_updated']
                        ))
                        
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating options current prices: {e}")
            return False 