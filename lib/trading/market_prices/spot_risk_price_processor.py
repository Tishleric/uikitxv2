"""(DEPRECATED) Spot Risk Price Processor

This module is now deprecated and replaced by a more robust, decoupled architecture
using a Redis pub/sub channel.

- The SpotRiskWatcher (`run_spot_risk_watcher.py`) now acts as the "Producer",
  publishing completed data batches to the `spot_risk:results_channel`.
- The new PriceUpdaterService (`run_price_updater_service.py`) acts as a "Consumer",
  subscribing to the channel and updating the pricing table in trades.db.

This file is kept for historical reference but should not be used.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

from lib.monitoring.decorators import monitor
from .rosetta_stone import RosettaStone
from .storage import MarketPriceStorage

logger = logging.getLogger(__name__)


class SpotRiskPriceProcessor:
    """Processes spot risk files to extract current prices."""
    
    def __init__(self, storage: MarketPriceStorage):
        """
        Initialize processor with storage instance.
        
        Args:
            storage: MarketPriceStorage instance for database operations
        """
        self.storage = storage
        self.symbol_translator = RosettaStone()
        
    @monitor()
    def process_file(self, file_path: Path) -> bool:
        """
        Process a spot risk CSV file and update current prices.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            True if successfully processed, False otherwise
        """
        try:
            logger.info(f"Processing spot risk file: {file_path.name}")
            
            # Extract timestamp from filename
            file_timestamp = self._extract_timestamp_from_filename(file_path.name)
            if not file_timestamp:
                logger.warning(f"Could not extract timestamp from filename: {file_path.name}")
                return False
                
            # Read CSV file - first row has column names, second row has types
            df = pd.read_csv(file_path)
            # Skip the type row (row index 0 after header)
            df = df.iloc[1:].reset_index(drop=True)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
            
            # Extract prices
            prices = self._extract_prices(df)
            logger.info(f"Extracted {len(prices)} valid prices")
            
            # Update database
            if prices:
                success = self._update_database(prices, file_timestamp)
                if success:
                    logger.info(f"Successfully updated {len(prices)} prices in database")
                    return True
                else:
                    logger.error("Failed to update database")
                    return False
            else:
                logger.warning("No valid prices found in file")
                return True  # Not an error, just no data
                
        except Exception as e:
            logger.error(f"Error processing spot risk file {file_path}: {e}")
            return False
            
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract timestamp from filename format: bav_analysis_YYYYMMDD_HHMMSS.csv
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            datetime object or None if cannot parse
        """
        try:
            pattern = r'bav_analysis_(\d{8})_(\d{6})\.csv'
            match = re.search(pattern, filename)
            
            if not match:
                return None
                
            date_str = match.group(1)  # YYYYMMDD
            time_str = match.group(2)  # HHMMSS
            
            # Parse datetime
            dt = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
            return dt
            
        except Exception as e:
            logger.error(f"Error parsing timestamp from {filename}: {e}")
            return None
            
    def _extract_prices(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract prices from dataframe using ADJTHEOR or BID/ASK midpoint.
        
        Args:
            df: Spot risk dataframe
            
        Returns:
            Dictionary mapping Bloomberg symbols to prices
        """
        prices = {}
        
        # Normalize column names to handle case variations
        df.columns = df.columns.str.upper()
        
        for _, row in df.iterrows():
            try:
                # Get spot risk symbol from Key column
                spot_risk_symbol = row.get('KEY', '')
                if not spot_risk_symbol or pd.isna(spot_risk_symbol):
                    continue
                    
                # Skip if it's the underlying future row or invalid
                if spot_risk_symbol == 'XCME.ZN' or 'INVALID' in str(spot_risk_symbol):
                    continue
                    
                # Check if it's a future or option
                itype = row.get('ITYPE', '')
                
                # Handle futures differently
                if itype == 'F':
                    # Futures format: XCME.ZN.SEP25 -> TYU5 Comdty
                    bloomberg_symbol = self._translate_future(spot_risk_symbol)
                    if not bloomberg_symbol:
                        logger.info(f"Untranslatable future: {spot_risk_symbol}")
                        continue
                else:
                    # Options: use centralized translator
                    bloomberg_symbol = self.symbol_translator.translate(
                        spot_risk_symbol, 
                        'actantrisk', 
                        'bloomberg'
                    )
                    if not bloomberg_symbol:
                        logger.info(f"Untranslatable symbol (likely historical): {spot_risk_symbol}")
                        continue
                    
                # Extract price - prefer ADJTHEOR
                price = None
                adjtheor = row.get('ADJTHEOR')
                
                if pd.notna(adjtheor) and adjtheor != 'INVALID':
                    try:
                        price = float(adjtheor)
                    except (ValueError, TypeError):
                        pass
                        
                # Fallback to BID/ASK midpoint
                if price is None:
                    bid = row.get('BID')
                    ask = row.get('ASK')
                    
                    if pd.notna(bid) and pd.notna(ask) and bid != 'INVALID' and ask != 'INVALID':
                        try:
                            bid_val = float(bid)
                            ask_val = float(ask)
                            price = (bid_val + ask_val) / 2.0
                        except (ValueError, TypeError):
                            pass
                            
                # Store if we got a valid price
                if price is not None and price > 0:
                    prices[bloomberg_symbol] = price
                    
            except Exception as e:
                logger.debug(f"Error processing row: {e}")
                continue
                
        return prices
        
    def _translate_future(self, xcme_symbol: str) -> Optional[str]:
        """
        Translate XCME future symbol to Bloomberg format.
        
        Args:
            xcme_symbol: XCME format future symbol (e.g., "XCME.ZN.SEP25")
            
        Returns:
            Bloomberg format symbol (e.g., "TYU5 Comdty") or None if invalid
        """
        try:
            # Parse XCME future format: XCME.ZN.SEP25
            parts = xcme_symbol.split('.')
            if len(parts) != 3 or parts[0] != 'XCME':
                return None
                
            product = parts[1]
            expiry = parts[2]
            
            # Map product codes
            product_map = {
                'ZN': 'TY',  # 10-year Treasury Note
                'ZF': 'FV',  # 5-year Treasury Note
                'ZT': 'TU',  # 2-year Treasury Note
                'ZB': 'US',  # 30-year Treasury Bond
            }
            
            bb_product = product_map.get(product)
            if not bb_product:
                return None
                
            # Parse expiry: SEP25 -> U5
            if len(expiry) < 5:
                return None
                
            month_str = expiry[:3]
            year_str = expiry[-1]  # Bloomberg uses single digit year
            
            # Month mapping
            month_map = {
                'JAN': 'F', 'FEB': 'G', 'MAR': 'H', 'APR': 'J',
                'MAY': 'K', 'JUN': 'M', 'JUL': 'N', 'AUG': 'Q',
                'SEP': 'U', 'OCT': 'V', 'NOV': 'X', 'DEC': 'Z'
            }
            
            month_code = month_map.get(month_str)
            if not month_code:
                return None
                
            # Construct Bloomberg symbol
            bloomberg_symbol = f"{bb_product}{month_code}{year_str} Comdty"
            return bloomberg_symbol
            
        except Exception as e:
            logger.debug(f"Error translating future {xcme_symbol}: {e}")
            return None
        
    @monitor()
    def _update_database(self, prices: Dict[str, float], file_timestamp: datetime) -> bool:
        """
        Update Current_Price in database for given symbols.
        
        Args:
            prices: Dictionary mapping Bloomberg symbols to prices
            file_timestamp: Timestamp from the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use file date as trade date
            trade_date = file_timestamp.date()
            
            # Separate futures and options
            futures_updates = []
            options_updates = []
            
            for symbol, price in prices.items():
                # Keep 'Comdty' suffix for consistent storage
                # Symbol already includes 'Comdty' from translator
                
                # Determine if it's an option or future
                # Options have strike price in the symbol (space before strike)
                # e.g., "VBYN25C3 111.750 Comdty" vs "TYU5 Comdty"
                if symbol.count(' ') >= 2:  # Options have at least 2 spaces
                    options_updates.append({
                        'trade_date': trade_date,
                        'symbol': symbol,
                        'Current_Price': price,
                        'expire_dt': None,  # Let translator handle this in future
                        'last_updated': file_timestamp
                    })
                else:
                    # Futures (only one space before Comdty)
                    futures_updates.append({
                        'trade_date': trade_date,
                        'symbol': symbol,
                        'Current_Price': price,
                        'last_updated': file_timestamp
                    })
            
            # Update database
            success = True
            
            if futures_updates:
                success = success and self.storage.update_current_prices_futures(futures_updates)
                logger.info(f"Updated {len(futures_updates)} futures prices")
                
            if options_updates:
                success = success and self.storage.update_current_prices_options(options_updates)
                logger.info(f"Updated {len(options_updates)} options prices")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            return False 