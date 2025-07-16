"""
MARKET_PRICE_REFACTOR: This file is being replaced with a new market price processing system.
The old code is commented out below for reference during the refactoring process.

This class handled basic time window detection but the new system will have:
- Separate handling for futures vs options
- More strict time window validation (±15 minutes)
- Row-level tracking to prevent reprocessing
- Database storage of historical prices

See lib/trading/market_prices/ for the new implementation.
"""

# """Price file selector that determines which price column to use based on time."""
# 
# import logging
# from datetime import datetime, time
# from pathlib import Path
# 
# logger = logging.getLogger(__name__)
# 
# 
# class PriceFileSelector:
#     """Determines which price column to use based on file timestamp."""
#     
#     # Time windows for price selection
#     PM_2_START = time(13, 45)  # 1:45 PM
#     PM_2_END = time(14, 30)    # 2:30 PM
#     PM_4_START = time(15, 45)  # 3:45 PM
#     PM_4_END = time(16, 30)    # 4:30 PM
#     
#     @staticmethod
#     def determine_price_column(file_path: Path) -> str:
#         """
#         Determine which price column to use based on file timestamp.
#         
#         Args:
#             file_path: Path to the price file
#             
#         Returns:
#             Column name to use: 'PX_LAST' or 'PX_SETTLE'
#         """
#         file_time = PriceFileSelector.extract_time_from_filename(file_path)
#         
#         if not file_time:
#             logger.warning(f"Could not extract time from filename {file_path.name}, defaulting to PX_LAST")
#             return "PX_LAST"
#             
#         # Check if time falls in 2PM window
#         if PriceFileSelector.PM_2_START <= file_time <= PriceFileSelector.PM_2_END:
#             logger.info(f"File {file_path.name} is in 2PM window, using PX_LAST")
#             return "PX_LAST"
#             
#         # Check if time falls in 4PM window
#         elif PriceFileSelector.PM_4_START <= file_time <= PriceFileSelector.PM_4_END:
#             logger.info(f"File {file_path.name} is in 4PM window, using PX_SETTLE")
#             return "PX_SETTLE"
#             
#         else:
#             logger.info(f"File {file_path.name} is outside standard windows, defaulting to PX_LAST")
#             return "PX_LAST"
#             
#     @staticmethod
#     def extract_time_from_filename(file_path: Path) -> time:
#         """
#         Extract time from filename.
#         
#         Expected formats:
#         - Futures_YYYYMMDD_HHMM.csv
#         - Options_YYYYMMDD_HHMM.csv
#         
#         Args:
#             file_path: Path to the file
#             
#         Returns:
#             Extracted time object or None if parsing fails
#         """
#         try:
#             # Remove extension and split by underscore
#             parts = file_path.stem.split('_')
#             
#             # Look for HHMM pattern
#             if len(parts) >= 3:
#                 time_str = parts[-1]  # Last part should be HHMM
#                 
#                 # Validate it's 4 digits
#                 if len(time_str) == 4 and time_str.isdigit():
#                     hour = int(time_str[:2])
#                     minute = int(time_str[2:])
#                     
#                     # Validate hour and minute ranges
#                     if 0 <= hour <= 23 and 0 <= minute <= 59:
#                         return time(hour, minute)
#                         
#         except Exception as e:
#             logger.debug(f"Error extracting time from {file_path.name}: {e}")
#             
#         return None
#         
#     @staticmethod
#     def is_in_price_window(file_path: Path) -> bool:
#         """
#         Check if file is in either the 2PM or 4PM window.
#         
#         Args:
#             file_path: Path to check
#             
#         Returns:
#             True if file is in a valid price window
#         """
#         file_time = PriceFileSelector.extract_time_from_filename(file_path)
#         
#         if not file_time:
#             return False
#             
#         # Check both windows
#         in_2pm_window = PriceFileSelector.PM_2_START <= file_time <= PriceFileSelector.PM_2_END
#         in_4pm_window = PriceFileSelector.PM_4_START <= file_time <= PriceFileSelector.PM_4_END
#         
#         return in_2pm_window or in_4pm_window 