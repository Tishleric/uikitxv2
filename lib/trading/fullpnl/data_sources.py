"""
Database adapters for FULLPNL automation.

Provides unified interfaces to:
- P&L database (positions, trades)
- Spot Risk database (Greeks, market data) 
- Market Prices database (futures/options prices)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class BaseDatabase:
    """Base class for database connections."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        
    @property
    def conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # Enable column access by name
        return self._conn
        
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query with parameters."""
        return self.conn.execute(query, params)
        
    def fetchall_dict(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts."""
        cursor = self.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Tuple[Any]]:
        """Execute a query and return a single row."""
        cursor = self.execute(query, params)
        return cursor.fetchone()
        
    def fetchone_dict(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and return a single row as a dict."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
        

class PnLDatabase(BaseDatabase):
    """Adapter for P&L tracker database."""
    
    def get_all_symbols(self) -> List[str]:
        """Get all unique symbols from positions table."""
        query = """
            SELECT DISTINCT instrument_name as symbol
            FROM positions
            WHERE instrument_name IS NOT NULL
            ORDER BY instrument_name
        """
        results = self.fetchall_dict(query)
        return [r['symbol'] for r in results]
        
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions with details."""
        query = """
            SELECT 
                instrument_name as symbol,
                position_quantity as open_position,
                avg_cost,
                total_realized_pnl,
                unrealized_pnl,
                last_market_price,
                is_option,
                option_strike,
                option_expiry,
                closed_quantity as closed_position
            FROM positions
            WHERE position_quantity != 0 OR closed_quantity != 0
            ORDER BY instrument_name
        """
        return self.fetchall_dict(query)
        
    def get_fullpnl_columns(self) -> List[str]:
        """Get existing columns in FULLPNL table."""
        cursor = self.execute("PRAGMA table_info(FULLPNL)")
        return [col[1] for col in cursor.fetchall()]
        
    def fullpnl_exists(self) -> bool:
        """Check if FULLPNL table exists."""
        cursor = self.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='FULLPNL'
        """)
        return cursor.fetchone() is not None
        

class SpotRiskDatabase(BaseDatabase):
    """Adapter for spot risk database."""
    
    def get_latest_spot_risk_data(self, bloomberg_symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get latest spot risk data for symbols.
        
        Matches by strike and instrument_type (PUT/CALL), not by symbol name.
        This follows the pattern from the standalone scripts.
        """
        if not bloomberg_symbols:
            return {}
            
        # Get latest session
        session_query = """
            SELECT session_id 
            FROM spot_risk_sessions 
            ORDER BY start_time DESC 
            LIMIT 1
        """
        session_result = self.fetchone(session_query)
        if not session_result:
            return {}
            
        session_id = session_result[0]
        
        # Contract to expiry mappings (from standalone scripts)
        CONTRACT_MAPPINGS = {
            '3MN': '18JUL25',    # 3M series
            '3M': '18JUL25',     # Alternative for 3M series
            'VBYN': '21JUL25',   # VBY series  
            'TYWN': '23JUL25',   # TWN series
        }
        
        # Parse Bloomberg symbols to extract strike and type
        parsed_symbols = []
        symbol_mapping = {}  # Map (strike, type, expiry) to original symbol
        
        for symbol in bloomberg_symbols:
            # Remove " Comdty" suffix
            clean_symbol = symbol.replace(' Comdty', '').strip()
            parts = clean_symbol.split()
            
            if len(parts) == 2:
                # Option format: CONTRACT STRIKE
                contract_part = parts[0]
                strike = float(parts[1])
                
                # Extract option type
                if 'P' in contract_part:
                    instrument_type = 'PUT'
                elif 'C' in contract_part:
                    instrument_type = 'CALL'
                else:
                    continue
                
                # Extract contract code and map to expiry
                expiry = None
                for prefix, mapped_expiry in CONTRACT_MAPPINGS.items():
                    if contract_part.startswith(prefix):
                        expiry = mapped_expiry
                        break
                        
                if expiry:
                    parsed_symbols.append((strike, instrument_type, expiry))
                    symbol_mapping[(strike, instrument_type, expiry)] = symbol
                else:
                    # If no mapping found, try without expiry
                    parsed_symbols.append((strike, instrument_type, None))
                    symbol_mapping[(strike, instrument_type, None)] = symbol
                    
            elif len(parts) == 1:
                # Future - query by symbol for futures
                parsed_symbols.append(('FUTURE', clean_symbol, None))
                symbol_mapping[('FUTURE', clean_symbol, None)] = symbol
        
        if not parsed_symbols:
            return {}
        
        # Build query for options
        data_by_symbol = {}
        
        for parsed in parsed_symbols:
            if parsed[0] == 'FUTURE':
                # For futures, use symbol-based query
                future_symbol = parsed[1]
                
                # Map TYU5 to SEP25 for spot risk lookup
                search_pattern = future_symbol
                if future_symbol == 'TYU5':
                    search_pattern = 'SEP25'
                    
                query = f"""
                    SELECT 
                        sr.instrument_key,
                        sr.midpoint_price,
                        sr.vtexp,
                        json_extract(sr.raw_data, '$.bid') as bid,
                        json_extract(sr.raw_data, '$.ask') as ask,
                        json_extract(sr.raw_data, '$.adjtheor') as adjtheor
                    FROM spot_risk_raw sr
                    WHERE sr.session_id = ?
                      AND sr.instrument_key LIKE ?
                    ORDER BY sr.id DESC
                    LIMIT 1
                """
                result = self.fetchone_dict(query, (session_id, f'%{search_pattern}%'))
                
                if result:
                    original_symbol = symbol_mapping[parsed]
                    data_by_symbol[original_symbol] = dict(result)
            else:
                # For options, match by strike, type, and expiry (if available)
                strike, instrument_type, expiry = parsed
                
                # Build query with optional expiry
                if expiry:
                    query = """
                        SELECT 
                            sr.instrument_key,
                            sr.midpoint_price,
                            sr.vtexp,
                            json_extract(sr.raw_data, '$.bid') as bid,
                            json_extract(sr.raw_data, '$.ask') as ask,
                            json_extract(sr.raw_data, '$.adjtheor') as adjtheor,
                            sc.delta_F,
                            sc.delta_y,
                            sc.gamma_F,
                            sc.gamma_y,
                            sc.speed_F,
                            sc.theta_F,
                            sc.vega_price,
                            sc.vega_y,
                            sc.implied_vol,
                            sc.calculation_status
                        FROM spot_risk_raw sr
                        LEFT JOIN spot_risk_calculated sc ON sr.id = sc.raw_id
                        WHERE sr.session_id = ?
                          AND sr.instrument_type = ?
                          AND sr.strike = ?
                          AND sr.expiry_date = ?
                          AND (sc.calculation_status = 'success' OR sc.calculation_status IS NULL)
                        ORDER BY sr.id DESC
                        LIMIT 1
                    """
                    result = self.fetchone_dict(query, (session_id, instrument_type, strike, expiry))
                else:
                    # Without expiry constraint
                    query = """
                        SELECT 
                            sr.instrument_key,
                            sr.midpoint_price,
                            sr.vtexp,
                            json_extract(sr.raw_data, '$.bid') as bid,
                            json_extract(sr.raw_data, '$.ask') as ask,
                            json_extract(sr.raw_data, '$.adjtheor') as adjtheor,
                            sc.delta_F,
                            sc.delta_y,
                            sc.gamma_F,
                            sc.gamma_y,
                            sc.speed_F,
                            sc.theta_F,
                            sc.vega_price,
                            sc.vega_y,
                            sc.implied_vol,
                            sc.calculation_status
                        FROM spot_risk_raw sr
                        LEFT JOIN spot_risk_calculated sc ON sr.id = sc.raw_id
                        WHERE sr.session_id = ?
                          AND sr.instrument_type = ?
                          AND sr.strike = ?
                          AND (sc.calculation_status = 'success' OR sc.calculation_status IS NULL)
                        ORDER BY sr.id DESC
                        LIMIT 1
                    """
                    result = self.fetchone_dict(query, (session_id, instrument_type, strike))
                
                if result:
                    original_symbol = symbol_mapping[parsed]
                    # Map database column names to expected names
                    data = dict(result)
                    # Rename Greek columns to match expected names
                    if 'delta_F' in data:
                        data['delta_F'] = data['delta_F']
                    if 'gamma_F' in data:
                        data['gamma_F'] = data['gamma_F']
                    if 'speed_F' in data:
                        data['speed_F'] = data['speed_F']
                    if 'theta_F' in data:
                        data['theta_F'] = data['theta_F']
                    if 'vega_price' in data:
                        data['vega_f'] = data['vega_price']
                    
                    data_by_symbol[original_symbol] = data
            
        return data_by_symbol
        
    def get_vtexp_mappings(self) -> Dict[str, float]:
        """Get all vtexp mappings."""
        query = "SELECT symbol, vtexp FROM vtexp_mappings"
        results = self.fetchall_dict(query)
        return {r['symbol']: r['vtexp'] for r in results}
        

class MarketPricesDatabase(BaseDatabase):
    """Adapter for market prices database."""
    
    def get_latest_prices(self, symbols: List[str], as_of_date: Optional[date] = None) -> Dict[str, Dict[str, float]]:
        """Get latest market prices for symbols.
        
        Returns dict mapping symbol to {current_price, prior_close}.
        """
        if not symbols:
            return {}
            
        prices = {}
        
        # Process futures
        # Check for options by looking for strike price pattern (numbers after letters)
        futures_symbols = []
        options_symbols = []
        
        for s in symbols:
            # Options have format like "3MN5P 110.000 Comdty" or "VBYN25P3 109.500 Comdty"
            # Futures have format like "TYU5 Comdty"
            parts = s.split()
            if len(parts) >= 2 and parts[1].replace('.', '').isdigit():
                # Has a strike price - it's an option
                options_symbols.append(s)
            else:
                # No strike price - it's a future
                futures_symbols.append(s.replace(' Comdty', ''))
                
        if futures_symbols:
            prices.update(self._get_futures_prices(futures_symbols, as_of_date))
            
        # Process options (keep full symbol with strike)
        if options_symbols:
            prices.update(self._get_options_prices(options_symbols, as_of_date))
            
        return prices
        
    def _get_futures_prices(self, symbols: List[str], as_of_date: Optional[date]) -> Dict[str, Dict[str, float]]:
        """Get futures prices."""
        placeholders = ','.join(['?' for _ in symbols])
        
        if as_of_date:
            query = f"""
                SELECT symbol, Flash_Close as current_price, prior_close
                FROM futures_prices
                WHERE symbol IN ({placeholders})
                  AND trade_date <= ?
                ORDER BY symbol, trade_date DESC
            """
            params = tuple(symbols) + (as_of_date,)
        else:
            query = f"""
                SELECT symbol, Flash_Close as current_price, prior_close
                FROM futures_prices
                WHERE symbol IN ({placeholders})
                ORDER BY symbol, trade_date DESC
            """
            params = tuple(symbols)
            
        results = self.fetchall_dict(query, params)
        
        # Get first non-null price for each symbol
        prices = {}
        current_prices = {}
        prior_closes = {}
        
        for row in results:
            symbol = row['symbol'] + ' Comdty'  # Add back Bloomberg suffix
            
            # Track first non-null current_price
            if symbol not in current_prices and row['current_price'] is not None:
                current_prices[symbol] = row['current_price']
                
            # Track first (latest) prior_close
            if symbol not in prior_closes and row['prior_close'] is not None:
                prior_closes[symbol] = row['prior_close']
                
        # Combine results
        for symbol in set(list(current_prices.keys()) + list(prior_closes.keys())):
            prices[symbol] = {
                'current_price': current_prices.get(symbol),
                'prior_close': prior_closes.get(symbol)
            }
                
        return prices
        
    def _get_options_prices(self, symbols: List[str], as_of_date: Optional[date]) -> Dict[str, Dict[str, float]]:
        """Get options prices."""
        placeholders = ','.join(['?' for _ in symbols])
        
        if as_of_date:
            query = f"""
                SELECT symbol, Flash_Close as current_price, prior_close
                FROM options_prices
                WHERE symbol IN ({placeholders})
                  AND trade_date <= ?
                ORDER BY symbol, trade_date DESC
            """
            params = tuple(symbols) + (as_of_date,)
        else:
            query = f"""
                SELECT symbol, Flash_Close as current_price, prior_close
                FROM options_prices
                WHERE symbol IN ({placeholders})
                ORDER BY symbol, trade_date DESC
            """
            params = tuple(symbols)
            
        results = self.fetchall_dict(query, params)
        
        # Get first (latest) price for each symbol
        prices = {}
        for row in results:
            symbol = row['symbol']
            if symbol not in prices:
                prices[symbol] = {
                    'current_price': row['current_price'],
                    'prior_close': row['prior_close']
                }
                
        return prices
        
    def get_latest_trade_dates(self) -> Tuple[Optional[date], Optional[date]]:
        """Get T and T+1 dates from market prices.
        
        Returns (T, T+1) where T is latest trade date with prior_close = NULL
        and T+1 is latest date with prior_close != NULL.
        """
        # Get T (latest date with NULL prior_close)
        cursor = self.execute("""
            SELECT MAX(trade_date) as t_date
            FROM futures_prices
            WHERE prior_close IS NULL
        """)
        result = cursor.fetchone()
        t_date = datetime.strptime(result[0], '%Y-%m-%d').date() if result and result[0] else None
        
        # Get T+1 (latest date with non-NULL prior_close)
        cursor = self.execute("""
            SELECT MAX(trade_date) as t_plus_1_date
            FROM futures_prices
            WHERE prior_close IS NOT NULL
        """)
        result = cursor.fetchone()
        t_plus_1_date = datetime.strptime(result[0], '%Y-%m-%d').date() if result and result[0] else None
        
        return t_date, t_plus_1_date 