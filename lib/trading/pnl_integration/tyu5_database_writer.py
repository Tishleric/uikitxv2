"""TYU5 Database Writer

This module handles persisting TYU5 P&L calculation results to the database,
including lot positions, Greeks, risk scenarios, and P&L attribution.
"""

import logging
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import traceback

logger = logging.getLogger(__name__)


class TYU5DatabaseWriter:
    """Writes TYU5 calculation results to database tables."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        """Initialize the database writer.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._vtexp_cache = None
        self._vtexp_load_time = None
        
    def _convert_32nds_to_decimal(self, price_str: str) -> float:
        """Convert price from 32nds format to decimal.
        
        Args:
            price_str: Price in format like "110-20" or decimal like "110.625"
            
        Returns:
            Price as decimal float
        """
        if isinstance(price_str, (int, float)):
            return float(price_str)
            
        price_str = str(price_str).strip()
        
        # Check if already decimal
        if '.' in price_str and '-' not in price_str:
            return float(price_str)
            
        # Handle 32nds format (e.g., "110-20" means 110 + 20/32)
        if '-' in price_str:
            parts = price_str.split('-')
            if len(parts) == 2:
                whole = float(parts[0])
                fraction = float(parts[1]) / 32.0
                return whole + fraction
                
        # Try to convert as-is
        try:
            return float(price_str)
        except ValueError:
            logger.warning(f"Could not convert price '{price_str}' to decimal")
            return 0.0
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
        
    def _load_latest_vtexp(self) -> Dict[str, float]:
        """Load the most recent vtexp CSV file.
        
        Returns:
            Dictionary mapping symbol to vtexp value
        """
        # Check cache first (valid for 1 hour)
        if self._vtexp_cache and self._vtexp_load_time:
            if (datetime.now() - self._vtexp_load_time).seconds < 3600:
                return self._vtexp_cache
                
        vtexp_dir = Path("data/input/vtexp")
        if not vtexp_dir.exists():
            logger.warning("vtexp directory not found")
            return {}
            
        # Find most recent vtexp file
        vtexp_files = list(vtexp_dir.glob("vtexp_*.csv"))
        if not vtexp_files:
            logger.warning("No vtexp files found")
            return {}
            
        latest_file = max(vtexp_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Loading vtexp from: {latest_file}")
        
        # Load and cache
        try:
            vtexp_df = pd.read_csv(latest_file)
            self._vtexp_cache = dict(zip(vtexp_df['symbol'], vtexp_df['vtexp']))
            self._vtexp_load_time = datetime.now()
            return self._vtexp_cache
        except Exception as e:
            logger.error(f"Error loading vtexp file: {e}")
            return {}
            
    def write_results(self, 
                     positions_df: pd.DataFrame,
                     trades_df: pd.DataFrame,
                     breakdown_df: pd.DataFrame,
                     risk_df: Optional[pd.DataFrame] = None,
                     summary_df: Optional[pd.DataFrame] = None,
                     calc_timestamp: Optional[datetime] = None) -> bool:
        """Write all TYU5 results to database.
        
        Args:
            positions_df: Current positions with P&L
            trades_df: Processed trades
            breakdown_df: Position breakdown (lot details)
            risk_df: Risk matrix scenarios (optional)
            summary_df: P&L summary (optional)
            calc_timestamp: Calculation timestamp (defaults to now)
            
        Returns:
            True if successful, False otherwise
        """
        if calc_timestamp is None:
            calc_timestamp = datetime.now()
            
        conn = self._get_connection()
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Get run ID for this calculation
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM tyu5_runs")
            result = cursor.fetchone()
            run_id = (result[0] or 0) + 1 if result else 1
            
            # Write lot positions
            self._write_lot_positions(conn, breakdown_df, calc_timestamp)
            
            # Write position Greeks (for options)
            self._write_position_greeks(conn, positions_df, calc_timestamp)
            
            # Write P&L components if available
            if 'PNL_Components' in positions_df.columns:
                self._write_pnl_components(conn, positions_df, breakdown_df, run_id, calc_timestamp)
            
            # Write risk scenarios
            if risk_df is not None:
                self._write_risk_scenarios(conn, risk_df, positions_df, calc_timestamp)
                
            # Write match history from trades
            self._write_match_history(conn, trades_df, calc_timestamp)
            
            # Update positions table with short quantities
            self._update_positions_table(conn, positions_df)
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully wrote TYU5 results to database at {calc_timestamp}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error writing TYU5 results: {e}")
            traceback.print_exc()  # Print full traceback
            return False
        finally:
            conn.close()

    def _write_pnl_components(self, 
                            conn: sqlite3.Connection, 
                            positions_df: pd.DataFrame,
                            breakdown_df: pd.DataFrame,
                            run_id: int,
                            calc_timestamp: datetime) -> None:
        """Write P&L components to database with proper error handling for missing prices.
        
        Args:
            conn: Database connection
            positions_df: Positions with PNL_Components column
            breakdown_df: Lot breakdown for mapping
            run_id: Calculation run ID
            calc_timestamp: Timestamp of calculation
        """
        cursor = conn.cursor()
        components_written = 0
        missing_price_warnings = []
        
        try:
            # Clear old components for this run
            cursor.execute("""
                DELETE FROM tyu5_pnl_components 
                WHERE calculation_run_id = ?
            """, (run_id,))
            
            for _, position in positions_df.iterrows():
                symbol = position['Symbol']
                
                # Skip if no components
                if pd.isna(position.get('PNL_Components')):
                    continue
                
                # Check for detailed components (new approach)
                detailed_components = None
                if 'detailed_components' in position:
                    detailed_components = position['detailed_components']
                elif hasattr(position.get('PNL_Components'), '__iter__') and 'detailed_components' in position.get('PNL_Components', {}):
                    detailed_components = position['PNL_Components'].get('detailed_components', [])
                
                # If we have detailed components, write them
                if detailed_components:
                    for comp in detailed_components:
                        # Get lot info from breakdown
                        lot_id = getattr(comp, 'lot_id', f"LOT_{symbol}_{components_written}")
                        
                        cursor.execute("""
                            INSERT INTO tyu5_pnl_components
                            (lot_id, symbol, component_type, start_time, end_time,
                             start_price, end_price, quantity, pnl_amount, 
                             start_settlement_key, end_settlement_key,
                             calculation_run_id, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            lot_id,
                            symbol,
                            comp.period_type,
                            comp.start_time,
                            comp.end_time,
                            comp.start_price,
                            comp.end_price,
                            0,  # Quantity - we'll update this later
                            comp.pnl_amount,
                            comp.start_settlement_key,
                            comp.end_settlement_key,
                            run_id,
                            calc_timestamp
                        ))
                        components_written += 1
                else:
                    # Fallback to aggregated components (old approach)
                    components = position.get('PNL_Components', {})
                    
                    if isinstance(components, dict):
                        for comp_type, comp_amount in components.items():
                            if comp_amount != 0:  # Only store non-zero components
                                cursor.execute("""
                                    INSERT INTO tyu5_pnl_components
                                    (lot_id, symbol, component_type, start_time, end_time,
                                     start_price, end_price, quantity, pnl_amount, 
                                     calculation_run_id, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    f"AGG_{symbol}_{comp_type}",
                                    symbol,
                                    comp_type,
                                    calc_timestamp,  # Placeholder
                                    calc_timestamp,  # Placeholder
                                    0,  # Placeholder
                                    0,  # Placeholder
                                    0,  # Placeholder
                                    comp_amount,
                                    run_id,
                                    calc_timestamp
                                ))
                                components_written += 1
                
                # Check for missing settlement prices
                if position.get('Settlement_PNL_Total') == 'MISSING_PRICE':
                    missing_price_warnings.append({
                        'symbol': symbol,
                        'message': 'Missing settlement price for P&L calculation'
                    })
            
            # Log warnings for missing prices
            if missing_price_warnings:
                logger.warning(f"Missing settlement prices for {len(missing_price_warnings)} symbols:")
                for warning in missing_price_warnings:
                    logger.warning(f"  - {warning['symbol']}: {warning['message']}")
                    
                # Write to alerts table
                cursor.execute("""
                    INSERT INTO tyu5_alerts (alert_type, message, details, created_at)
                    VALUES ('MISSING_SETTLEMENT_PRICE', ?, ?, ?)
                """, (
                    f"Missing settlement prices for {len(missing_price_warnings)} symbols",
                    json.dumps(missing_price_warnings),
                    calc_timestamp
                ))
            
            logger.info(f"Wrote {components_written} P&L components for run {run_id}")
            
        except Exception as e:
            logger.error(f"Error writing P&L components: {e}")
            raise
            
    def _map_symbol_to_bloomberg(self, symbol: str) -> str:
        """Map TYU5 internal symbol format to Bloomberg format for position lookup.
        
        Args:
            symbol: TYU5 format symbol (e.g., "VY3N5", "TYU5")
            
        Returns:
            Bloomberg format symbol
        """
        # For futures, no change needed
        if len(symbol) <= 5 and not any(c in symbol for c in ['VY', 'GY', 'WY', 'HY']):
            return symbol + " Comdty"
            
        # For options, need to map from CME format back to Bloomberg
        # VY3N5 -> VBYN25P3 (base symbol without strike/type)
        cme_to_bloomberg = {
            'VY': 'VBY',  # Monday
            'GY': 'TJP',  # Tuesday  
            'WY': 'TYW',  # Wednesday
            'HY': 'TJW',  # Thursday
            'ZN': '3M',   # Friday (special case - already in right format)
        }
        
        # Parse CME format (e.g., VY3N5)
        if len(symbol) >= 5:
            series = symbol[:2]
            if series in cme_to_bloomberg:
                week = symbol[2]
                month_year = symbol[3:5]
                
                if series == 'ZN':
                    # Friday options: 3MN5
                    bloomberg_base = f"3M{month_year}"
                else:
                    # Mon-Thu: VBYN25P3 format
                    # Map single letter month to numeric
                    month_map = {'F': '01', 'G': '02', 'H': '03', 'J': '04', 'K': '05', 'M': '06',
                               'N': '07', 'Q': '08', 'U': '09', 'V': '10', 'X': '11', 'Z': '12'}
                    month_letter = symbol[3]
                    month_num = month_map.get(month_letter, '00')
                    year = symbol[4]
                    
                    bloomberg_base = f"{cme_to_bloomberg[series]}{month_letter}2{year}P{week}"
                    
                # This will be used to match against positions table which has full symbol
                return bloomberg_base  # Return base without " Comdty" suffix
                
        # Default - return as is
        return symbol
    
    def _write_lot_positions(self, conn: sqlite3.Connection, 
                           breakdown_df: pd.DataFrame,
                           calc_timestamp: datetime):
        """Write lot positions from breakdown data."""
        if breakdown_df.empty:
            return
            
        # Filter for OPEN_POSITION rows only (not SUMMARY rows)
        open_positions = breakdown_df[breakdown_df['Label'] == 'OPEN_POSITION'].copy()
        if open_positions.empty:
            return
            
        # Clear existing lot positions for symbols in this calculation
        symbols = open_positions['Symbol'].unique().tolist()
        if not symbols:
            return
        
        placeholders = ','.join('?' * len(symbols))
        conn.execute(f"""
            DELETE FROM lot_positions 
            WHERE symbol IN ({placeholders})
        """, symbols)
        
        # Prepare lot position records
        lot_records = []
        for idx, row in open_positions.iterrows():
            # Extract lot details from breakdown
            symbol = row['Symbol']
            
            # Parse trade ID from Description (e.g., "POS_TYU5 Comdty_001")
            description = row.get('Description', '')
            trade_id = description.split('_')[-1] if description and '_' in description else f"LOT_{idx}"
            
            # Get quantity and price
            quantity = float(row.get('Quantity', 0))
            price_raw = row.get('Price', 0)
            price = self._convert_32nds_to_decimal(str(price_raw))
            
            # Map symbol to Bloomberg format to find position_id
            bloomberg_symbol = self._map_symbol_to_bloomberg(str(symbol))
            
            # Try to find position_id
            position_id = None
            
            # For options, need to search more broadly as the symbol might have strike info
            if any(prefix in symbol for prefix in ['VY', 'GY', 'WY', 'HY']):
                # Query positions table for matching option
                cursor = conn.execute("""
                    SELECT id FROM positions 
                    WHERE instrument_name LIKE ? || '%'
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (bloomberg_symbol,))
            else:
                # For futures, exact match
                cursor = conn.execute("""
                    SELECT id FROM positions 
                    WHERE instrument_name = ?
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (bloomberg_symbol,))
                
            result = cursor.fetchone()
            if result:
                position_id = result[0]
            
            if quantity != 0:  # Only store non-zero lots
                # Use the mapped Bloomberg symbol for consistency
                # For options without full strike info, we need to get it from positions table
                storage_symbol = symbol  # Default to original
                
                if position_id and any(prefix in symbol for prefix in ['VY', 'GY', 'WY', 'HY']):
                    # Get the full Bloomberg symbol from positions table
                    cursor = conn.execute("""
                        SELECT instrument_name FROM positions WHERE id = ?
                    """, (position_id,))
                    result = cursor.fetchone()
                    if result:
                        storage_symbol = result[0]
                elif not str(symbol).endswith(' Comdty'):
                    # For futures or other symbols, ensure Bloomberg format
                    storage_symbol = bloomberg_symbol if bloomberg_symbol.endswith(' Comdty') else f"{bloomberg_symbol} Comdty"
                
                lot_records.append((
                    storage_symbol,  # Use Bloomberg format symbol
                    trade_id,
                    quantity,  # remaining_quantity
                    price,     # entry_price
                    str(calc_timestamp),  # entry_date (using calc timestamp)
                    position_id,
                    calc_timestamp  # created_at
                ))
                
        # Bulk insert
        if lot_records:
            conn.executemany("""
                INSERT INTO lot_positions 
                (symbol, trade_id, remaining_quantity, entry_price, entry_date,
                 position_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, lot_records)
            logger.info(f"Inserted {len(lot_records)} lot positions")
            
    def _write_position_greeks(self, conn: sqlite3.Connection,
                              positions_df: pd.DataFrame,
                              calc_timestamp: datetime):
        """Write Greek values for option positions."""
        if positions_df.empty:
            return
            
        # Load vtexp data
        vtexp_map = self._load_latest_vtexp()
        
        # Filter for options only
        options_df = positions_df[positions_df['Type'].isin(['CALL', 'PUT'])].copy()
        if options_df.empty:
            return
            
        greek_records = []
        for _, pos in options_df.iterrows():
            symbol = pos['Symbol']
            
            # Get position_id from positions table
            cursor = conn.execute("""
                SELECT id FROM positions 
                WHERE instrument_name = ?
            """, (symbol,))
            result = cursor.fetchone()
            position_id = result[0] if result else None
            
            if position_id:
                # Calculate Greeks if available in the dataframe
                # TYU5 might provide these, or we calculate them
                underlying_price = pos.get('Current_Price', pos.get('Avg_Entry_Price', 0))
                
                greek_records.append((
                    position_id,
                    calc_timestamp,
                    float(underlying_price),
                    float(pos.get('Implied_Vol', 0.0)),  # May need calculation
                    float(pos.get('Delta', 0.0)),
                    float(pos.get('Gamma', 0.0)),
                    float(pos.get('Vega', 0.0)),
                    float(pos.get('Theta', 0.0)),
                    float(pos.get('Speed', 0.0)),
                    calc_timestamp
                ))
                
        # Bulk insert Greeks
        if greek_records:
            conn.executemany("""
                INSERT INTO position_greeks
                (position_id, calc_timestamp, underlying_price, implied_vol,
                 delta, gamma, vega, theta, speed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, greek_records)
            logger.info(f"Inserted {len(greek_records)} Greek records")
            
    def _write_risk_scenarios(self, conn: sqlite3.Connection,
                            risk_df: pd.DataFrame,
                            positions_df: pd.DataFrame,
                            calc_timestamp: datetime):
        """Write risk scenario matrix data."""
        if risk_df.empty:
            return
            
        # Clear old scenarios (keep 7 days as per partial index)
        # TODO: Fix partial index issue with datetime() in SQLite
        # conn.execute("""
        #     DELETE FROM risk_scenarios 
        #     WHERE calc_timestamp < datetime('now', '-7 days')
        # """)
        
        # Prepare scenario records
        scenario_records = []
        
        # TYU5 Risk matrix has columns: Position_ID (symbol), TYU5_Price, Price_Change, Scenario_PNL
        if 'Position_ID' not in risk_df.columns or 'Scenario_PNL' not in risk_df.columns:
            logger.warning("Risk matrix missing required columns")
            return
            
        # Process each row
        for _, row in risk_df.iterrows():
            symbol = row['Position_ID']
            scenario_price = float(row.get('TYU5_Price', 0))
            scenario_pnl = float(row.get('Scenario_PNL', 0))
            
            # Get position quantity from positions_df
            pos_rows = positions_df[positions_df['Symbol'] == symbol]
            position_qty = float(pos_rows['Net_Quantity'].iloc[0]) if not pos_rows.empty else 0
            
            scenario_records.append((
                calc_timestamp,
                symbol,
                scenario_price,
                scenario_pnl,
                None,  # scenario_delta
                None,  # scenario_gamma  
                position_qty,
                calc_timestamp
            ))
                    
        # Bulk insert scenarios
        if scenario_records:
            # Batch insert in chunks of 500 for performance
            chunk_size = 500
            for i in range(0, len(scenario_records), chunk_size):
                chunk = scenario_records[i:i + chunk_size]
                conn.executemany("""
                    INSERT INTO risk_scenarios
                    (calc_timestamp, symbol, scenario_price, scenario_pnl,
                     scenario_delta, scenario_gamma, position_quantity, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, chunk)
            logger.info(f"Inserted {len(scenario_records)} risk scenarios in chunks")
            
    def _write_match_history(self, conn: sqlite3.Connection,
                           trades_df: pd.DataFrame,
                           calc_timestamp: datetime):
        """Write FIFO match history from processed trades."""
        if trades_df.empty:
            return
            
        # TYU5 trades have match information we can extract
        match_records = []
        
        # Look for matched trades (trades with Realized_PnL)
        if 'Realized_PnL' not in trades_df.columns:
            logger.info("No Realized_PnL column in trades, skipping match history")
            return
            
        matched_trades = trades_df[trades_df['Realized_PnL'] != 0].copy()
        
        for _, trade in matched_trades.iterrows():
            # Extract match details from trade
            # This is a simplified version - actual TYU5 may provide more detail
            if 'Match_Details' in trade:
                # Parse match details if available
                pass
            else:
                # Create basic match record
                match_records.append((
                    trade['Symbol'],
                    trade.get('DateTime', calc_timestamp),
                    str(trade.get('Trade_ID', trade.get('trade_id', ''))),  # buy_trade_id
                    str(trade.get('Trade_ID', trade.get('trade_id', ''))),  # sell_trade_id (simplified)
                    abs(float(trade.get('Quantity', 0))),
                    float(trade.get('Price_Decimal', trade.get('Price', 0))),
                    float(trade.get('Price_Decimal', trade.get('Price', 0))),
                    float(trade.get('Realized_PnL', 0)),
                    calc_timestamp
                ))
                
        # Bulk insert matches
        if match_records:
            conn.executemany("""
                INSERT INTO match_history
                (symbol, match_date, buy_trade_id, sell_trade_id,
                 matched_quantity, buy_price, sell_price, realized_pnl, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, match_records)
            logger.info(f"Inserted {len(match_records)} match history records")
            
    def _update_positions_table(self, conn: sqlite3.Connection,
                               positions_df: pd.DataFrame):
        """Update positions table with short quantities and match history."""
        if positions_df.empty:
            return
            
        for _, pos in positions_df.iterrows():
            symbol = pos['Symbol']
            net_qty = float(pos.get('Net_Quantity', 0))
            
            # Calculate short quantity (negative positions)
            short_qty = abs(min(0, net_qty))
            
            # Update positions table
            conn.execute("""
                UPDATE positions 
                SET short_quantity = ?
                WHERE instrument_name = ?
            """, (short_qty, symbol))
            
        logger.info("Updated positions table with short quantities")
        
    def clear_calculation_data(self, calc_timestamp: datetime):
        """Clear data from a specific calculation run."""
        conn = self._get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # Clear lot positions by timestamp
            conn.execute("""
                DELETE FROM lot_positions 
                WHERE created_at = ?
            """, (calc_timestamp,))
            
            # Clear Greeks by timestamp
            conn.execute("""
                DELETE FROM position_greeks 
                WHERE calc_timestamp = ?
            """, (calc_timestamp,))
            
            # Clear risk scenarios by timestamp
            conn.execute("""
                DELETE FROM risk_scenarios 
                WHERE calc_timestamp = ?
            """, (calc_timestamp,))
            
            conn.commit()
            logger.info(f"Cleared calculation data for {calc_timestamp}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error clearing calculation data: {e}")
        finally:
            conn.close() 