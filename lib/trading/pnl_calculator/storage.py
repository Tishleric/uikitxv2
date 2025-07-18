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
            source_file TEXT NOT NULL
            -- Removed UNIQUE constraint to allow duplicate trade IDs from different days
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
        
        -- CTO_INTEGRATION: Trade processing tracker for row-level deduplication
        CREATE TABLE IF NOT EXISTS trade_processing_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,              -- Original CSV filename
            source_row_number INTEGER NOT NULL,     -- Row number in CSV (1-based)
            trade_id TEXT NOT NULL,                 -- tradeId from CSV
            trade_timestamp DATETIME NOT NULL,      -- marketTradeTime from CSV
            instrument_name TEXT NOT NULL,          -- instrumentName from CSV
            quantity REAL NOT NULL,                 -- quantity from CSV
            price REAL NOT NULL,                    -- price from CSV
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            -- Removed UNIQUE constraint to allow duplicate trade IDs from different days
        );
        
        -- Index for efficient lookups
        CREATE INDEX IF NOT EXISTS idx_trade_tracker_file 
        ON trade_processing_tracker(source_file);
        
        CREATE INDEX IF NOT EXISTS idx_trade_tracker_timestamp
        ON trade_processing_tracker(trade_timestamp);
        
        -- CTO_INTEGRATION: New trades table with CTO's exact schema
        CREATE TABLE IF NOT EXISTS cto_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date DATE NOT NULL,              -- Trade date
            Time TIME NOT NULL,              -- Trade time  
            Symbol TEXT NOT NULL,            -- Bloomberg symbol
            Action TEXT NOT NULL,            -- 'BUY' or 'SELL'
            Quantity INTEGER NOT NULL,       -- Negative for sells
            Price REAL NOT NULL,             -- Decimal price
            Fees REAL DEFAULT 0.0,           -- Trading fees
            Counterparty TEXT NOT NULL,      -- Always 'FRGM' for now
            tradeID TEXT NOT NULL,           -- Original trade ID (removed UNIQUE constraint)
            Type TEXT NOT NULL,              -- 'FUT' or 'OPT'
            
            -- Metadata
            source_file TEXT NOT NULL,       -- Source CSV filename
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Flags for edge cases
            is_sod BOOLEAN DEFAULT 0,        -- Start of day flag (midnight timestamp)
            is_exercise BOOLEAN DEFAULT 0    -- Exercise flag (price = 0)
        );
        
        -- Indexes for CTO trades table
        CREATE INDEX IF NOT EXISTS idx_cto_trades_date 
        ON cto_trades(Date);
        
        CREATE INDEX IF NOT EXISTS idx_cto_trades_symbol
        ON cto_trades(Symbol);
        
        -- Removed UNIQUE index on tradeID to allow duplicate trade IDs from different days
        
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
        
        -- Current positions (only non-zero)
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_name TEXT NOT NULL UNIQUE,
            position_quantity REAL NOT NULL,        -- Current net position
            avg_cost REAL NOT NULL,                 -- FIFO average cost
            total_realized_pnl REAL NOT NULL DEFAULT 0,  -- Cumulative realized P&L
            unrealized_pnl REAL NOT NULL DEFAULT 0,      -- Current unrealized P&L
            closed_quantity REAL NOT NULL DEFAULT 0,     -- Quantity closed today
            last_market_price REAL,                 -- Last price used for unrealized calc
            last_trade_id TEXT,                     -- For tracking
            last_updated DATETIME NOT NULL,
            is_option BOOLEAN NOT NULL DEFAULT 0,
            option_strike REAL,                     -- For options
            option_expiry DATE,                     -- For options
            has_exercised_trades BOOLEAN DEFAULT 0, -- Flag for exercised options
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Position snapshots for SOD/EOD
        CREATE TABLE IF NOT EXISTS position_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_type TEXT NOT NULL,            -- 'SOD' or 'EOD'
            snapshot_timestamp DATETIME NOT NULL,
            instrument_name TEXT NOT NULL,
            position_quantity REAL NOT NULL,
            avg_cost REAL NOT NULL,
            total_realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            market_price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(snapshot_type, snapshot_timestamp, instrument_name)
        );
        
        -- Index for position snapshots
        CREATE INDEX IF NOT EXISTS idx_position_snapshots 
        ON position_snapshots(snapshot_type, snapshot_timestamp);
        
        -- =====================================================
        -- TYU5 P&L System Enhancements
        -- =====================================================
        
        -- Enable WAL mode for better concurrency
        PRAGMA journal_mode=WAL;
        
        -- Lot positions for individual lot tracking
        CREATE TABLE IF NOT EXISTS lot_positions (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            trade_id TEXT NOT NULL,
            remaining_quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            entry_date DATETIME NOT NULL,
            position_id INTEGER REFERENCES positions(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_lot_positions_symbol 
        ON lot_positions(symbol);
        
        CREATE INDEX IF NOT EXISTS idx_lot_positions_trade 
        ON lot_positions(trade_id, entry_date);
        
        -- Position Greeks table
        CREATE TABLE IF NOT EXISTS position_greeks (
            id INTEGER PRIMARY KEY,
            position_id INTEGER REFERENCES positions(id),
            calc_timestamp DATETIME NOT NULL,
            underlying_price REAL NOT NULL,
            implied_vol REAL,
            delta REAL,
            gamma REAL,
            vega REAL,
            theta REAL,
            speed REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_position_greeks_latest 
        ON position_greeks(position_id, calc_timestamp DESC);
        
        -- Risk scenarios table
        CREATE TABLE IF NOT EXISTS risk_scenarios (
            id INTEGER PRIMARY KEY,
            calc_timestamp DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            scenario_price REAL NOT NULL,
            scenario_pnl REAL NOT NULL,
            scenario_delta REAL,
            scenario_gamma REAL,
            position_quantity REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Partial index for latest scenarios (7 days rolling window)
        CREATE INDEX IF NOT EXISTS idx_risk_scenarios_latest 
        ON risk_scenarios(symbol, calc_timestamp DESC)
        WHERE calc_timestamp > datetime('now', '-7 days');
        
        -- Match history for detailed FIFO tracking
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            match_date DATETIME NOT NULL,
            buy_trade_id TEXT NOT NULL,
            sell_trade_id TEXT NOT NULL,
            matched_quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            realized_pnl REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_match_history_symbol 
        ON match_history(symbol, match_date DESC);
        
        -- P&L attribution table
        CREATE TABLE IF NOT EXISTS pnl_attribution (
            id INTEGER PRIMARY KEY,
            position_id INTEGER REFERENCES positions(id),
            calc_timestamp DATETIME NOT NULL,
            total_pnl REAL NOT NULL,
            delta_pnl REAL,
            gamma_pnl REAL,
            vega_pnl REAL,
            theta_pnl REAL,
            speed_pnl REAL,
            residual_pnl REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_pnl_attribution_latest 
        ON pnl_attribution(position_id, calc_timestamp DESC);
        
        -- Schema migrations tracking
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with self._get_connection() as conn:
            conn.executescript(schema)
            
            # Add columns to positions table if they don't exist
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(positions)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'short_quantity' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE positions 
                    ADD COLUMN short_quantity REAL NOT NULL DEFAULT 0;
                """)
                
            if 'match_history' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE positions 
                    ADD COLUMN match_history TEXT;  -- JSON column
                """)
            
            conn.commit()
            
        logger.info(f"Database initialized at {self.db_path}")
        
    @monitor()
    def drop_and_recreate_tables(self):
        """Drop all tables and recreate them. USE WITH CAUTION - This will delete all data!"""
        logger.warning("Dropping all P&L tracking tables...")
        
        drop_sql = """
        DROP TABLE IF EXISTS market_prices;
        DROP TABLE IF EXISTS processed_trades;
        DROP TABLE IF EXISTS pnl_snapshots;
        DROP TABLE IF EXISTS eod_pnl;
        DROP TABLE IF EXISTS file_processing_log;
        DROP TABLE IF EXISTS trade_processing_tracker;
        DROP TABLE IF EXISTS cto_trades;
        DROP TABLE IF EXISTS pnl_audit_log;
        DROP TABLE IF EXISTS positions;
        DROP TABLE IF EXISTS position_snapshots;
        """
        
        with self._get_connection() as conn:
            conn.executescript(drop_sql)
            conn.commit()
            
        logger.info("All tables dropped. Recreating...")
        self._initialize_database()
        logger.info("Tables recreated successfully")
        
    @monitor()
    def save_market_prices(self, prices_df: pd.DataFrame, upload_time: datetime, 
                          source_file: str) -> int:
        """Save market prices from DataFrame to database.
        
        Args:
            prices_df: DataFrame with market price data
            upload_time: Timestamp when prices were uploaded
            source_file: Path to source file
            
        Returns:
            Number of records saved
        """
        if prices_df.empty:
            logger.warning("Empty prices DataFrame provided")
            return 0
            
        records_saved = 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Extract date and hour from upload_time for partitioning
            upload_date = upload_time.date()
            upload_hour = upload_time.hour
            
            for _, row in prices_df.iterrows():
                try:
                    # Get bloomberg symbol - handle both column names
                    bloomberg = row.get('bloomberg') or row.get('SYMBOL')
                    if not bloomberg:
                        continue
                        
                    # Validate and clean price data
                    px_settle = row.get('PX_SETTLE') or row.get('px_settle')
                    px_last = row.get('PX_LAST') or row.get('px_last')
                    
                    # Skip if both prices are invalid
                    if pd.isna(px_settle) and pd.isna(px_last):
                        continue
                        
                    # Clean price values - convert to float or None
                    def clean_price(value):
                        if pd.isna(value):
                            return None
                        if isinstance(value, str):
                            # Skip invalid string values
                            if '#N/A' in value or 'Requesting' in value:
                                return None
                            try:
                                return float(value)
                            except ValueError:
                                return None
                        try:
                            return float(value)
                        except:
                            return None
                    
                    px_settle_clean = clean_price(px_settle)
                    px_last_clean = clean_price(px_last)
                    
                    # Skip if both cleaned prices are None
                    if px_settle_clean is None and px_last_clean is None:
                        logger.debug(f"Skipping {bloomberg} - no valid prices")
                        continue
                    
                    # Determine asset type based on source file path
                    if 'futures' in source_file.lower():
                        asset_type = 'FUTURE'
                    elif 'options' in source_file.lower():
                        asset_type = 'OPTION'
                    else:
                        # Fallback to symbol check
                        asset_type = 'OPTION' if any(x in str(bloomberg) for x in ['C ', 'P ']) else 'FUTURE'
                    
                    # Extract other fields
                    px_bid = clean_price(row.get('PX_BID'))
                    px_ask = clean_price(row.get('PX_ASK'))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO market_prices 
                        (bloomberg, asset_type, px_settle, px_last, px_bid, px_ask,
                         opt_expire_dt, moneyness, upload_timestamp, upload_date, upload_hour,
                         source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        bloomberg,
                        asset_type,
                        px_settle_clean,
                        px_last_clean,
                        px_bid,
                        px_ask,
                        row.get('EXPIRE_DT'),
                        row.get('MONEYNESS'),
                        upload_time,
                        upload_date,
                        upload_hour,
                        source_file
                    ))
                    
                    records_saved += 1
                    
                except Exception as e:
                    logger.error(f"Error saving price for {row.get('bloomberg', 'unknown')}: {e}")
                    continue
                    
            conn.commit()
            
        logger.info(f"Saved {records_saved} market prices from {source_file}")
        return records_saved
        
    @monitor()
    def get_market_price(self, instrument: str, as_of: datetime) -> Tuple[Optional[float], str]:
        """Get appropriate market price for an instrument at a specific time.
        
        Finds the most recent price available before or at the as_of time.
        Prefers px_settle but falls back to px_last if settle not available.
        
        Args:
            instrument: Bloomberg identifier or internal instrument name
            as_of: Timestamp to get price for
            
        Returns:
            Tuple of (price, source) where source is 'px_settle', 'px_last', or 'none'
        """
        # Try to map internal instrument name to Bloomberg symbol
        bloomberg_symbol = self._map_to_bloomberg(instrument)
        if not bloomberg_symbol:
            bloomberg_symbol = instrument  # Fallback to original
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Look for the most recent price up to the as_of time
            # Prefer px_settle over px_last when both are available
            query = """
            SELECT 
                bloomberg,
                px_settle,
                px_last,
                upload_timestamp,
                CASE 
                    WHEN px_settle IS NOT NULL THEN px_settle
                    WHEN px_last IS NOT NULL THEN px_last
                    ELSE NULL
                END as price,
                CASE 
                    WHEN px_settle IS NOT NULL THEN 'px_settle'
                    WHEN px_last IS NOT NULL THEN 'px_last'
                    ELSE 'none'
                END as price_source
            FROM market_prices
            WHERE bloomberg = ? 
              AND upload_timestamp <= ?
              AND (px_settle IS NOT NULL OR px_last IS NOT NULL)
            ORDER BY upload_timestamp DESC
            LIMIT 1
            """
            
            cursor.execute(query, (bloomberg_symbol, as_of))
            result = cursor.fetchone()
            
            if result and result['price'] is not None:
                return float(result['price']), result['price_source']
            
            # If no price found, log and return None
            logger.debug(f"No market price found for {instrument} as of {as_of}")
            return None, 'none'
        
    def _map_to_bloomberg(self, instrument: str) -> Optional[str]:
        """Map internal instrument name to Bloomberg symbol.
        
        Args:
            instrument: Internal instrument name
            
        Returns:
            Bloomberg symbol or None if no mapping found
        """
        # Use the existing SymbolTranslator
        from lib.trading.symbol_translator import SymbolTranslator
        
        translator = SymbolTranslator()
        bloomberg_symbol = translator.translate(instrument)
        
        if bloomberg_symbol:
            # Return the full Bloomberg symbol as stored in market_prices table
            # e.g., "VBYN25C2 110.750 Comdty" or "TYU5 Comdty"
            return bloomberg_symbol
                
        return None
        
    @monitor()
    def save_processed_trades(self, trades_df: pd.DataFrame, source_file: str, trade_date: date) -> int:
        """Save processed trades to database.
        
        Args:
            trades_df: DataFrame with trade data
            source_file: Name of the source CSV file
            trade_date: Trading day date (from filename)
            
        Returns:
            Number of new trades inserted
        """
        records = []
        for _, row in trades_df.iterrows():
            record = {
                'trade_id': row['tradeId'],
                'instrument_name': row['instrumentName'],
                'trade_date': trade_date.isoformat(),  # Use the trading day date
                'trade_timestamp': row['marketTradeTime'],
                'quantity': row['quantity'],
                'price': row['price'],
                'side': row['buySell'],
                'source_file': source_file
            }
            records.append(record)
            
        query = """
        INSERT INTO processed_trades (
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
    def get_last_trade_price(self, instrument: str, trade_date: date) -> Optional[float]:
        """Get the last trade price for an instrument on a specific date.
        
        Args:
            instrument: Instrument name
            trade_date: Trading date
            
        Returns:
            Last trade price or None if no trades found
        """
        query = """
        SELECT price 
        FROM processed_trades
        WHERE instrument_name = ? AND trade_date = ?
        ORDER BY trade_timestamp DESC
        LIMIT 1
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (instrument, trade_date))
            result = cursor.fetchone()
            
        if result:
            return result['price']
        return None
            
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
            try:
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
            except Exception as e:
                logger.error(f"Error logging file processing: {e}")
    
    # CTO_INTEGRATION: Add methods for row-level trade tracking
    @monitor()
    def get_processed_trades_for_file(self, source_file: str) -> set:
        """Get set of trade IDs that have already been processed from a file.
        
        Args:
            source_file: Name of the source CSV file
            
        Returns:
            Set of trade IDs that have been processed
        """
        query = """
        SELECT trade_id
        FROM trade_processing_tracker
        WHERE source_file = ?
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (source_file,))
            results = cursor.fetchall()
            
        return {row['trade_id'] for row in results}
    
    @monitor()
    def record_processed_trade(self, source_file: str, row_number: int, trade_data: dict) -> bool:
        """Record that a trade has been processed.
        
        Args:
            source_file: Name of the source CSV file
            row_number: Row number in the CSV (1-based)
            trade_data: Dictionary with trade information
            
        Returns:
            True if successfully recorded, False on error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trade_processing_tracker 
                    (source_file, source_row_number, trade_id, trade_timestamp, 
                     instrument_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    source_file,
                    row_number,
                    trade_data['tradeId'],
                    trade_data['marketTradeTime'],
                    trade_data['instrumentName'],
                    trade_data['quantity'],
                    trade_data['price']
                ))
                conn.commit()
                logger.debug(f"Recorded trade {trade_data['tradeId']} from {source_file} row {row_number}")
                return True
                
        except Exception as e:
            logger.error(f"Error recording processed trade: {e}")
            raise
    
    @monitor()
    def get_last_processed_row_for_file(self, source_file: str) -> int:
        """Get the last processed row number for a file.
        
        Args:
            source_file: Name of the source CSV file
            
        Returns:
            Last processed row number (0 if no rows processed)
        """
        query = """
        SELECT MAX(source_row_number) as last_row
        FROM trade_processing_tracker
        WHERE source_file = ?
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (source_file,))
            result = cursor.fetchone()
            
        return result['last_row'] if result and result['last_row'] else 0
    
    @monitor()
    def get_processing_stats_for_file(self, source_file: str) -> dict:
        """Get processing statistics for a file.
        
        Args:
            source_file: Name of the source CSV file
            
        Returns:
            Dictionary with processing stats
        """
        query = """
        SELECT 
            COUNT(*) as total_processed,
            MIN(trade_timestamp) as first_trade_time,
            MAX(trade_timestamp) as last_trade_time,
            MIN(processed_at) as first_processed_at,
            MAX(processed_at) as last_processed_at
        FROM trade_processing_tracker
        WHERE source_file = ?
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (source_file,))
            result = cursor.fetchone()
            
        return dict(result) if result else {
            'total_processed': 0,
            'first_trade_time': None,
            'last_trade_time': None,
            'first_processed_at': None,
            'last_processed_at': None
        } 
    
    # CTO_INTEGRATION: Methods for CTO trades table
    @monitor()
    def insert_cto_trade(self, trade_data: dict) -> bool:
        """Insert a trade into the CTO trades table.
        
        Args:
            trade_data: Dictionary with all required CTO fields
            
        Returns:
            True if successfully inserted, False on error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cto_trades 
                    (Date, Time, Symbol, Action, Quantity, Price, Fees, 
                     Counterparty, tradeID, Type, source_file, is_sod, is_exercise)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data['Date'],
                    trade_data['Time'],
                    trade_data['Symbol'],
                    trade_data['Action'],
                    trade_data['Quantity'],
                    trade_data['Price'],
                    trade_data.get('Fees', 0.0),
                    trade_data['Counterparty'],
                    trade_data['tradeID'],
                    trade_data['Type'],
                    trade_data['source_file'],
                    trade_data.get('is_sod', False),
                    trade_data.get('is_exercise', False)
                ))
                conn.commit()
                logger.debug(f"Inserted CTO trade {trade_data['tradeID']} from {trade_data['source_file']}")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting CTO trade: {e}")
            raise
    
    @monitor()
    def get_cto_trades_by_date(self, trade_date: date) -> pd.DataFrame:
        """Get all CTO trades for a specific date.
        
        Args:
            trade_date: Date to query trades for
            
        Returns:
            DataFrame with CTO trades
        """
        query = """
        SELECT * FROM cto_trades
        WHERE Date = ?
        ORDER BY Time, id
        """
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[trade_date.isoformat()])
            
        return df
    
    @monitor()
    def get_cto_trades_summary(self) -> dict:
        """Get summary statistics for CTO trades table.
        
        Returns:
            Dictionary with summary stats
        """
        query = """
        SELECT 
            COUNT(*) as total_trades,
            COUNT(DISTINCT Date) as trading_days,
            COUNT(DISTINCT Symbol) as unique_symbols,
            SUM(CASE WHEN is_sod = 1 THEN 1 ELSE 0 END) as sod_trades,
            SUM(CASE WHEN is_exercise = 1 THEN 1 ELSE 0 END) as exercise_trades,
            MIN(Date) as first_trade_date,
            MAX(Date) as last_trade_date
        FROM cto_trades
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            
        return dict(result) if result else {
            'total_trades': 0,
            'trading_days': 0,
            'unique_symbols': 0,
            'sod_trades': 0,
            'exercise_trades': 0,
            'first_trade_date': None,
            'last_trade_date': None
        } 