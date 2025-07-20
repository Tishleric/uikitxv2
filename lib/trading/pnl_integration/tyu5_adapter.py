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
from lib.trading.market_prices.centralized_symbol_translator import CentralizedSymbolTranslator

logger = logging.getLogger(__name__)


class TYU5Adapter:
    """Adapter to connect UIKitXv2 data stores to TYU5 P&L engine."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the adapter.
        
        Args:
            db_path: Path to SQLite database (defaults to data/output/pnl/pnl_tracker.db)
        """
        self.storage = PnLStorage(db_path or "data/output/pnl/pnl_tracker.db")
        self.symbol_translator = CentralizedSymbolTranslator()
        
        # Store TYU5 path for later import
        self.tyu5_path = Path(__file__).parent.parent / "pnl" / "tyu5_pnl"
        
    def get_trades_for_calculation(self, trade_date: Optional[date] = None) -> pd.DataFrame:
        """Query cto_trades table and format for TYU5.
        
        Args:
            trade_date: Date to get trades for (None for most recent date)
            
        Returns:
            DataFrame with TYU5 expected columns
        """
        # If no date provided, get the most recent trade date
        if trade_date is None:
            query_latest = """
            SELECT MAX(Date) as latest_date 
            FROM cto_trades 
            WHERE is_exercise = 0
            """
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_latest)
            result = cursor.fetchone()
            
            if result and result['latest_date']:
                trade_date = datetime.strptime(result['latest_date'], '%Y-%m-%d').date()
                logger.info(f"Using most recent trade date: {trade_date}")
            else:
                logger.warning("No trades found in database")
                conn.close()
                return pd.DataFrame()
            conn.close()
        
        # Build query - now includes SOD trades but excludes exercises
        query = """
        SELECT * FROM cto_trades 
        WHERE Date = ? 
        AND is_exercise = 0
        ORDER BY is_sod DESC, Date, Time
        """
        params = [trade_date.isoformat()]
            
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
            'Type': df['Type'],
            'is_sod': df['is_sod']  # Include SOD flag for TYU5 to handle properly
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
                    # Use centralized translator to convert Bloomberg to CME format
                    cme_symbol = self.symbol_translator.translate(base_symbol, 'bloomberg', 'cme')
                    if not cme_symbol:
                        logger.warning(f"Could not translate symbol: {base_symbol}")
                        cme_symbol = base_symbol  # Fallback
                    # Reconstruct in TYU5 format with CME symbol (base only, no strike/type)
                    cme_base = cme_symbol.split()[0] if ' ' in cme_symbol else cme_symbol
                    tyu5_trades.at[idx, 'Symbol'] = f"{cme_base} {type_char} {strike}"
        
        logger.info(f"Prepared {len(tyu5_trades)} trades for TYU5 calculation")
        return tyu5_trades
        
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
            return pd.DataFrame({'Symbol': [], 'Current_Price': [], 'Flash_Close': [], 'Prior_Close': []})
        
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
                SELECT symbol, Current_Price, Flash_Close, prior_close 
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
                        'Current_Price': df.iloc[0]['Current_Price'],
                        'Flash_Close': df.iloc[0]['Flash_Close'],
                        'Prior_Close': df.iloc[0]['prior_close']
                    })
                    
            elif len(symbol_parts) >= 3:
                # Option symbol like "VY3N5 P 110.250" (CME format from TYU5)
                # Need to convert back to Bloomberg format for database lookup
                cme_base = symbol_parts[0]      # VY3N5
                option_type = symbol_parts[1]   # P
                strike = symbol_parts[2]        # 110.250
                
                # Use centralized translator to convert CME to Bloomberg
                bloomberg_full = self.symbol_translator.translate(cme_base, 'cme', 'bloomberg')
                if not bloomberg_full:
                    logger.warning(f"Could not translate CME symbol: {cme_base}")
                    # Construct a fallback Bloomberg symbol
                    bloomberg_symbol = f"{cme_base} {strike} Comdty"
                else:
                    # Extract base from full Bloomberg symbol (before strike)
                    bloomberg_parts = bloomberg_full.split()
                    if len(bloomberg_parts) >= 1:
                        bloomberg_base = bloomberg_parts[0]
                        # For options, ensure the type character matches
                        if len(bloomberg_base) > 6 and bloomberg_base[-2] in ['C', 'P']:
                            # Replace the option type character with the one from TYU5
                            bloomberg_base = bloomberg_base[:-2] + option_type + bloomberg_base[-1]
                        bloomberg_symbol = f"{bloomberg_base} {strike} Comdty"
                    else:
                        bloomberg_symbol = f"{cme_base} {strike} Comdty"
                
                logger.debug(f"Option lookup: {symbol} -> {bloomberg_symbol}")
                
                # Query for the option price
                option_query = """
                SELECT symbol, Current_Price, Flash_Close, prior_close 
                FROM options_prices 
                WHERE symbol = ?
                """
                if price_date:
                    option_query += " AND trade_date = ?"
                    option_params = [bloomberg_symbol, price_date.isoformat()]
                else:
                    option_params = [bloomberg_symbol]
                    
                opt_df = pd.read_sql_query(option_query, conn, params=option_params)
                if not opt_df.empty:
                    result_rows.append({
                        'Symbol': symbol,
                        'Current_Price': opt_df.iloc[0]['Current_Price'],
                        'Flash_Close': opt_df.iloc[0]['Flash_Close'], 
                        'Prior_Close': opt_df.iloc[0]['prior_close']
                    })
                    logger.debug(f"Found price for option {bloomberg_symbol}: {opt_df.iloc[0]['Flash_Close']}")
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
            return pd.DataFrame({'Symbol': [], 'Flash_Close': [], 'Prior_Close': []})
        
        import sqlite3
        conn = sqlite3.connect(str(market_prices_db))
        
        # Query futures prices - now all in Bloomberg format
        futures_query = """
        SELECT 
            symbol as Ticker,
            Current_Price,
            Flash_Close as PX_LAST,
            prior_close as PX_SETTLE,
            NULL as EXPIRE_DT,
            NULL as MONEYNESS,
            'FUTURE' as asset_type
        FROM futures_prices
        WHERE Flash_Close IS NOT NULL OR prior_close IS NOT NULL
        """
        
        # Query options prices - already in Bloomberg format
        options_query = """
        SELECT 
            symbol as Ticker,
            Current_Price,
            Flash_Close as PX_LAST,
            prior_close as PX_SETTLE,
            expire_dt as EXPIRE_DT,
            moneyness as MONEYNESS,
            'OPTION' as asset_type
        FROM options_prices
        WHERE Flash_Close IS NOT NULL OR prior_close IS NOT NULL
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
            return pd.DataFrame({'Symbol': [], 'Flash_Close': [], 'Prior_Close': []})
        
        # Remove duplicates, keeping most recent price for each ticker
        prices_df = prices_df.drop_duplicates(subset=['Ticker'], keep='first')
        
        # Store Bloomberg format for later lookup
        prices_df['Bloomberg_Symbol'] = prices_df['Ticker']
        
        # Map Bloomberg symbols to TYU5 format
        prices_df['Ticker'] = prices_df.apply(self._map_to_tyu5_symbol, axis=1)
        
        # Select columns for TYU5 - it expects Symbol, Current_Price, Flash_Close, Prior_Close
        result_df = pd.DataFrame({
            'Symbol': prices_df['Ticker'],  # TYU5 expects 'Symbol' not 'Ticker'
            'Current_Price': prices_df['Current_Price'],  # ACTIVE: added Current_Price
            'Flash_Close': prices_df['PX_LAST'],  # ACTIVE: renamed from Current_Price
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
        
        # Remove ' Comdty' suffix for all processing
        ticker_clean = ticker.replace(' Comdty', '').strip()
        
        # For futures: Keep as is (e.g., "TYU5 Comdty" -> "TYU5")
        if asset_type == 'FUTURE':
            return ticker_clean
            
        # For options: Need to transform Bloomberg to TYU5 format
        # Example: "VBYN25P3 110.250 Comdty" -> "VY3N5 P 110.250"
        if asset_type == 'OPTION':
            parts = ticker_clean.split()
            if len(parts) >= 2:
                bloomberg_base = parts[0]  # e.g., "VBYN25P3"
                strike = parts[1]          # e.g., "110.250"
                
                # Use centralized translator to convert Bloomberg to CME format
                cme_full = self.symbol_translator.translate(bloomberg_base, 'bloomberg', 'cme')
                if not cme_full:
                    logger.warning(f"Could not translate Bloomberg symbol: {bloomberg_base}")
                    cme_base = bloomberg_base  # Fallback
                else:
                    # Extract just the base part (before any strike/type)
                    cme_base = cme_full.split()[0]
                
                # Determine option type from Bloomberg symbol
                option_type = 'P' if 'P' in bloomberg_base else 'C'
                
                # Return TYU5 format
                return f"{cme_base} {option_type} {strike}"
                
        # Default: return cleaned ticker
        return ticker_clean
        
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
            prices_df = pd.DataFrame({'Symbol': [], 'Current_Price': [], 'Flash_Close': [], 'Prior_Close': []})
        
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