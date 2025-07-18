"""TYU5 P&L Engine Adapter

This adapter queries UIKitXv2 data stores and formats the data
for the TYU5 P&L calculation engine. All prices remain decimal
throughout - no 32nds conversion.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import sys
import os

# Import our storage first
from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.symbol_translator import SymbolTranslator

logger = logging.getLogger(__name__)


class TYU5Adapter:
    """Adapter to connect UIKitXv2 data stores to TYU5 P&L engine."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the adapter.
        
        Args:
            db_path: Path to SQLite database (defaults to data/output/pnl/pnl_tracker.db)
        """
        self.storage = PnLStorage(db_path or "data/output/pnl/pnl_tracker.db")
        self.symbol_translator = SymbolTranslator()
        
        # Store TYU5 path for later import
        self.tyu5_path = Path(__file__).parent.parent / "pnl" / "tyu5_pnl"
        
    def get_trades_for_calculation(self, trade_date: Optional[date] = None) -> pd.DataFrame:
        """Query cto_trades table and format for TYU5.
        
        Args:
            trade_date: Date to get trades for (None for all trades)
            
        Returns:
            DataFrame with TYU5 expected columns
        """
        # Build query
        if trade_date:
            query = """
            SELECT * FROM cto_trades 
            WHERE Date = ? 
            AND is_sod = 0 
            AND is_exercise = 0
            ORDER BY Date, Time
            """
            params = [trade_date.isoformat()]
        else:
            query = """
            SELECT * FROM cto_trades 
            WHERE is_sod = 0 
            AND is_exercise = 0
            ORDER BY Date, Time
            """
            params = []
            
        # Get data
        conn = self.storage._get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            logger.warning(f"No trades found for {trade_date or 'all dates'}")
            return pd.DataFrame()
            
        # Transform to TYU5 format
        tyu5_trades = pd.DataFrame({
            'Date': pd.to_datetime(df['Date']),
            'Time': df['Time'],
            'Symbol': df['Symbol'],
            'Action': df['Action'],
            'Quantity': df['Quantity'].abs(),  # TYU5 expects positive quantities
            'Price': df['Price'],  # Already decimal, no conversion needed
            'Fees': df['Fees'],
            'Counterparty': df['Counterparty'],
            'trade_id': df['tradeID'],
            'Type': df['Type']
        })
        
        # Transform option symbols to TYU5 format
        # Bloomberg format: "VBYN25C2 108.750 Comdty" with Type="CALL"
        # TYU5 format: "VBYN25C2 C 108.750"
        for idx, row in tyu5_trades.iterrows():
            if row['Type'] in ['CALL', 'PUT']:
                # Parse Bloomberg format symbol
                symbol_parts = str(row['Symbol']).split()
                if len(symbol_parts) >= 2:
                    base_symbol = symbol_parts[0]  # e.g., "VBYN25C2"
                    strike = symbol_parts[1]        # e.g., "108.750"
                    # Convert Type to single character
                    type_char = 'C' if row['Type'] == 'CALL' else 'P'
                    # Map Bloomberg symbol to CME format for calendar lookup
                    cme_symbol = self._map_bloomberg_to_cme(base_symbol)
                    # Reconstruct in TYU5 format with CME symbol
                    tyu5_trades.at[idx, 'Symbol'] = f"{cme_symbol} {type_char} {strike}"
        
        logger.info(f"Prepared {len(tyu5_trades)} trades for TYU5 calculation")
        return tyu5_trades
        
    def _map_bloomberg_to_cme(self, bloomberg_symbol: str) -> str:
        """Map Bloomberg option symbol to CME calendar symbol.
        
        Bloomberg format: VBYN25C2 (VBY + N + 25 + C + 2)
        CME format: VY2N5 (VY + 2 + N + 5)
        
        Args:
            bloomberg_symbol: Bloomberg option symbol
            
        Returns:
            CME calendar symbol
        """
        # Create reverse mapping from Bloomberg contract to CME series
        bloomberg_to_cme = {
            'VBY': 'VY',  # Monday
            'TJP': 'GY',  # Tuesday (GY in CME calendar)
            'TYW': 'WY',  # Wednesday
            'TJW': 'HY',  # Thursday (HY in CME calendar)
            '3M': 'ZN',   # Friday
        }
        
        # Handle special case for 3MN5P format (already close to CME)
        if bloomberg_symbol.startswith('3M'):
            # Extract parts: 3MN5P -> ZN + week + month + year
            if len(bloomberg_symbol) >= 5:
                month = bloomberg_symbol[2]  # N
                year = bloomberg_symbol[3]   # 5
                # For 3MN5P, we need to determine the week - using 3 as default
                return f"ZN3{month}{year}"
            return bloomberg_symbol  # Fallback
        
        # Parse standard Bloomberg format (e.g., VBYN25C2)
        if len(bloomberg_symbol) >= 8:
            contract = bloomberg_symbol[:3]  # VBY
            month = bloomberg_symbol[3]      # N
            year = bloomberg_symbol[5]        # 5 (from 25)
            # type = bloomberg_symbol[6]     # C/P (not needed for CME)
            week = bloomberg_symbol[7]        # 2
            
            # Get CME series code
            cme_series = bloomberg_to_cme.get(contract, contract[:2])
            
            # Construct CME symbol
            return f"{cme_series}{week}{month}{year}"
        
        # If we can't parse it, return as-is
        return bloomberg_symbol
        
    def _convert_cme_to_bloomberg_base(self, cme_symbol: str) -> str:
        """Convert CME option base symbol back to Bloomberg base.
        
        Example: "VY3N5" -> "VBYN25P3" (without strike/type)
        
        Args:
            cme_symbol: CME format symbol (e.g., "VY3N5")
            
        Returns:
            Bloomberg base symbol
        """
        # Reverse mapping from CME to Bloomberg
        cme_to_bloomberg = {
            'VY': 'VBY',  # Monday
            'GY': 'TJP',  # Tuesday
            'WY': 'TYW',  # Wednesday
            'HY': 'TJW',  # Thursday
            'ZN': '3M',   # Friday
        }
        
        # Parse CME format: VY3N5 -> VY + 3 + N + 5
        if len(cme_symbol) >= 5:
            series = cme_symbol[:2]  # VY
            week = cme_symbol[2]     # 3
            month = cme_symbol[3]    # N
            year = cme_symbol[4]     # 5
            
            # Get Bloomberg prefix
            bloomberg_prefix = cme_to_bloomberg.get(series, series)
            
            # For 3M series, format is different
            if bloomberg_prefix == '3M':
                # 3MN5P format (3M + month + year + P/C)
                # We'll add P for put later when we know the type
                return f"{bloomberg_prefix}{month}{year}P"
            else:
                # Standard format: VBYN25P3
                # We need to determine if it's a put or call - we know the type from parsing
                # For now, construct base without type indicator
                return f"{bloomberg_prefix}{month}2{year}P{week}"
        
        return cme_symbol  # Fallback
        
    def get_market_prices_for_symbols(self, symbols: List[str], price_date: Optional[date] = None) -> pd.DataFrame:
        """Get market prices for specific symbols from trades.
        
        Args:
            symbols: List of symbols in TYU5 format (e.g., "TYU5", "VBYN25P3 P 110.250")
            price_date: Date to get prices for (None for latest)
            
        Returns:
            DataFrame with columns: Symbol, Current_Price, Prior_Close
        """
        market_prices_db = Path("data/output/market_prices/market_prices.db")
        
        if not market_prices_db.exists():
            logger.warning(f"Market prices database not found: {market_prices_db}")
            return pd.DataFrame({'Symbol': [], 'Current_Price': [], 'Prior_Close': []})
        
        import sqlite3
        conn = sqlite3.connect(str(market_prices_db))
        
        result_rows = []
        
        for symbol in symbols:
            # Parse the symbol to determine if it's a future or option
            symbol_parts = str(symbol).split()
            
            # Remove 'Comdty' suffix if present
            if symbol_parts and symbol_parts[-1] == 'Comdty':
                symbol_parts = symbol_parts[:-1]
            
            if len(symbol_parts) == 1:
                # Simple future symbol like "TYU5"
                query = """
                SELECT symbol, current_price, prior_close 
                FROM futures_prices 
                WHERE symbol = ?
                """
                if price_date:
                    query += " AND trade_date = ?"
                    params = [symbol_parts[0], price_date.isoformat()]
                else:
                    params = [symbol_parts[0]]
                    
                df = pd.read_sql_query(query, conn, params=params)
                if not df.empty:
                    result_rows.append({
                        'Symbol': symbol,
                        'Current_Price': df.iloc[0]['current_price'],
                        'Prior_Close': df.iloc[0]['prior_close']
                    })
                    
            elif len(symbol_parts) >= 3:
                # Option symbol like "VY3N5 P 110.250" (CME format from TYU5)
                # Need to convert back to Bloomberg format for database lookup
                cme_base = symbol_parts[0]      # VY3N5
                option_type = symbol_parts[1]   # P
                strike = symbol_parts[2]        # 110.250
                
                # Convert CME base back to Bloomberg base
                bloomberg_base = self._convert_cme_to_bloomberg_base(cme_base)
                
                # Fix the Bloomberg symbol construction based on the actual database format
                # The database stores full Bloomberg symbols like "VBYN25P3 109.500 Comdty"
                # We need to inject the option type into the base symbol
                if bloomberg_base.endswith('P'):
                    # Replace the default P with the actual option type
                    bloomberg_base = bloomberg_base[:-1] + option_type
                elif '3M' in bloomberg_base:
                    # For Friday options, format is "3MN5P" or "3MN5C"
                    # Remove the trailing P and add the actual type
                    bloomberg_base = bloomberg_base[:-1] + option_type
                else:
                    # For other weeklies, insert the type before the week number
                    # VBYN25P3 -> VBY + N + 25 + P + 3
                    if len(bloomberg_base) >= 8:
                        # Extract parts: VBYN25P3
                        prefix = bloomberg_base[:3]   # VBY
                        month = bloomberg_base[3]     # N
                        year = bloomberg_base[4:6]    # 25
                        week = bloomberg_base[7]      # 3
                        bloomberg_base = f"{prefix}{month}{year}{option_type}{week}"
                
                # Construct full Bloomberg symbol for DB lookup
                bloomberg_symbol = f"{bloomberg_base} {strike} Comdty"
                
                logger.debug(f"Option lookup: {symbol} -> {bloomberg_symbol}")
                
                query = """
                SELECT symbol, current_price, prior_close 
                FROM options_prices 
                WHERE symbol = ?
                """
                if price_date:
                    query += " AND trade_date = ?"
                    params = [bloomberg_symbol, price_date.isoformat()]
                else:
                    params = [bloomberg_symbol]
                    
                df = pd.read_sql_query(query, conn, params=params)
                if not df.empty:
                    # Use prior_close if current_price is NULL
                    current = df.iloc[0]['current_price']
                    if pd.isna(current):
                        current = df.iloc[0]['prior_close']
                        
                    result_rows.append({
                        'Symbol': symbol,
                        'Current_Price': current,
                        'Prior_Close': df.iloc[0]['prior_close']
                    })
                else:
                    logger.debug(f"No market price found for option: {bloomberg_symbol}")
        
        conn.close()
        
        result_df = pd.DataFrame(result_rows)
        logger.info(f"Found market prices for {len(result_df)}/{len(symbols)} symbols")
        
        return result_df
        
    def get_market_prices(self, price_date: Optional[date] = None) -> pd.DataFrame:
        """Get market prices for all symbols.
        
        Args:
            price_date: Date to get prices for (None for latest)
            
        Returns:
            DataFrame with TYU5 expected columns
        """
        # Connect to the correct market prices database
        market_prices_db = Path("data/output/market_prices/market_prices.db")
        
        if not market_prices_db.exists():
            logger.warning(f"Market prices database not found: {market_prices_db}")
            return pd.DataFrame({'Symbol': [], 'Current_Price': [], 'Prior_Close': []})
        
        import sqlite3
        conn = sqlite3.connect(str(market_prices_db))
        
        # Query futures prices
        futures_query = """
        SELECT 
            symbol as Ticker,
            current_price as PX_LAST,
            prior_close as PX_SETTLE,
            NULL as EXPIRE_DT,
            NULL as MONEYNESS,
            'FUTURE' as asset_type
        FROM futures_prices
        WHERE current_price IS NOT NULL OR prior_close IS NOT NULL
        """
        
        # Query options prices
        options_query = """
        SELECT 
            symbol as Ticker,
            current_price as PX_LAST,
            prior_close as PX_SETTLE,
            expire_dt as EXPIRE_DT,
            moneyness as MONEYNESS,
            'OPTION' as asset_type
        FROM options_prices
        WHERE current_price IS NOT NULL OR prior_close IS NOT NULL
        """
        
        if price_date:
            # Get prices for specific date
            futures_query += f" AND trade_date = '{price_date.isoformat()}'"
            options_query += f" AND trade_date = '{price_date.isoformat()}'"
            
        # Execute queries and combine results
        try:
            futures_df = pd.read_sql_query(futures_query, conn)
            options_df = pd.read_sql_query(options_query, conn)
            prices_df = pd.concat([futures_df, options_df], ignore_index=True)
        except Exception as e:
            logger.error(f"Error querying market prices: {e}")
            prices_df = pd.DataFrame()
        finally:
            conn.close()
        
        if prices_df.empty:
            logger.warning("No market prices found")
            return pd.DataFrame({'Ticker': [], 'PX_LAST': [], 'PX_SETTLE': [], 'EXPIRE_DT': [], 'MONEYNESS': []})
        
        # Remove duplicates, keeping most recent price for each ticker
        prices_df = prices_df.drop_duplicates(subset=['Ticker'], keep='first')
        
        # Map Bloomberg symbols to TYU5 format
        prices_df['Ticker'] = prices_df.apply(self._map_to_tyu5_symbol, axis=1)
        
        # Select columns for TYU5 - it expects Symbol, Current_Price, Prior_Close
        result_df = pd.DataFrame({
            'Symbol': prices_df['Ticker'],  # TYU5 expects 'Symbol' not 'Ticker'
            'Current_Price': prices_df['PX_LAST'],
            'Prior_Close': prices_df['PX_SETTLE']
        })
        
        # Add optional columns if present (but TYU5 doesn't use these in update_prices)
        if 'EXPIRE_DT' in prices_df.columns:
            result_df['EXPIRE_DT'] = prices_df['EXPIRE_DT']
        if 'MONEYNESS' in prices_df.columns:
            result_df['MONEYNESS'] = prices_df['MONEYNESS']
            
        logger.info(f"Prepared {len(result_df)} market prices for TYU5 calculation")
        return result_df
        
    def _map_to_tyu5_symbol(self, row: pd.Series) -> str:
        """Map bloomberg symbol to TYU5 format.
        
        Args:
            row: Series with 'Ticker' and 'asset_type' columns
            
        Returns:
            TYU5-formatted symbol
        """
        ticker = str(row['Ticker'])
        asset_type = str(row.get('asset_type', ''))
        
        # For futures: TY -> TYU5
        if asset_type == 'FUTURE' or 'Comdty' not in ticker:
            if ticker == 'TY':
                return 'TYU5'
            return ticker
            
        # For options: Already in correct format (e.g., "VBYN25C2 110.750 Comdty")
        # Just remove " Comdty" suffix if present
        return ticker.replace(' Comdty', '')
        
    def prepare_excel_data(self, trade_date: Optional[date] = None) -> Dict[str, pd.DataFrame]:
        """Prepare data in the format TYU5 expects from Excel.
        
        Args:
            trade_date: Date to calculate for (None for all)
            
        Returns:
            Dictionary with 'Trades_Input' and 'Market_Prices' DataFrames
        """
        trades_df = self.get_trades_for_calculation(trade_date)
        
        # Get unique symbols from trades to query specific market prices
        if not trades_df.empty:
            unique_symbols = trades_df['Symbol'].unique().tolist()
            prices_df = self.get_market_prices_for_symbols(unique_symbols, trade_date)
        else:
            prices_df = pd.DataFrame({'Symbol': [], 'Current_Price': [], 'Prior_Close': []})
        
        # TYU5 expects these exact sheet names
        return {
            'Trades_Input': trades_df,
            'Market_Prices': prices_df
        }
        
    def run_calculation(self, 
                       output_file: str,
                       trade_date: Optional[date] = None,
                       base_price: float = 120.0,
                       price_range: Tuple[float, float] = (-3, 3),
                       steps: int = 13) -> bool:
        """Run TYU5 P&L calculation with data from our stores.
        
        Args:
            output_file: Path for output Excel/CSV file
            trade_date: Date to calculate for (None for all)
            base_price: Base price for risk matrix
            price_range: Price range for risk scenarios
            steps: Number of steps in risk matrix
            
        Returns:
            True if calculation succeeded
        """
        try:
            # Prepare data
            excel_data = self.prepare_excel_data(trade_date)
            
            if excel_data['Trades_Input'].empty:
                logger.warning("No trades to process")
                return False
                
            # Log summary
            logger.info(f"Running TYU5 calculation:")
            logger.info(f"  - Trades: {len(excel_data['Trades_Input'])}")
            logger.info(f"  - Prices: {len(excel_data['Market_Prices'])}")
            logger.info(f"  - Output: {output_file}")
            
            # Debug: Log the data columns
            logger.debug(f"Trades_Input columns: {excel_data['Trades_Input'].columns.tolist()}")
            logger.debug(f"Market_Prices columns: {excel_data['Market_Prices'].columns.tolist()}")
            
            # Import and run TYU5 calculation
            # Dynamic import to avoid circular dependency issues
            sys.path.insert(0, str(self.tyu5_path))
            
            # Convert output file to absolute path since we're changing directories
            output_file_abs = os.path.abspath(output_file)
            
            # Save current directory and change to TYU5 directory
            original_cwd = os.getcwd()
            os.chdir(str(self.tyu5_path))
            
            try:
                from main import run_pnl_analysis
                
                run_pnl_analysis(
                    input_file=None,  # We're passing data directly
                    output_file=output_file_abs,
                    base_price=base_price,
                    price_range=price_range,
                    steps=steps,
                    sample_data=excel_data  # Our data mimics the sample structure
                )
            finally:
                # Restore original directory
                os.chdir(original_cwd)
                # Clean up sys.path
                if str(self.tyu5_path) in sys.path:
                    sys.path.remove(str(self.tyu5_path))
            
            logger.info(f"TYU5 calculation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running TYU5 calculation: {e}")
            return False
            
    def get_calculation_summary(self, excel_data: Dict[str, pd.DataFrame]) -> Dict:
        """Get summary statistics for console output.
        
        Args:
            excel_data: Data prepared for TYU5
            
        Returns:
            Dictionary with summary stats
        """
        trades_df = excel_data.get('Trades_Input', pd.DataFrame())
        prices_df = excel_data.get('Market_Prices', pd.DataFrame())
        
        if trades_df.empty:
            return {'error': 'No trades data'}
            
        # Calculate summary
        summary = {
            'total_trades': len(trades_df),
            'unique_symbols': trades_df['Symbol'].nunique() if 'Symbol' in trades_df else 0,
            'date_range': {
                'start': trades_df['Date'].min() if 'Date' in trades_df else None,
                'end': trades_df['Date'].max() if 'Date' in trades_df else None
            },
            'total_buys': len(trades_df[trades_df['Action'] == 'BUY']) if 'Action' in trades_df else 0,
            'total_sells': len(trades_df[trades_df['Action'] == 'SELL']) if 'Action' in trades_df else 0,
            'prices_loaded': len(prices_df),
            'futures_count': len(trades_df[trades_df['Type'] == 'FUT']) if 'Type' in trades_df else 0,
            'options_count': len(trades_df[trades_df['Type'] == 'OPT']) if 'Type' in trades_df else 0
        }
        
        return summary 