#!/usr/bin/env python3
"""
Direct writer for TYU5 DataFrames to database.

This writer takes the DataFrame dictionary directly from TYU5's run_pnl_analysis()
and writes each DataFrame to its corresponding table with no transformations.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import uuid
import time


class TYU5DirectWriter:
    """Write TYU5 output DataFrames directly to database tables."""
    
    # Mapping of DataFrame keys to table names
    TABLE_MAPPING = {
        'processed_trades_df': 'tyu5_trades',
        'positions_df': 'tyu5_positions',
        'summary_df': 'tyu5_summary',
        'risk_df': 'tyu5_risk_matrix',
        'breakdown_df': 'tyu5_position_breakdown',
        'pnl_components_df': 'tyu5_pnl_components'
    }
    
    def __init__(self, db_path: str = 'data/output/pnl/pnl_tracker.db'):
        """
        Initialize the writer.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        
    def _clean_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Clean DataFrame for database storage.
        
        - Replace "awaiting data" with None/NaN
        - Ensure numeric columns are numeric dtype
        - Preserve all column names
        
        Args:
            df: Original DataFrame
            table_name: Target table name (for specific handling)
            
        Returns:
            Cleaned DataFrame copy
        """
        # Create a copy to avoid modifying original
        clean_df = df.copy()
        
        # Replace "awaiting data" strings with NaN
        clean_df = clean_df.replace("awaiting data", np.nan)
        
        # Table-specific numeric conversions
        if table_name == 'tyu5_trades':
            # Note: 'Price' column is actually 'Price_Decimal' in the DataFrame
            numeric_cols = ['Quantity', 'Price_Decimal', 'Realized_PNL', 'Fees']
            for col in numeric_cols:
                if col in clean_df.columns:
                    clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
                    
        elif table_name == 'tyu5_positions':
            # All PNL columns should be numeric
            pnl_cols = [col for col in clean_df.columns if 'PNL' in col or 'Price' in col or 'Value' in col]
            numeric_cols = ['Net_Quantity', 'Closed_Quantity', 'Avg_Entry_Price'] + pnl_cols
            for col in numeric_cols:
                if col in clean_df.columns:
                    clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
                    
        elif table_name == 'tyu5_summary':
            # Summary has 'Metric', 'Value', 'Details' columns
            # Only 'Value' should be numeric
            if 'Value' in clean_df.columns:
                clean_df['Value'] = pd.to_numeric(clean_df['Value'], errors='coerce')
                    
        elif table_name == 'tyu5_risk_matrix':
            # Risk matrix has Position_ID, TYU5_Price, TYU5_Price_32nds, Price_Change, Scenario_PNL
            numeric_cols = ['TYU5_Price', 'Price_Change', 'Scenario_PNL']
            for col in numeric_cols:
                if col in clean_df.columns:
                    clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
        
        # tyu5_position_breakdown has mixed types, preserve as-is after "awaiting data" replacement
        
        return clean_df
    
    def _create_runs_table(self, conn: sqlite3.Connection):
        """Create the tyu5_runs metadata table if it doesn't exist."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tyu5_runs (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                trades_count INTEGER,
                positions_count INTEGER,
                total_pnl REAL,
                excel_file_path TEXT,
                execution_time_seconds REAL
            )
        """)
        conn.commit()
        
    def write_results(self, 
                      dataframes: Dict[str, pd.DataFrame],
                      run_metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Write TYU5 results directly to database.
        
        Args:
            dataframes: Dictionary with keys:
                - processed_trades_df
                - positions_df
                - summary_df
                - risk_df
                - breakdown_df
            run_metadata: Dictionary with:
                - run_id (optional, will generate if not provided)
                - timestamp (optional, will use current if not provided)
                - excel_file_path
                - execution_time_seconds
                
        Returns:
            (success: bool, error_message: Optional[str])
        """
        # Generate run_id if not provided
        run_id = run_metadata.get('run_id', str(uuid.uuid4()))
        timestamp = run_metadata.get('timestamp', datetime.now().isoformat())
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Create runs table if needed
            self._create_runs_table(conn)
            
            # Track metadata
            trades_count = 0
            positions_count = 0
            total_pnl = None
            tables_written = []
            
            # Write each DataFrame
            for df_key, table_name in self.TABLE_MAPPING.items():
                if df_key not in dataframes:
                    # Make pnl_components_df optional for backward compatibility
                    if df_key == 'pnl_components_df':
                        continue
                    raise ValueError(f"Missing required DataFrame: {df_key}")
                
                df = dataframes[df_key]
                
                # Clean the DataFrame
                clean_df = self._clean_dataframe(df, table_name)
                
                # Write to database (replace existing data)
                clean_df.to_sql(table_name, conn, if_exists='replace', index=False)
                tables_written.append(table_name)
                
                # Collect metadata
                if df_key == 'processed_trades_df':
                    trades_count = len(clean_df)
                elif df_key == 'positions_df':
                    positions_count = len(clean_df)
                elif df_key == 'summary_df' and not clean_df.empty:
                    # Get total P&L from summary - it's in the 'Value' column where 'Metric' is 'Total PNL'
                    total_row = clean_df[clean_df['Metric'] == 'Total PNL']
                    if not total_row.empty and 'Value' in total_row.columns:
                        total_pnl = total_row.iloc[0]['Value']
                        if pd.isna(total_pnl):
                            total_pnl = None
            
            # Write run metadata
            conn.execute("""
                INSERT OR REPLACE INTO tyu5_runs 
                (run_id, timestamp, status, error_message, trades_count, 
                 positions_count, total_pnl, excel_file_path, execution_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                timestamp,
                'success',
                None,  # No error
                trades_count,
                positions_count,
                total_pnl,
                run_metadata.get('excel_file_path'),
                run_metadata.get('execution_time_seconds')
            ))
            
            # Commit transaction
            conn.commit()
            
            print(f"Successfully wrote {len(tables_written)} tables to database:")
            for table in tables_written:
                print(f"  - {table}")
            print(f"Run ID: {run_id}")
            
            return True, None
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            
            error_msg = f"Error writing to database: {str(e)}"
            
            # Try to log the error in runs table
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO tyu5_runs 
                    (run_id, timestamp, status, error_message, trades_count, 
                     positions_count, total_pnl, excel_file_path, execution_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    timestamp,
                    'error',
                    error_msg,
                    0,
                    0,
                    None,
                    run_metadata.get('excel_file_path'),
                    run_metadata.get('execution_time_seconds')
                ))
                conn.commit()
            except:
                # If we can't even log the error, just continue
                pass
            
            return False, error_msg
            
        finally:
            conn.close()
            
    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Get information about the latest run."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT * FROM tyu5_runs 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
        except:
            return None
        finally:
            conn.close() 