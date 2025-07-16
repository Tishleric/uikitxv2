"""
Constants and configuration for market price processing.
"""

from datetime import time
import pytz

# Chicago timezone for all time operations
CHICAGO_TZ = pytz.timezone('America/Chicago')

# Time windows for price file processing
TIME_WINDOWS = {
    '2pm': {
        'start': time(13, 45),      # 1:45 PM CDT
        'end': time(14, 30),        # 2:30 PM CDT
        'target': time(14, 0),      # 2:00 PM CDT
        'column': 'PX_LAST',        # Use last price for current price
        'action': 'update_current'   # Update current_price column
    },
    '4pm': {
        'start': time(15, 45),      # 3:45 PM CDT
        'end': time(16, 30),        # 4:30 PM CDT
        'target': time(16, 0),      # 4:00 PM CDT
        'column': 'PX_SETTLE',      # Use settlement price for prior close
        'action': 'insert_next_day'  # Insert prior_close for next trading day
    },
    '3pm': {
        'start': time(14, 45),      # 2:45 PM CDT
        'end': time(15, 30),        # 3:30 PM CDT
        'target': time(15, 0),      # 3:00 PM CDT
        'column': None,             # Don't use this window
        'action': 'skip'            # Skip these files
    }
}

# Bloomberg symbol suffix for futures
FUTURES_SUFFIX = 'U5'

# File name patterns
FILE_PATTERNS = {
    'futures': r'Futures_(\d{8})_(\d{4})\.csv',
    'options': r'Options_(\d{8})_(\d{4})\.csv'
}

# Database configuration
DB_FILE_NAME = 'market_prices.db'

# Data root directory
import os
from pathlib import Path
DATA_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' 