"""
FULLPNL Builder

Combines TYU5 positions data with spot risk Greeks to create the unified FULLPNL table.
Handles symbol translation, data merging, and database updates.
"""

import logging
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
import glob
import os

from .fullpnl_symbol_mapper import FULLPNLSymbolMapper
from ..market_prices.centralized_symbol_translator import CentralizedSymbolTranslator, SymbolFormat
from ..market_prices.strike_converter import StrikeConverter

logger = logging.getLogger(__name__)


class FULLPNLBuilder:
    """Builds and maintains the FULLPNL table from TYU5 and spot risk data."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        """Initialize builder.
        
        Args:
            db_path: Path to database containing TYU5 data and FULLPNL table
        """
        self.db_path = db_path
        self.symbol_mapper = FULLPNLSymbolMapper()
        self.centralized_translator = CentralizedSymbolTranslator()
        self.spot_risk_dir = Path("data/output/spot_risk")
        
        # Load ExpirationCalendar for CME to XCME base mapping
        self._load_expiration_calendar()
        
    def _load_expiration_calendar(self):
        """Load the expiration calendar for CME to XCME base mapping."""
        calendar_path = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
        self.expiration_df = pd.read_csv(calendar_path)
        
        # Create CME to XCME base mapping
        self.cme_to_xcme_base = {}
        for _, row in self.expiration_df.iterrows():
            if pd.notna(row['CME']) and pd.notna(row['XCME']):
                self.cme_to_xcme_base[row['CME']] = row['XCME']
                
        logger.info(f"Loaded {len(self.cme_to_xcme_base)} CME to XCME mappings")
        
    def build_fullpnl(self) -> bool:
        """Build/update FULLPNL table with latest data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting FULLPNL table build")
            
            # Create FULLPNL table if it doesn't exist
            self._ensure_fullpnl_table()
            
            # Load TYU5 positions data
            tyu5_positions = self._load_tyu5_positions()
            if tyu5_positions.empty:
                logger.warning("No TYU5 positions data found")
                return False
                
            logger.info(f"Loaded {len(tyu5_positions)} TYU5 positions")
            
            # Load latest spot risk data
            spot_risk_data = self._load_latest_spot_risk()
            if spot_risk_data.empty:
                logger.warning("No spot risk data found - proceeding with positions only")
                
            logger.info(f"Loaded {len(spot_risk_data)} spot risk records")
            
            # Create symbol mapping (TYU5 to Bloomberg for display)
            tyu5_symbols = tyu5_positions['Symbol'].unique().tolist()
            symbol_mapping = self.symbol_mapper.create_symbol_mapping(tyu5_symbols)
            
            # Merge the data using direct CME to XCME mapping
            fullpnl_data = self._merge_data(tyu5_positions, spot_risk_data, symbol_mapping)
            
            # Write to FULLPNL table
            success = self._write_fullpnl(fullpnl_data)
            
            if success:
                logger.info(f"Successfully built FULLPNL table with {len(fullpnl_data)} records")
            else:
                logger.error("Failed to write FULLPNL data")
                
            return success
            
        except Exception as e:
            logger.error(f"Error building FULLPNL table: {e}")
            return False
    
    def _ensure_fullpnl_table(self):
        """Create FULLPNL table with correct schema."""
        # Drop existing table if it exists (may have wrong schema)
        drop_sql = "DROP TABLE IF EXISTS FULLPNL;"
        
        schema_sql = """
        CREATE TABLE FULLPNL (
            -- Identity columns
            symbol_tyu5 TEXT PRIMARY KEY,
            symbol_bloomberg TEXT,
            type TEXT,
            
            -- Position data from tyu5_positions
            net_quantity REAL,
            closed_quantity REAL,
            avg_entry_price REAL,
            current_price REAL,
            flash_close REAL,
            prior_close REAL,
            current_present_value REAL,
            prior_present_value REAL,
            unrealized_pnl_current REAL,
            unrealized_pnl_flash REAL,
            unrealized_pnl_close REAL,
            realized_pnl REAL,
            daily_pnl REAL,
            total_pnl REAL,
            
            -- Greeks F-space from spot_risk
            vtexp REAL,
            dv01_f REAL,
            delta_f REAL,
            gamma_f REAL,
            speed_f REAL,
            theta_f REAL,
            vega_f REAL,
            
            -- Greeks Y-space from spot_risk
            dv01_y REAL,
            delta_y REAL,
            gamma_y REAL,
            speed_y REAL,
            theta_y REAL,
            vega_y REAL,
            
            -- Metadata
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            spot_risk_file TEXT,
            tyu5_run_id TEXT
        );
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(drop_sql)
                conn.execute(schema_sql)
                conn.commit()
                logger.debug("FULLPNL table schema recreated")
        except Exception as e:
            logger.error(f"Failed to create FULLPNL table: {e}")
            raise
    
    def _load_tyu5_positions(self) -> pd.DataFrame:
        """Load positions data from TYU5 table.
        
        Returns:
            DataFrame with TYU5 positions data
        """
        query = """
        SELECT 
            Symbol,
            Type,
            Net_Quantity,
            Closed_Quantity,
            Avg_Entry_Price,
            Current_Price,
            Flash_Close,
            Prior_Close,
            Current_Present_Value,
            Prior_Present_Value,
            Unrealized_PNL_Current,
            Unrealized_PNL_Flash,
            Unrealized_PNL_Close,
            Realized_PNL,
            Daily_PNL,
            Total_PNL
        FROM tyu5_positions
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn)
                logger.debug(f"Loaded {len(df)} TYU5 positions")
                return df
        except Exception as e:
            logger.error(f"Failed to load TYU5 positions: {e}")
            return pd.DataFrame()
    
    def _load_latest_spot_risk(self) -> pd.DataFrame:
        """Load latest spot risk CSV file.
        
        Returns:
            DataFrame with spot risk data including Greeks
        """
        try:
            # Find the most recent spot risk CSV
            pattern = str(self.spot_risk_dir / "**/*.csv")
            csv_files = glob.glob(pattern, recursive=True)
            
            if not csv_files:
                logger.warning(f"No spot risk CSV files found in {self.spot_risk_dir}")
                return pd.DataFrame()
            
            # Get the most recent file
            latest_file = max(csv_files, key=os.path.getmtime)
            logger.info(f"Loading spot risk data from: {os.path.basename(latest_file)}")
            
            # Load the CSV
            df = pd.read_csv(latest_file)
            
            # Store the filename for metadata
            self.latest_spot_risk_file = os.path.basename(latest_file)
            
            # Standardize column names
            df.columns = df.columns.str.upper()
            
            # Filter for required columns if they exist
            required_cols = ['KEY', 'ITYPE']
            greek_cols_f = ['VTEXP', 'DV01', 'DELTA_F', 'GAMMA_F', 'SPEED_F', 'THETA_F', 'VEGA_PRICE']
            greek_cols_y = ['DV01_Y', 'DELTA_Y', 'GAMMA_Y', 'SPEED_Y', 'THETA_Y', 'VEGA_Y']
            
            available_cols = [col for col in required_cols + greek_cols_f + greek_cols_y 
                            if col in df.columns]
            
            if 'KEY' not in df.columns:
                logger.error("Spot risk CSV missing required 'KEY' column")
                return pd.DataFrame()
                
            # Select available columns
            df_filtered = df[available_cols].copy()
            
            # Keep all valid entries including futures
            df_filtered = df_filtered[
                (~df_filtered['KEY'].str.contains('INVALID', na=False)) &
                (df_filtered['KEY'].notna())
            ]
            
            logger.debug(f"Filtered to {len(df_filtered)} spot risk records")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Failed to load spot risk data: {e}")
            return pd.DataFrame()
    
    def _tyu5_to_xcme(self, tyu5_symbol: str) -> Optional[str]:
        """Convert TYU5 symbol to XCME format.
        
        Args:
            tyu5_symbol: Symbol like "VY3N5 P 110.25"
            
        Returns:
            XCME symbol like "XCME.VY3.21JUL25.110:25.P" or None
        """
        try:
            # Parse TYU5 symbol
            parts = tyu5_symbol.strip().split()
            if len(parts) != 3:
                # Handle futures
                if parts[0] in self.cme_to_xcme_base:
                    xcme_base = self.cme_to_xcme_base[parts[0]]
                    # Futures don't have strike/type, return just base
                    return xcme_base.replace('.', '.', 1)  # Ensure proper format
                return None
                
            base = parts[0]  # VY3N5
            opt_type = parts[1]  # P
            strike_str = parts[2]  # 110.25
            
            # Look up XCME base
            if base not in self.cme_to_xcme_base:
                logger.debug(f"No XCME mapping for CME base: {base}")
                return None
                
            xcme_base = self.cme_to_xcme_base[base]  # XCME.VY3.21JUL25
            
            # Convert strike to XCME format (with colon notation)
            xcme_strike = StrikeConverter.decimal_to_xcme(strike_str)
            
            # Construct full XCME symbol
            xcme_symbol = f"{xcme_base}.{xcme_strike}.{opt_type}"
            
            return xcme_symbol
            
        except Exception as e:
            logger.debug(f"Failed to convert TYU5 to XCME: {tyu5_symbol} - {e}")
            return None
    
    def _merge_data(self, tyu5_positions: pd.DataFrame, spot_risk_data: pd.DataFrame, 
                   symbol_mapping: Dict[str, str]) -> pd.DataFrame:
        """Merge TYU5 positions with spot risk Greeks.
        
        Args:
            tyu5_positions: TYU5 positions DataFrame
            spot_risk_data: Spot risk DataFrame
            symbol_mapping: TYU5 -> Bloomberg symbol mapping
            
        Returns:
            Merged DataFrame for FULLPNL table
        """
        try:
            # Start with TYU5 positions as base
            merged = tyu5_positions.copy()
            
            # Add Bloomberg symbols
            merged['symbol_bloomberg'] = merged['Symbol'].map(symbol_mapping)
            
            # Rename columns to match FULLPNL schema
            column_mapping = {
                'Symbol': 'symbol_tyu5',
                'Type': 'type',
                'Net_Quantity': 'net_quantity',
                'Closed_Quantity': 'closed_quantity',
                'Avg_Entry_Price': 'avg_entry_price',
                'Current_Price': 'current_price',
                'Flash_Close': 'flash_close',
                'Prior_Close': 'prior_close',
                'Current_Present_Value': 'current_present_value',
                'Prior_Present_Value': 'prior_present_value',
                'Unrealized_PNL_Current': 'unrealized_pnl_current',
                'Unrealized_PNL_Flash': 'unrealized_pnl_flash',
                'Unrealized_PNL_Close': 'unrealized_pnl_close',
                'Realized_PNL': 'realized_pnl',
                'Daily_PNL': 'daily_pnl',
                'Total_PNL': 'total_pnl'
            }
            
            merged = merged.rename(columns=column_mapping)
            
            # Initialize Greek columns with NULL
            greek_columns = [
                'vtexp', 'dv01_f', 'delta_f', 'gamma_f', 'speed_f', 'theta_f', 'vega_f',
                'dv01_y', 'delta_y', 'gamma_y', 'speed_y', 'theta_y', 'vega_y'
            ]
            
            for col in greek_columns:
                merged[col] = None
            
            # Merge spot risk data if available
            if not spot_risk_data.empty and 'KEY' in spot_risk_data.columns:
                # Create TYU5 to XCME mapping
                tyu5_to_xcme_map = {}
                for tyu5_symbol in merged['symbol_tyu5'].unique():
                    xcme_symbol = self._tyu5_to_xcme(tyu5_symbol)
                    if xcme_symbol:
                        tyu5_to_xcme_map[tyu5_symbol] = xcme_symbol
                
                # Create reverse mapping: XCME -> TYU5
                xcme_to_tyu5 = {v: k for k, v in tyu5_to_xcme_map.items()}
                
                # Track matches for logging
                matched_count = 0
                checked_count = 0
                
                # Process each spot risk record
                for _, spot_row in spot_risk_data.iterrows():
                    spot_symbol = spot_row['KEY']
                    checked_count += 1
                    
                    # Find matching TYU5 symbol
                    tyu5_symbol = xcme_to_tyu5.get(spot_symbol)
                    
                    if tyu5_symbol:
                        # Find the row to update
                        mask = merged['symbol_tyu5'] == tyu5_symbol
                        if mask.any():
                            matched_count += 1
                            
                            # Map spot risk columns to FULLPNL columns
                            spot_risk_mapping = {
                                'VTEXP': 'vtexp',
                                'DV01': 'dv01_f',
                                'DELTA_F': 'delta_f',
                                'GAMMA_F': 'gamma_f',
                                'SPEED_F': 'speed_f',
                                'THETA_F': 'theta_f',
                                'VEGA_PRICE': 'vega_f',
                                'DV01_Y': 'dv01_y',
                                'DELTA_Y': 'delta_y',
                                'GAMMA_Y': 'gamma_y',
                                'SPEED_Y': 'speed_y',
                                'THETA_Y': 'theta_y',
                                'VEGA_Y': 'vega_y'
                            }
                            
                            # Update Greek values
                            for spot_col, fullpnl_col in spot_risk_mapping.items():
                                if spot_col in spot_row.index and pd.notna(spot_row[spot_col]):
                                    merged.loc[mask, fullpnl_col] = spot_row[spot_col]
                
                logger.info(f"Matched {matched_count} of {checked_count} spot risk records to TYU5 positions")
                
                # Log sample mappings for debugging
                if tyu5_to_xcme_map:
                    sample_mappings = list(tyu5_to_xcme_map.items())[:3]
                    for tyu5, xcme in sample_mappings:
                        logger.debug(f"Sample mapping: {tyu5} -> {xcme}")
            
            # Add metadata
            merged['last_update'] = datetime.now()
            merged['spot_risk_file'] = getattr(self, 'latest_spot_risk_file', None)
            
            # Get latest TYU5 run ID if available
            try:
                with sqlite3.connect(self.db_path) as conn:
                    run_query = "SELECT run_id FROM tyu5_runs ORDER BY timestamp DESC LIMIT 1"
                    run_result = pd.read_sql_query(run_query, conn)
                    if not run_result.empty:
                        merged['tyu5_run_id'] = run_result.iloc[0]['run_id']
                    else:
                        merged['tyu5_run_id'] = None
            except:
                merged['tyu5_run_id'] = None
            
            logger.info(f"Merged data: {len(merged)} positions with Greeks")
            return merged
            
        except Exception as e:
            logger.error(f"Failed to merge data: {e}")
            return pd.DataFrame()
    
    def _write_fullpnl(self, fullpnl_data: pd.DataFrame) -> bool:
        """Write merged data to FULLPNL table.
        
        Args:
            fullpnl_data: DataFrame with merged FULLPNL data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM FULLPNL")
                
                # Insert new data
                fullpnl_data.to_sql('FULLPNL', conn, if_exists='append', index=False)
                
                conn.commit()
                logger.info(f"Successfully wrote {len(fullpnl_data)} records to FULLPNL table")
                return True
                
        except Exception as e:
            logger.error(f"Failed to write FULLPNL data: {e}")
            return False 