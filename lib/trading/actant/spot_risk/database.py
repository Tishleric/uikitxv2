"""Database service for Spot Risk data storage.

This module provides SQLite storage functionality for spot risk data,
including session management, raw data storage, and calculated Greeks.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
import pandas as pd
from lib.trading.market_prices.rosetta_stone import RosettaStone

logger = logging.getLogger(__name__)


class SpotRiskDatabaseService:
    """Service for managing spot risk data in SQLite database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database service.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path("data/output/spot_risk/spot_risk.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize symbol translator
        self.symbol_translator = RosettaStone()
        
        # Initialize database schema
        self._initialize_database()
        logger.info(f"Initialized SpotRiskDatabaseService with database at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with WAL mode."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL for concurrent access
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """Initialize database schema from schema.sql file."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
        
        logger.info("Database schema initialized")
    
    def create_session(self, source_file: str, data_timestamp: Optional[str] = None) -> int:
        """
        Create a new processing session.
        
        Args:
            source_file: Path to the source CSV file
            data_timestamp: Timestamp from the data itself (from filename)
            
        Returns:
            session_id: ID of the created session
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO spot_risk_sessions (source_file, data_timestamp, status)
                VALUES (?, ?, 'active')
                """,
                (source_file, data_timestamp)
            )
            session_id = cursor.lastrowid
            logger.info(f"Created session {session_id} for file {source_file}")
            return session_id
    
    def update_session(self, session_id: int, status: str, 
                      row_count: Optional[int] = None,
                      error_count: Optional[int] = None,
                      notes: Optional[str] = None):
        """Update session status and metadata."""
        updates = ["status = ?", "last_refresh = CURRENT_TIMESTAMP"]
        params = [status]
        
        if row_count is not None:
            updates.append("row_count = ?")
            params.append(row_count)
        
        if error_count is not None:
            updates.append("error_count = ?")
            params.append(error_count)
        
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        
        params.append(session_id)
        
        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE spot_risk_sessions SET {', '.join(updates)} WHERE session_id = ?",
                params
            )
        
        logger.info(f"Updated session {session_id}: status={status}")
    
    def insert_raw_data(self, df: pd.DataFrame, session_id: int) -> int:
        """
        Insert raw data from DataFrame into database.
        
        Args:
            df: DataFrame with spot risk data
            session_id: Session ID for this processing run
            
        Returns:
            Number of rows inserted
        """
        rows_inserted = 0
        
        with self._get_connection() as conn:
            for idx, row in df.iterrows():
                # Extract key fields
                instrument_key = row.get('key', row.get('instrument_key', row.get('Product', '')))
                
                # Determine instrument type
                if 'Instrument Type' in row:
                    instrument_type = str(row['Instrument Type']).upper()
                elif 'instrument type' in row:
                    instrument_type = str(row['instrument type']).upper()
                elif 'itype' in row:
                    itype = str(row['itype']).upper()
                    if itype == 'F':
                        instrument_type = 'FUTURE'
                    elif itype == 'C':
                        instrument_type = 'CALL'
                    elif itype == 'P':
                        instrument_type = 'PUT'
                    else:
                        instrument_type = itype
                else:
                    instrument_type = 'UNKNOWN'
                
                expiry_date = row.get('expiry_date', '')
                strike = row.get('strike', row.get('Strike'))
                midpoint_price = row.get('midpoint_price', row.get('Price', row.get('price')))
                vtexp = row.get('vtexp')  # Get vtexp from dataframe
                
                # Convert row to JSON for raw_data column
                raw_data = json.dumps(row.to_dict(), default=str)
                
                # Translate to Bloomberg symbol
                bloomberg_symbol = None
                if instrument_key:
                    try:
                        bloomberg_symbol = self.symbol_translator.translate(instrument_key, 'actantrisk', 'bloomberg')
                        if bloomberg_symbol:
                            logger.debug(f"Translated {instrument_key} → {bloomberg_symbol}")
                    except Exception as e:
                        logger.warning(f"Failed to translate symbol {instrument_key}: {e}")
                
                conn.execute(
                    """
                    INSERT INTO spot_risk_raw 
                    (session_id, instrument_key, bloomberg_symbol, instrument_type, expiry_date, strike, midpoint_price, vtexp, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (session_id, instrument_key, bloomberg_symbol, instrument_type, expiry_date, strike, midpoint_price, vtexp, raw_data)
                )
                rows_inserted += 1
        
        logger.info(f"Inserted {rows_inserted} raw data rows for session {session_id}")
        return rows_inserted
    
    def insert_calculated_greeks(self, df: pd.DataFrame, results: List[Any], 
                                session_id: int) -> Tuple[int, int]:
        """
        Insert calculated Greeks into database.
        
        Args:
            df: DataFrame with calculated Greeks
            results: List of GreekResult objects from calculator
            session_id: Session ID for this processing run
            
        Returns:
            Tuple of (successful_inserts, failed_inserts)
        """
        successful_inserts = 0
        failed_inserts = 0
        
        with self._get_connection() as conn:
            # First, get raw_id mapping for this session
            raw_id_map = {}
            cursor = conn.execute(
                """
                SELECT id, instrument_key 
                FROM spot_risk_raw 
                WHERE session_id = ?
                """,
                (session_id,)
            )
            for row in cursor:
                raw_id_map[row['instrument_key']] = row['id']
            
            # Process each row in the DataFrame
            for idx, row in df.iterrows():
                instrument_key = row.get('key', row.get('instrument_key', row.get('Product', '')))
                raw_id = raw_id_map.get(instrument_key)
                
                if not raw_id:
                    # This might be an aggregate row (NET_FUTURES, NET_OPTIONS_F, etc.)
                    logger.debug(f"No raw_id found for {instrument_key}, skipping")
                    continue
                
                # Get calculation status
                calc_success = row.get('greek_calc_success', False)
                calc_error = row.get('greek_calc_error', '')
                model_version = row.get('model_version', 'unknown')
                
                # Determine status
                if calc_success:
                    calc_status = 'success'
                else:
                    calc_status = 'failed'
                
                # Extract Greek values
                greek_values = {
                    'implied_vol': row.get('implied_vol'),
                    'delta_F': row.get('delta_F'),
                    'delta_y': row.get('delta_y'),
                    'gamma_F': row.get('gamma_F'),
                    'gamma_y': row.get('gamma_y'),
                    'vega_price': row.get('vega_price'),
                    'vega_y': row.get('vega_y'),
                    'theta_F': row.get('theta_F'),
                    'rho_y': row.get('rho_y'),  # Not currently calculated
                    'vanna_F_price': row.get('vanna_F_price'),
                    'vanna_F_y': row.get('vanna_F_y'),  # Map if available
                    'charm_F': row.get('charm_F'),
                    'volga_price': row.get('volga_price'),
                    'volga_y': row.get('volga_y'),  # Map if available
                    'veta_y': row.get('veta_y'),  # Not currently calculated
                    'speed_F': row.get('speed_F'),
                    'color_F': row.get('color_F'),
                    'ultima': row.get('ultima'),
                    'zomma': row.get('zomma')
                }
                
                # Build INSERT statement dynamically based on available columns
                columns = ['raw_id', 'session_id', 'model_version', 'calculation_status']
                values = [raw_id, session_id, model_version, calc_status]
                
                if calc_error:
                    columns.append('error_message')
                    values.append(calc_error)
                
                # Add Greek values
                for greek_name, greek_value in greek_values.items():
                    if greek_value is not None and not pd.isna(greek_value):
                        columns.append(greek_name)
                        values.append(float(greek_value))
                
                # Insert calculated data
                placeholders = ', '.join(['?' for _ in values])
                column_list = ', '.join(columns)
                
                try:
                    conn.execute(
                        f"""
                        INSERT INTO spot_risk_calculated ({column_list})
                        VALUES ({placeholders})
                        """,
                        values
                    )
                    successful_inserts += 1
                except Exception as e:
                    logger.error(f"Failed to insert calculated data for {instrument_key}: {e}")
                    failed_inserts += 1
        
        logger.info(f"Inserted calculated Greeks: {successful_inserts} successful, {failed_inserts} failed")
        return successful_inserts, failed_inserts 