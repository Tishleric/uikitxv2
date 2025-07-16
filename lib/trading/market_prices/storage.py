"""
Storage layer for market price data.

Handles database operations for futures and options prices with row-level tracking.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Tuple
from contextlib import contextmanager

from lib.monitoring.decorators import monitor
from .constants import DB_FILE_NAME, CHICAGO_TZ

logger = logging.getLogger(__name__)


class MarketPriceStorage:
    """Handles database storage for market price data."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize storage with database path.
        
        Args:
            db_path: Path to database file (defaults to data/output/market_prices/market_prices.db)
        """
        if db_path is None:
            # Default to data/output/market_prices/
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / 'data' / 'output' / 'market_prices' / DB_FILE_NAME
            
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
            
            # Futures prices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS futures_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date DATE NOT NULL,
                    symbol TEXT NOT NULL,
                    current_price REAL,
                    prior_close REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trade_date, symbol)
                )
            """)
            
            # Options prices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS options_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date DATE NOT NULL,
                    symbol TEXT NOT NULL,
                    current_price REAL,
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
    def update_futures_current_price(self, trade_date: date, symbol: str, price: float):
        """
        Update current price for a futures contract.
        
        Args:
            trade_date: The trading date
            symbol: Bloomberg symbol (with U5 suffix)
            price: Current price from PX_LAST
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO futures_prices (trade_date, symbol, current_price)
                VALUES (?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    current_price = excluded.current_price,
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
    def update_options_current_price(self, trade_date: date, symbol: str, price: float,
                                   expire_dt: Optional[date] = None, 
                                   moneyness: Optional[float] = None):
        """
        Update current price for an option.
        
        Args:
            trade_date: The trading date
            symbol: Bloomberg symbol
            price: Current price from PX_LAST
            expire_dt: Expiration date
            moneyness: Moneyness value
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO options_prices 
                (trade_date, symbol, current_price, expire_dt, moneyness)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trade_date, symbol) 
                DO UPDATE SET 
                    current_price = excluded.current_price,
                    expire_dt = COALESCE(excluded.expire_dt, expire_dt),
                    moneyness = COALESCE(excluded.moneyness, moneyness),
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
                    expire_dt = COALESCE(excluded.expire_dt, expire_dt),
                    moneyness = COALESCE(excluded.moneyness, moneyness),
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
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM futures_prices WHERE current_price IS NOT NULL")
            summary['futures_with_current'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM options_prices WHERE current_price IS NOT NULL")
            summary['options_with_current'] = cursor.fetchone()[0]
            
            return summary 