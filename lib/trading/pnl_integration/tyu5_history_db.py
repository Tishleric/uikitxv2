"""TYU5 History Database - Persistent storage for positions and trades"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TYU5HistoryDB:
    """Database interface for storing TYU5 calculation results"""
    
    def __init__(self, db_path: str = "data/output/pnl/tyu5_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self.connect() as conn:
            # Positions table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS tyu5_positions (
                run_timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                type TEXT,
                net_quantity REAL,
                avg_entry_price REAL,
                avg_entry_price_32nds TEXT,
                prior_close REAL,
                current_price REAL,
                prior_present_value REAL,
                current_present_value REAL,
                unrealized_pnl REAL,
                unrealized_pnl_current REAL,
                unrealized_pnl_flash REAL,
                unrealized_pnl_close REAL,
                realized_pnl REAL,
                daily_pnl REAL,
                total_pnl REAL,
                attribution_error TEXT,
                PRIMARY KEY (run_timestamp, symbol)
            )''')
            
            # Trades table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS tyu5_trades (
                run_timestamp DATETIME NOT NULL,
                trade_id TEXT NOT NULL,
                datetime TEXT,
                symbol TEXT,
                action TEXT,
                quantity REAL,
                price_decimal REAL,
                price_32nds TEXT,
                fees REAL,
                type TEXT,
                realized_pnl REAL,
                counterparty TEXT,
                PRIMARY KEY (run_timestamp, trade_id)
            )''')
            
            # Runs metadata
            conn.execute('''
            CREATE TABLE IF NOT EXISTS tyu5_runs (
                run_timestamp DATETIME PRIMARY KEY,
                trade_ledger_file TEXT,
                total_trades INTEGER,
                total_positions INTEGER,
                total_pnl REAL,
                daily_pnl REAL,
                realized_pnl REAL,
                unrealized_pnl REAL,
                status TEXT,
                error_message TEXT,
                excel_file TEXT
            )''')
            
            conn.commit()
    
    def connect(self):
        """Get database connection"""
        return sqlite3.connect(str(self.db_path))
    
    def save_run(self, run_timestamp: datetime, trades_df: pd.DataFrame, 
                 positions_df: pd.DataFrame, trade_ledger_file: str,
                 excel_file: str = None, status: str = "SUCCESS", 
                 error: str = None) -> bool:
        """Save complete TYU5 run to database"""
        
        with self.connect() as conn:
            try:
                # Calculate summary metrics
                total_trades = len(trades_df)
                total_positions = len(positions_df)
                total_pnl = positions_df['Total_PNL'].sum() if not positions_df.empty else 0
                daily_pnl = positions_df['Daily_PNL'].sum() if not positions_df.empty else 0
                realized_pnl = trades_df['Realized_PNL'].sum() if not trades_df.empty else 0
                unrealized_pnl = positions_df['Unrealized_PNL'].sum() if not positions_df.empty else 0
                
                # Insert run metadata
                conn.execute('''
                INSERT INTO tyu5_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (run_timestamp, trade_ledger_file, total_trades, total_positions,
                      total_pnl, daily_pnl, realized_pnl, unrealized_pnl, 
                      status, error, excel_file))
                
                # Prepare DataFrames
                trades_copy = trades_df.copy()
                positions_copy = positions_df.copy()
                
                # Add run timestamp
                trades_copy['run_timestamp'] = run_timestamp
                positions_copy['run_timestamp'] = run_timestamp
                
                # Normalize column names to lowercase for database
                trades_copy.columns = [col.lower() for col in trades_copy.columns]
                positions_copy.columns = [col.lower() for col in positions_copy.columns]
                
                # Insert data
                trades_copy.to_sql('tyu5_trades', conn, if_exists='append', index=False)
                positions_copy.to_sql('tyu5_positions', conn, if_exists='append', index=False)
                
                conn.commit()
                logger.info(f"Saved TYU5 run: {total_positions} positions, {total_trades} trades")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to save TYU5 run: {e}")
                raise
    
    def get_latest_positions(self) -> pd.DataFrame:
        """Get most recent positions snapshot"""
        query = '''
        SELECT * FROM tyu5_positions 
        WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM tyu5_positions)
        '''
        with self.connect() as conn:
            return pd.read_sql_query(query, conn)
    
    def get_position_history(self, symbol: str) -> pd.DataFrame:
        """Get historical positions for a specific symbol"""
        query = '''
        SELECT * FROM tyu5_positions 
        WHERE symbol = ? 
        ORDER BY run_timestamp DESC
        '''
        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=[symbol])
    
    def get_run_summary(self) -> pd.DataFrame:
        """Get summary of all runs"""
        query = '''
        SELECT * FROM tyu5_runs 
        ORDER BY run_timestamp DESC
        '''
        with self.connect() as conn:
            return pd.read_sql_query(query, conn) 