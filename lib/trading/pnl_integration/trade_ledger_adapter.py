"""Trade Ledger to TYU5 Direct Adapter

This adapter reads trade ledger CSV files directly and transforms them
into the format expected by TYU5 P&L engine, bypassing the database.
"""

import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import re
import glob
import os
import sqlite3

from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.pnl_integration.tyu5_runner import TYU5Runner
from lib.trading.pnl_integration.tyu5_history_db import TYU5HistoryDB

logger = logging.getLogger(__name__)


class TradeLedgerAdapter:
    """Direct adapter from trade ledger CSV to TYU5 format."""
    
    def __init__(self):
        """Initialize the adapter with symbol translator."""
        self.symbol_translator = SymbolTranslator()
        
    def get_latest_trade_ledger(self, directory: str = "data/input/trade_ledger") -> Optional[str]:
        """Find the most recent trade ledger file.
        
        Args:
            directory: Directory containing trade ledger files
            
        Returns:
            Path to the most recent trades_*.csv file or None if not found
        """
        pattern = os.path.join(directory, "trades_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            logger.error(f"No trade ledger files found in {directory}")
            return None
            
        # Get the most recent file by modification time
        latest_file = max(files, key=os.path.getmtime)
        logger.info(f"Found latest trade ledger: {latest_file}")
        return latest_file
        
    def read_trade_ledger(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """Read trade ledger CSV file.
        
        Expected columns:
        - tradeId
        - instrumentName (XCME format)
        - marketTradeTime
        - buySell
        - quantity
        - price
        """
        # If no filepath provided, get the latest
        if filepath is None:
            filepath = self.get_latest_trade_ledger()
            if not filepath:
                raise ValueError("No trade ledger files found")
                
        logger.info(f"Reading trade ledger from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} trades from {filepath}")
            logger.debug(f"Columns: {df.columns.tolist()}")
            
            # Filter out exercised/expired options (price = 0 on expiry date)
            original_count = len(df)
            df = df[df['price'] != 0]
            filtered_count = original_count - len(df)
            
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} exercised/expired options (price = 0)")
            else:
                logger.debug(f"No trades filtered (all {original_count} have non-zero prices)")
                
            return df
        except Exception as e:
            logger.error(f"Failed to read trade ledger: {e}")
            raise
            
    def _parse_xcme_symbol(self, xcme_symbol: str) -> Optional[Dict[str, Any]]:
        """Parse XCME symbol and determine type.
        
        Returns dict with:
        - type: 'FUT', 'CALL', or 'PUT'
        - tyu5_symbol: Formatted for TYU5
        - bloomberg_symbol: For reference
        """
        # Use new parsing method
        components = self.parse_xcme_symbol(xcme_symbol)
        
        if not components:
            logger.error(f"Unknown XCME format: {xcme_symbol}")
            return None
            
        if components['type'] == 'future':
            logger.debug(f"Future: product={components['product']}, month={components['month_code']}")
            
            # Map product codes
            product_map = {'ZN': 'TY', 'ZT': 'TU', 'ZF': 'FV', 'US': 'US', 'RX': 'RX'}
            base = product_map.get(components['product'], components['product'])
            
            # Build symbols
            year = '5'  # 2025
            tyu5_symbol = f"{base}{components['month_code']}{year}"
            bloomberg = f"{tyu5_symbol} Comdty"
            
            logger.info(f"Future: {xcme_symbol} → {tyu5_symbol}")
            return {
                'type': 'FUT',
                'tyu5_symbol': tyu5_symbol,
                'bloomberg_symbol': bloomberg
            }
            
        else:  # option
            logger.debug(f"Option: series={components['series']}, strike={components['strike']}")
            
            # Determine type from original symbol
            is_put = 'PADPS' in xcme_symbol
            opt_type = 'P' if is_put else 'C'
            
            # Check for July 25, 2025 special case (Friday option, not weekly)
            if components['expiry_date'] == '20250725':
                # This is a standard Friday option, not weekly
                # Format strike with 3 decimal places for Bloomberg
                strike_formatted = f"{float(components['strike']):.3f}"
                tyu5_symbol = f"OZNQ5 {opt_type} {components['strike']}"
                bloomberg = f"TYQ5{opt_type} {strike_formatted} Comdty"
                logger.info(f"July 25 Friday option: {xcme_symbol} → {tyu5_symbol}")
            else:
                # Build TYU5 format with occurrence
                year = '5'
                tyu5_base = f"{components['series']}{components['month_code']}{year}"
                tyu5_symbol = f"{tyu5_base} {opt_type} {components['strike']}"
                
                # Build Bloomberg - need special encoding for weekly options
                # Map series to Bloomberg format
                if components['product'] == 'ZN':
                    bbg_prefix = 'T'  # TY options
                elif components['product'] == 'VY':
                    bbg_prefix = 'VB'  # VY weekly options 
                elif components['product'] == 'WY':
                    bbg_prefix = 'WB'  # WY weekly options
                else:
                    bbg_prefix = components['product']
                    
                # Format strike with 3 decimal places for Bloomberg
                strike_formatted = f"{float(components['strike']):.3f}"
                bloomberg = f"{bbg_prefix}YN25{opt_type}{components.get('occurrence', '')} {strike_formatted} Comdty"
            
            logger.info(f"Option: {xcme_symbol} → {tyu5_symbol}")
            return {
                'type': 'PUT' if is_put else 'CALL',
                'tyu5_symbol': tyu5_symbol,
                'bloomberg_symbol': bloomberg
            }
        
    def _manual_option_translation(self, xcme_symbol: str, is_call: bool, series: str, strike: str) -> Optional[Dict]:
        """Manual fallback for option translation."""
        # Series mapping based on observed patterns
        series_map = {
            'VY': 'VY',   # Monday
            'TJ': 'GY',   # Tuesday (CME)
            'WY': 'WY',   # Wednesday
            'TH': 'HY',   # Thursday (CME)
            'ZN': 'ZN',   # Friday
        }
        
        cme_base = series_map.get(series, series)
        # Extract date info from symbol to determine month/year
        date_match = re.search(r'PS(\d{4})(\d{2})', xcme_symbol)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2)
            # Convert to contract format (this is simplified)
            month_codes = {
                '01': 'F', '02': 'G', '03': 'H', '04': 'J',
                '05': 'K', '06': 'M', '07': 'N', '08': 'Q',
                '09': 'U', '10': 'V', '11': 'X', '12': 'Z'
            }
            month_code = month_codes.get(month, 'X')
            year_digit = year[-1]
            
            # Build TYU5 symbol
            opt_char = 'C' if is_call else 'P'
            tyu5_symbol = f"{cme_base}{month_code}{year_digit} {opt_char} {strike}"
            
            logger.info(f"  Manual translation: {xcme_symbol} → {tyu5_symbol}")
            
            return {
                'type': 'CALL' if is_call else 'PUT',
                'tyu5_symbol': tyu5_symbol,
                'bloomberg_symbol': f"{cme_base}{month_code}{year_digit}{opt_char} {strike} Comdty"
            }
            
        return None
        
    def _extract_cme_base(self, bloomberg_code: str) -> str:
        """Extract CME base from Bloomberg code."""
        # Remove year and option type suffixes
        # VBYN25P2 → VY (simplified logic)
        if len(bloomberg_code) >= 3:
            # Common patterns
            if bloomberg_code.startswith('VBY'):
                return 'VY'
            elif bloomberg_code.startswith('TYW'):
                return 'WY'
            elif bloomberg_code.startswith('TJP'):
                return 'GY'
            elif bloomberg_code.startswith('TJW'):
                return 'HY'
            elif bloomberg_code.startswith('3M'):
                return 'ZN'
                
        # Default: return first 2-3 chars
        return bloomberg_code[:3] if len(bloomberg_code) >= 3 else bloomberg_code
        
    def transform_to_tyu5_format(self, trades_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Transform trade ledger to TYU5 Trades_Input format.
        
        Required TYU5 columns:
        - Date: datetime
        - Time: string
        - Symbol: TYU5 format
        - Action: BUY/SELL
        - Quantity: positive float
        - Price: decimal
        - Type: FUT/CALL/PUT
        - trade_id: string
        """
        logger.info("Transforming trades to TYU5 format")
        
        tyu5_trades = []
        symbol_mappings = {}  # TYU5 → Bloomberg mapping
        
        for idx, row in trades_df.iterrows():
            try:
                # Parse timestamp
                trade_time = pd.to_datetime(row['marketTradeTime'])
                date_str = trade_time.strftime('%Y-%m-%d')
                time_str = trade_time.strftime('%H:%M:%S')
                
                # Parse symbol
                instrument_name = str(row['instrumentName'])
                logger.debug(f"Row {idx}: Parsing {instrument_name}")
                symbol_info = self._parse_xcme_symbol(instrument_name)
                if not symbol_info:
                    logger.error(f"Row {idx}: Failed to parse symbol {instrument_name}, skipping")
                    continue
                    
                # Map action
                action = 'BUY' if str(row['buySell']).upper() == 'B' else 'SELL'
                
                # Ensure positive quantity
                quantity = abs(float(row['quantity']))
                
                # Price is already decimal
                price = float(row['price'])
                
                tyu5_trade = {
                    'Date': trade_time,
                    'Time': time_str,
                    'Symbol': symbol_info['tyu5_symbol'],
                    'Action': action,
                    'Quantity': quantity,
                    'Price': price,
                    'Type': symbol_info['type'],
                    'trade_id': str(row['tradeId']),
                    'Bloomberg_Symbol': symbol_info['bloomberg_symbol']  # For reference
                }
                
                tyu5_trades.append(tyu5_trade)
                
                # Track symbol mapping for price lookups
                symbol_mappings[symbol_info['tyu5_symbol']] = symbol_info['bloomberg_symbol']
                
                logger.debug(f"Row {idx}: {row['instrumentName']} → {symbol_info['tyu5_symbol']} ({symbol_info['type']})")
                
            except Exception as e:
                logger.error(f"Row {idx}: Error processing trade: {e}")
                logger.error(f"  Row data: {row.to_dict()}")
                continue
                
        result_df = pd.DataFrame(tyu5_trades)
        logger.info(f"Successfully transformed {len(result_df)}/{len(trades_df)} trades")
        
        # Log summary
        if len(result_df) > 0:
            logger.info(f"Trade types: {result_df['Type'].value_counts().to_dict()}")
            logger.info(f"Unique symbols: {result_df['Symbol'].nunique()}")
            
        return result_df, symbol_mappings
        
    def get_market_prices_from_db(self, symbols: list, trade_date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch market prices for symbols from market_prices database.
        
        Returns DataFrame with TYU5 expected columns:
        - Symbol: TYU5 format
        - Current_Price: decimal
        - Flash_Close: decimal  
        - Prior_Close: decimal
        """
        from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
        
        # Use existing adapter's market price logic
        adapter = TYU5Adapter()
        return adapter.get_market_prices_for_symbols(symbols, trade_date)
        
    def prepare_tyu5_data(self, trade_ledger_path: Optional[str] = None, 
                         use_market_prices: bool = True) -> Dict[str, pd.DataFrame]:
        """Prepare complete data package for TYU5.
        
        Args:
            trade_ledger_path: Path to trade ledger CSV (None to use latest)
            use_market_prices: Whether to fetch market prices
            
        Returns:
            Dictionary with 'Trades_Input' and 'Market_Prices' DataFrames
        """
        # Read and transform trades
        trades_df = self.read_trade_ledger(trade_ledger_path)
        tyu5_trades, symbol_mappings = self.transform_to_tyu5_format(trades_df)
        
        # Get market prices if requested
        market_prices = pd.DataFrame()
        if use_market_prices and len(tyu5_trades) > 0:
            logger.info(f"Fetching market prices for {len(symbol_mappings)} symbols")
            
            # Use our direct price fetching with Bloomberg symbols
            market_prices = self._fetch_market_prices_direct(symbol_mappings)
            
        return {
            'Trades_Input': tyu5_trades,
            'Market_Prices': market_prices
        }
        
    def prepare_and_run_tyu5(self, trade_ledger_path: Optional[str] = None,
                            save_to_db: bool = True) -> Dict[str, Any]:
        """Prepare data, run TYU5, and save to database
        
        Args:
            trade_ledger_path: Path to trade ledger CSV (None to use latest)
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with TYU5 results including DataFrames and status
        """
        # Prepare data
        data = self.prepare_tyu5_data(trade_ledger_path)
        
        # Track which file was used
        if trade_ledger_path is None:
            trade_ledger_path = self.get_latest_trade_ledger()
        
        # Run TYU5 with capture
        runner = TYU5Runner()
        timestamp = datetime.now()
        output_file = f"data/output/pnl/tyu5_pnl_all_{timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        result = runner.run_with_capture(
            trades_input=data['Trades_Input'],
            market_prices=data['Market_Prices'],
            output_file=output_file
        )
        
        # Save to database if requested and successful
        if save_to_db and result['status'] == 'SUCCESS':
            db = TYU5HistoryDB()
            db.save_run(
                run_timestamp=timestamp,
                trades_df=result['trades_df'],
                positions_df=result['positions_df'],
                trade_ledger_file=os.path.basename(trade_ledger_path),
                excel_file=output_file
            )
        
        return result 

    def parse_xcme_symbol(self, xcme_symbol: str) -> Optional[Dict[str, Any]]:
        """Parse XCME trade ledger format into components.
        
        Examples:
        - XCMEFFDPSX20250919U0ZN -> Future
        - XCMEOPADPS20250718N0ZN3/110.25 -> Option
        
        Returns dict with: type, product, expiry_date, month_code, strike (if option)
        """
        # Future pattern: XCMEFFDPSX + date + month + digit + product
        future_match = re.match(r'XCMEFFDPSX(\d{8})([A-Z])(\d)([A-Z]{2,3})$', xcme_symbol)
        if future_match:
            date_str, month_code, year_digit, product = future_match.groups()
            return {
                'type': 'future',
                'product': product,
                'expiry_date': date_str,
                'month_code': month_code,
                'year_digit': year_digit
            }
        
        # Option pattern: XCMEOPADPS + date + month + digit + series + / + strike
        option_match = re.match(r'XCMEOPADPS(\d{8})([A-Z])(\d)([A-Z]{2,3}\d)/([0-9.]+)$', xcme_symbol)
        if option_match:
            date_str, month_code, year_digit, series, strike = option_match.groups()
            # Series like ZN3, VY3 - extract base and occurrence
            series_match = re.match(r'([A-Z]{2})(\d)$', series)
            if series_match:
                base_product, occurrence = series_match.groups()
            else:
                base_product = series
                occurrence = ''
            
            return {
                'type': 'option',
                'product': base_product,
                'series': series,
                'occurrence': occurrence,
                'expiry_date': date_str,
                'month_code': month_code,
                'year_digit': year_digit,
                'strike': strike
            }
        
        return None 

    def _fetch_market_prices_direct(self, symbol_mappings: Dict[str, str], trade_date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch market prices using Bloomberg symbols directly from database.
        
        Args:
            symbol_mappings: Dict mapping TYU5 symbol → Bloomberg symbol
            trade_date: Optional date for historical prices
            
        Returns:
            DataFrame with columns expected by TYU5
        """
        if not symbol_mappings:
            return pd.DataFrame(columns=['Symbol', 'Current_Price', 'Flash_Close', 'Prior_Close'])
            
        # Connect to market prices database
        db_path = Path("data/output/market_prices/market_prices.db")
        if not db_path.exists():
            logger.warning(f"Market prices database not found: {db_path}")
            return pd.DataFrame(columns=['Symbol', 'Current_Price', 'Flash_Close', 'Prior_Close'])
            
        conn = sqlite3.connect(str(db_path))
        
        # Separate futures and options
        futures_symbols = [bbg for bbg in symbol_mappings.values() if ' Comdty' in bbg and len(bbg.split()) == 2]
        options_symbols = [bbg for bbg in symbol_mappings.values() if len(bbg.split()) == 3]
        
        price_data = {}
        
        # Fetch futures prices
        if futures_symbols:
            placeholders = ','.join(['?'] * len(futures_symbols))
            futures_query = f"""
                SELECT symbol, Current_Price, Flash_Close, prior_close
                FROM futures_prices 
                WHERE symbol IN ({placeholders})
            """
            futures_df = pd.read_sql_query(futures_query, conn, params=futures_symbols)
            for _, row in futures_df.iterrows():
                price_data[row['symbol']] = row
                
        # Fetch options prices
        if options_symbols:
            placeholders = ','.join(['?'] * len(options_symbols))
            options_query = f"""
                SELECT symbol, Current_Price, Flash_Close, prior_close
                FROM options_prices
                WHERE symbol IN ({placeholders})
            """
            options_df = pd.read_sql_query(options_query, conn, params=options_symbols)
            for _, row in options_df.iterrows():
                price_data[row['symbol']] = row
                
        conn.close()
        
        # Build TYU5-compatible DataFrame
        market_prices = []
        for tyu5_symbol, bloomberg_symbol in symbol_mappings.items():
            if bloomberg_symbol in price_data:
                row = price_data[bloomberg_symbol]
                # Use Prior_Close as fallback if Current_Price is NaN
                current = row['Current_Price']
                flash = row['Flash_Close']
                prior = row['prior_close']
                
                # TYU5 needs non-NaN prices
                if pd.isna(current) and not pd.isna(prior):
                    current = prior
                if pd.isna(flash) and not pd.isna(prior):
                    flash = prior
                    
                market_prices.append({
                    'Symbol': tyu5_symbol,
                    'Current_Price': current,
                    'Flash_Close': flash,
                    'Prior_Close': prior
                })
                logger.debug(f"Found price for {tyu5_symbol} via {bloomberg_symbol}")
            else:
                logger.warning(f"No price found for {bloomberg_symbol} (TYU5: {tyu5_symbol})")
                
        return pd.DataFrame(market_prices) 