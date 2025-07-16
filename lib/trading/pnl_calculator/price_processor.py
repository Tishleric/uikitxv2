"""
MARKET_PRICE_REFACTOR: This file is being replaced with a new market price processing system.
The old code is commented out below for reference during the refactoring process.

New system will:
- Process futures and options price files separately
- Handle 2pm (current price) and 4pm (prior close) windows
- Use row-level tracking to prevent reprocessing
- Add U5 suffix to futures symbols
- Build historical price database over time

See lib/trading/market_prices/ for the new implementation.
"""

# """Price file processor for extracting and storing market prices."""
# 
# import logging
# import pandas as pd
# from pathlib import Path
# from datetime import datetime
# from typing import Dict, Optional, List
# import pytz
# 
# from .storage import PnLStorage
# 
# logger = logging.getLogger(__name__)
# 
# 
# class PriceProcessor:
#     """Processes price files and stores market prices."""
#     
#     def __init__(self, storage: PnLStorage):
#         """
#         Initialize the price processor.
#         
#         Args:
#             storage: PnLStorage instance for persisting prices
#         """
#         self.storage = storage
#         self.chicago_tz = pytz.timezone('America/Chicago')
#         
#     def process_price_file(self, file_path: Path) -> Dict[str, float]:
#         """
#         Process a single price file and extract prices.
#         
#         Args:
#             file_path: Path to the price CSV file
#             
#         Returns:
#             Dictionary mapping symbol to price
#         """
#         # Ensure file_path is a Path object
#         if not isinstance(file_path, Path):
#             file_path = Path(file_path)
#             
#         logger.info(f"Processing price file: {file_path}")
#         
#         try:
#             # Read CSV file
#             df = pd.read_csv(file_path)
#             
#             # Determine which column to use based on time
#             column_to_use = self._determine_price_column(file_path)
#             
#             # Extract prices
#             prices = self._extract_prices(df, column_to_use)
#             
#             # Store prices in database
#             self._store_prices(prices, file_path, column_to_use)
#             
#             logger.info(f"Processed {len(prices)} prices from {file_path.name}")
#             return prices
#             
#         except Exception as e:
#             logger.error(f"Error processing price file {file_path}: {e}")
#             raise
#     
#     def _determine_price_column(self, file_path: Path) -> str:
#         """Determine which price column to use based on file timestamp."""
#         # Extract time from filename
#         try:
#             # Expected format: market_prices_YYYYMMDD_HHMM.csv
#             parts = file_path.stem.split('_')
#             if len(parts) >= 4:
#                 time_str = parts[3]  # HHMM
#                 hour = int(time_str[:2])
#                 minute = int(time_str[2:4])
#                 
#                 # Create time object
#                 file_time = datetime.strptime(f"{hour:02d}{minute:02d}", "%H%M").time()
#                 
#                 # 2pm window (1:45-2:30) uses PX_LAST
#                 if datetime.strptime("1345", "%H%M").time() <= file_time <= datetime.strptime("1430", "%H%M").time():
#                     return "PX_LAST"
#                 # 4pm window (3:45-4:30) uses PX_SETTLE
#                 elif datetime.strptime("1545", "%H%M").time() <= file_time <= datetime.strptime("1630", "%H%M").time():
#                     return "PX_SETTLE"
#                 else:
#                     # Default to PX_LAST for other times
#                     return "PX_LAST"
#                     
#         except (ValueError, IndexError) as e:
#             logger.warning(f"Could not determine time from filename, defaulting to PX_LAST: {e}")
#         
#         # Default return if parsing fails
#         return "PX_LAST"
#     
#     def _extract_prices(self, df: pd.DataFrame, column: str) -> Dict[str, float]:
#         """
#         Extract prices from DataFrame.
#         
#         Args:
#             df: Price data DataFrame
#             column: Column name to extract (PX_LAST or PX_SETTLE)
#             
#         Returns:
#             Dictionary mapping symbol to price
#         """
#         prices = {}
#         
#         # Check if required columns exist
#         if 'Ticker' not in df.columns:
#             logger.error("No 'Ticker' column found in price file")
#             return prices
#             
#         if column not in df.columns:
#             logger.error(f"Column '{column}' not found in price file")
#             return prices
#         
#         # Process each row
#         for _, row in df.iterrows():
#             ticker_value = row.get('Ticker')
#             if ticker_value is None:
#                 continue
#             ticker = str(ticker_value).strip()
#             
#             price_value = row.get(column)
#             
#             if not ticker:
#                 continue
#                 
#             # Skip if price is not numeric
#             try:
#                 if price_value is None:
#                     continue
#                 price = float(price_value)
#                 if pd.isna(price):
#                     continue
#                 prices[ticker] = price
#             except (ValueError, TypeError):
#                 logger.debug(f"Skipping non-numeric price for {ticker}: {price_value}")
#                 continue
#         
#         return prices
#     
#     def _store_prices(self, prices: Dict[str, float], file_path: Path, column_used: str):
#         """
#         Store prices in the database.
#         
#         Args:
#             prices: Dictionary mapping symbol to price
#             file_path: Source file path
#             column_used: Which column was used (PX_LAST or PX_SETTLE)
#         """
#         if not prices:
#             logger.warning("No prices to store")
#             return
#             
#         # Get file timestamp
#         file_timestamp = self._get_file_timestamp(file_path)
#         
#         # Store each price
#         conn = self.storage._get_connection()
#         cursor = conn.cursor()
#         
#         try:
#             # Create prices table if it doesn't exist
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS price_snapshots (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     symbol TEXT NOT NULL,
#                     price REAL NOT NULL,
#                     price_type TEXT NOT NULL,
#                     file_timestamp TIMESTAMP NOT NULL,
#                     file_name TEXT NOT NULL,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     UNIQUE(symbol, file_timestamp)
#                 )
#             """)
#             
#             # Insert or update prices
#             for symbol, price in prices.items():
#                 cursor.execute("""
#                     INSERT OR REPLACE INTO price_snapshots 
#                     (symbol, price, price_type, file_timestamp, file_name)
#                     VALUES (?, ?, ?, ?, ?)
#                 """, (symbol, price, column_used, file_timestamp, file_path.name))
#             
#             conn.commit()
#             logger.info(f"Stored {len(prices)} prices from {file_path.name}")
#             
#         except Exception as e:
#             conn.rollback()
#             logger.error(f"Error storing prices: {e}")
#             raise
#         finally:
#             cursor.close()
#     
#     def _get_file_timestamp(self, file_path: Path) -> datetime:
#         """Extract timestamp from filename and localize to Chicago time."""
#         try:
#             # Expected format: market_prices_YYYYMMDD_HHMM.csv
#             parts = file_path.stem.split('_')
#             if len(parts) >= 4:
#                 date_str = parts[2]  # YYYYMMDD
#                 time_str = parts[3]  # HHMM
#                 
#                 # Parse datetime
#                 dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
#                 
#                 # Localize to Chicago time
#                 return self.chicago_tz.localize(dt)
#         except Exception as e:
#             logger.warning(f"Could not parse timestamp from {file_path.name}, using current time: {e}")
#         
#         # Return current time as fallback
#         return datetime.now(self.chicago_tz)
#     
#     def get_latest_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, float]:
#         """
#         Get the latest prices for specified symbols.
#         
#         Args:
#             symbols: List of symbols to get prices for (None for all)
#             
#         Returns:
#             Dictionary mapping symbol to latest price
#         """
#         conn = self.storage._get_connection()
#         cursor = conn.cursor()
#         
#         try:
#             # Build query
#             if symbols:
#                 placeholders = ','.join(['?' for _ in symbols])
#                 query = f"""
#                     SELECT DISTINCT symbol, price, file_timestamp
#                     FROM price_snapshots
#                     WHERE symbol IN ({placeholders})
#                     AND (symbol, file_timestamp) IN (
#                         SELECT symbol, MAX(file_timestamp)
#                         FROM price_snapshots
#                         WHERE symbol IN ({placeholders})
#                         GROUP BY symbol
#                     )
#                 """
#                 params = symbols + symbols
#             else:
#                 query = """
#                     SELECT DISTINCT symbol, price, file_timestamp
#                     FROM price_snapshots
#                     WHERE (symbol, file_timestamp) IN (
#                         SELECT symbol, MAX(file_timestamp)
#                         FROM price_snapshots
#                         GROUP BY symbol
#                     )
#                 """
#                 params = []
#             
#             cursor.execute(query, params)
#             
#             prices = {}
#             for row in cursor.fetchall():
#                 symbol, price, _ = row
#                 prices[symbol] = price
#                 
#             return prices
#             
#         finally:
#             cursor.close()
#     
#     def get_price_at_time(self, symbol: str, target_time: datetime) -> Optional[float]:
#         """
#         Get price for a symbol at or before a specific time.
#         
#         Args:
#             symbol: Symbol to get price for
#             target_time: Target timestamp
#             
#         Returns:
#             Price if found, None otherwise
#         """
#         conn = self.storage._get_connection()
#         cursor = conn.cursor()
#         
#         try:
#             # Find the most recent price at or before target time
#             cursor.execute("""
#                 SELECT price
#                 FROM price_snapshots
#                 WHERE symbol = ? AND file_timestamp <= ?
#                 ORDER BY file_timestamp DESC
#                 LIMIT 1
#             """, (symbol, target_time))
#             
#             result = cursor.fetchone()
#             return result[0] if result else None
#             
#         finally:
#             cursor.close() 