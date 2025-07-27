"""Market Prices Constants - ACTIVE VERSION"""

from pathlib import Path
from datetime import time
import pytz

# ACTIVE: Updated to watch Z:\Trade_Control directory
MARKET_PRICES_DIR = Path(r"Z:\Trade_Control")
FUTURES_SUBDIR = "futures"
OPTIONS_SUBDIR = "options"

# Chicago timezone for all time operations
CHICAGO_TZ = pytz.timezone('America/Chicago')

# Time windows for market price validity
TIME_WINDOWS = {
    "2pm": {
        "start": time(13, 45),      # 1:45 PM CDT
        "end": time(14, 30),        # 2:30 PM CDT
        "target": time(14, 0),      # 2:00 PM CDT
        "column": "PX_LAST",        # Use last price for Flash_Close
        "futures_column": "PX_LAST_DEC",  # Futures use decimal column
        "action": "update_flash"    # Update Flash_Close column
    },
    "4pm": {
        "start": time(15, 45),      # 3:45 PM CDT
        "end": time(16, 30),        # 4:30 PM CDT
        "target": time(16, 0),      # 4:00 PM CDT
        "column": "PX_SETTLE",      # Use settlement price for prior close
        "futures_column": "PX_SETTLE_DEC",  # Futures use decimal column
        "action": "insert_next_day" # Insert prior_close for next trading day
    }
}

# Bloomberg symbol suffix for futures
FUTURES_SUFFIX = 'U5'

# File name patterns
FILE_PATTERNS = {
    'futures': r'Futures_(\d{8})_(\d{4})\.csv',
    'options': r'Options_(\d{8})_(\d{4})\.csv'
}

# Default file sizes
DEFAULT_FILE_SIZE_MB = 0.0

# Database configuration
# DB_FILE_NAME = 'market_prices.db'  # REMOVED: market_prices.db deprecated in favor of new pricing infrastructure

# Data root directory
import os
DATA_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))