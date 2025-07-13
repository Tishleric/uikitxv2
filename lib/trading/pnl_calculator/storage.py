"""Storage layer for P&L calculation data.

This module handles all database operations for the P&L tracking system,
including market prices, trades, and P&L snapshots.
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import pandas as pd

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor():
        def decorator(func):
            return func
        return decorator


class PnLStorage:
    """Handles all storage operations for P&L tracking system."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        """Initialize storage with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
        self._initialize_database()
        
    def _ensure_directory(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    @monitor()
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        schema = """
        -- Market prices table (required for P&L calculation)
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bloomberg TEXT NOT NULL,                -- Bloomberg asset identifier
            asset_type TEXT NOT NULL,               -- 'FUTURE' or 'OPTION'
            px_settle REAL NOT NULL,                -- Settlement price
            px_last REAL NOT NULL,                  -- Last traded price
            px_bid REAL,                            -- Bid price
            px_ask REAL,                            -- Ask price
            opt_expire_dt TEXT,                     -- Option expiry date (options only)
            moneyness TEXT,                         -- ITM/OTM (options only)
            upload_timestamp DATETIME NOT NULL,      -- When CSV was uploaded
            upload_date DATE NOT NULL,              -- Date of upload (for grouping)
            upload_hour INTEGER NOT NULL,           -- Hour of upload (15 or 17 for 3pm/5pm)
            source_file TEXT NOT NULL,              -- Source CSV filename
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bloomberg, upload_timestamp)
        );
        
        -- Index for efficient price lookups
        CREATE INDEX IF NOT EXISTS idx_market_prices_lookup 
        ON market_prices(bloomberg, upload_date, upload_hour);
        
        -- Processed trades tracking
        CREATE TABLE IF NOT EXISTS processed_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT NOT NULL,
            instrument_name TEXT NOT NULL,
            trade_date DATE NOT NULL,
            trade_timestamp DATETIME NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            side TEXT NOT NULL,                     -- 'B' or 'S'
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_file TEXT NOT NULL,
            UNIQUE(trade_id, trade_date)
        );
        
        -- Real-time P&L snapshots
        CREATE TABLE IF NOT EXISTS pnl_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            position INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            market_price REAL NOT NULL,
            price_source TEXT NOT NULL,             -- 'px_last' or 'px_settle'
            price_upload_time DATETIME NOT NULL,    -- When the price was uploaded
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            total_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- End of day P&L summary
        CREATE TABLE IF NOT EXISTS eod_pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            instrument_name TEXT NOT NULL,
            opening_position INTEGER NOT NULL,
            closing_position INTEGER NOT NULL,
            trades_count INTEGER NOT NULL,
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            total_pnl REAL NOT NULL,
            avg_buy_price REAL,
            avg_sell_price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trade_date, instrument_name)
        );
        
        -- File processing log
        CREATE TABLE IF NOT EXISTS file_processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,                -- 'trades' or 'market_prices'
            file_size INTEGER NOT NULL,
            file_modified DATETIME NOT NULL,
            processing_status TEXT NOT NULL,        -- 'pending', 'processing', 'completed', 'error'
            error_message TEXT,
            rows_processed INTEGER,
            processing_started DATETIME,
            processing_completed DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- P&L calculation audit log
        CREATE TABLE IF NOT EXISTS pnl_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            calculation_type TEXT NOT NULL,         -- 'live' or 'eod'
            trades_processed INTEGER NOT NULL,
            market_price_used REAL NOT NULL,
            price_source TEXT NOT NULL,
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with self._get_connection() as conn:
            conn.executescript(schema)
            conn.commit()
            
        logger.info(f"Database initialized at {self.db_path}")
        
    @monitor()
    def save_market_prices(self, prices_df: pd.DataFrame, upload_time: datetime, 
                          source_file: str) -> int:
        """Save market prices from DataFrame to database.
        
        Args:
            prices_df: DataFrame with market price data
            upload_time: When the file was uploaded
            source_file: Name of the source CSV file
            
        Returns:
            Number of rows inserted
        """
        upload_date = upload_time.date()
        upload_hour = upload_time.hour
        
        records = []
        for _, row in prices_df.iterrows():
            # Determine asset type based on presence of option-specific columns
            asset_type = 'OPTION' if pd.notna(row.get('OPT_EXPIRE_DT')) else 'FUTURE'
            
            record = {
                'bloomberg': row['bloomberg'],
                'asset_type': asset_type,
                'px_settle': row['PX_SETTLE'],
                'px_last': row['PX_LAST'],
                'px_bid': row.get('PX_BID', None),
                'px_ask': row.get('PX_ASK', None),
                'opt_expire_dt': row.get('OPT_EXPIRE_DT', None),
                'moneyness': row.get('MONEYNESS', None),
                'upload_timestamp': upload_time,
                'upload_date': upload_date,
                'upload_hour': upload_hour,
                'source_file': source_file
            }
            records.append(record)
            
        # Insert records
        query = """
        INSERT OR REPLACE INTO market_prices (
            bloomberg, asset_type, px_settle, px_last, px_bid, px_ask,
            opt_expire_dt, moneyness, upload_timestamp, upload_date, 
            upload_hour, source_file
        ) VALUES (
            :bloomberg, :asset_type, :px_settle, :px_last, :px_bid, :px_ask,
            :opt_expire_dt, :moneyness, :upload_timestamp, :upload_date,
            :upload_hour, :source_file
        )
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, records)
            conn.commit()
            rows_inserted = cursor.rowcount
            
        logger.info(f"Saved {rows_inserted} market prices from {source_file}")
        return rows_inserted
        
    @monitor()
    def get_market_price(self, instrument: str, as_of: datetime) -> Tuple[Optional[float], str]:
        """Get appropriate market price for an instrument at a specific time.
        
        Implements the pricing logic:
        - Before 3pm: Use previous day's 5pm px_settle
        - 3pm-5pm: Use today's 3pm px_last
        - After 5pm: Use today's 5pm px_settle
        
        Args:
            instrument: Bloomberg identifier
            as_of: Timestamp to get price for (in EST)
            
        Returns:
            Tuple of (price, source) where source is 'px_settle' or 'px_last'
        """
        as_of_date = as_of.date()
        as_of_hour = as_of.hour
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine which price to use based on time
            if as_of_hour < 15:  # Before 3pm
                # Use previous day's 5pm px_settle
                query = """
                SELECT px_settle, upload_timestamp
                FROM market_prices
                WHERE bloomberg = ? 
                  AND upload_date < ?
                  AND upload_hour = 17
                ORDER BY upload_timestamp DESC
                LIMIT 1
                """
                cursor.execute(query, (instrument, as_of_date))
                result = cursor.fetchone()
                if result:
                    return result['px_settle'], 'px_settle'
                    
            elif 15 <= as_of_hour < 17:  # 3pm-5pm
                # Use today's 3pm px_last
                query = """
                SELECT px_last, upload_timestamp
                FROM market_prices
                WHERE bloomberg = ?
                  AND upload_date = ?
                  AND upload_hour = 15
                ORDER BY upload_timestamp DESC
                LIMIT 1
                """
                cursor.execute(query, (instrument, as_of_date))
                result = cursor.fetchone()
                if result:
                    return result['px_last'], 'px_last'
                    
            else:  # After 5pm
                # Use today's 5pm px_settle
                query = """
                SELECT px_settle, upload_timestamp
                FROM market_prices
                WHERE bloomberg = ?
                  AND upload_date = ?
                  AND upload_hour = 17
                ORDER BY upload_timestamp DESC
                LIMIT 1
                """
                cursor.execute(query, (instrument, as_of_date))
                result = cursor.fetchone()
                if result:
                    return result['px_settle'], 'px_settle'
                    
        logger.warning(f"No market price found for {instrument} as of {as_of}")
        return None, 'none'
        
    @monitor()
    def save_processed_trades(self, trades_df: pd.DataFrame, source_file: str) -> int:
        """Save processed trades to database.
        
        Args:
            trades_df: DataFrame with trade data
            source_file: Name of the source CSV file
            
        Returns:
            Number of new trades inserted
        """
        records = []
        for _, row in trades_df.iterrows():
            record = {
                'trade_id': row['tradeId'],
                'instrument_name': row['instrumentName'],
                'trade_date': pd.to_datetime(row['marketTradeTime']).date(),
                'trade_timestamp': row['marketTradeTime'],
                'quantity': row['quantity'],
                'price': row['price'],
                'side': row['buySell'],
                'source_file': source_file
            }
            records.append(record)
            
        query = """
        INSERT OR IGNORE INTO processed_trades (
            trade_id, instrument_name, trade_date, trade_timestamp,
            quantity, price, side, source_file
        ) VALUES (
            :trade_id, :instrument_name, :trade_date, :trade_timestamp,
            :quantity, :price, :side, :source_file
        )
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, records)
            conn.commit()
            rows_inserted = cursor.rowcount
            
        logger.info(f"Saved {rows_inserted} new trades from {source_file}")
        return rows_inserted
        
    @monitor()
    def get_unprocessed_trades(self, trade_date: date) -> pd.DataFrame:
        """Get trades for a specific date that haven't been processed for P&L.
        
        Args:
            trade_date: Date to get trades for
            
        Returns:
            DataFrame with unprocessed trades
        """
        query = """
        SELECT * FROM processed_trades
        WHERE trade_date = ?
        ORDER BY trade_timestamp
        """
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(trade_date,))
            
        logger.info(f"Retrieved {len(df)} trades for {trade_date}")
        return df
        
    @monitor()
    def save_pnl_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
        """Save a P&L snapshot.
        
        Args:
            snapshot_data: Dictionary with P&L snapshot data
        """
        query = """
        INSERT INTO pnl_snapshots (
            snapshot_timestamp, instrument_name, position, avg_cost,
            market_price, price_source, price_upload_time,
            realized_pnl, unrealized_pnl, total_pnl
        ) VALUES (
            :snapshot_timestamp, :instrument_name, :position, :avg_cost,
            :market_price, :price_source, :price_upload_time,
            :realized_pnl, :unrealized_pnl, :total_pnl
        )
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, snapshot_data)
            conn.commit()
            
    @monitor()
    def save_eod_pnl(self, eod_data: List[Dict[str, Any]]) -> None:
        """Save end-of-day P&L summaries.
        
        Args:
            eod_data: List of dictionaries with EOD P&L data
        """
        query = """
        INSERT OR REPLACE INTO eod_pnl (
            trade_date, instrument_name, opening_position, closing_position,
            trades_count, realized_pnl, unrealized_pnl, total_pnl,
            avg_buy_price, avg_sell_price
        ) VALUES (
            :trade_date, :instrument_name, :opening_position, :closing_position,
            :trades_count, :realized_pnl, :unrealized_pnl, :total_pnl,
            :avg_buy_price, :avg_sell_price
        )
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, eod_data)
            conn.commit()
            
        logger.info(f"Saved EOD P&L for {len(eod_data)} instruments")
        
    @monitor()
    def log_file_processing(self, file_path: str, file_type: str, status: str,
                           error_message: Optional[str] = None,
                           rows_processed: Optional[int] = None) -> None:
        """Log file processing status.
        
        Args:
            file_path: Path to the processed file
            file_type: Type of file ('trades' or 'market_prices')
            status: Processing status
            error_message: Error message if failed
            rows_processed: Number of rows processed
        """
        file_path = Path(file_path)
        
        query = """
        INSERT INTO file_processing_log (
            file_path, file_type, file_size, file_modified,
            processing_status, error_message, rows_processed,
            processing_started, processing_completed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                str(file_path),
                file_type,
                file_path.stat().st_size if file_path.exists() else 0,
                datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else None,
                status,
                error_message,
                rows_processed,
                datetime.now() if status == 'processing' else None,
                datetime.now() if status in ['completed', 'error'] else None
            ))
            conn.commit() 