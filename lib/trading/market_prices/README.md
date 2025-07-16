# Market Prices Processing System

This module provides automated processing for futures and options market price files arriving at specific time windows throughout the trading day.

## Overview

The system monitors directories for new CSV files containing market prices and processes them according to specific time windows:
- **2:00 PM CDT (±15 minutes)**: Updates current prices using PX_LAST values
- **4:00 PM CDT (±15 minutes)**: Inserts next day's prior close using PX_SETTLE values
- **3:00 PM files**: Ignored (not within either processing window)

## Architecture

```
lib/trading/market_prices/
├── __init__.py              # Package exports
├── constants.py             # Configuration and time windows
├── storage.py               # Database operations and schema
├── futures_processor.py     # Futures-specific processing logic
├── options_processor.py     # Options-specific processing logic
└── file_monitor.py          # File system monitoring
```

## Key Features

### 1. Time Window Validation
- Files are only processed if their timestamp falls within defined windows
- 2:00 PM window: 1:45 PM - 2:30 PM CDT
- 4:00 PM window: 3:45 PM - 4:30 PM CDT

### 2. Bloomberg Symbol Handling
- Futures: Automatically adds "U5" suffix (e.g., TU → TUU5)
- Options: Preserves existing Bloomberg format

### 3. Row-Level Tracking
- Prevents reprocessing of files
- Tracks each row processed to handle partial failures
- Maintains processing history in `price_file_tracker` table

### 4. Database Design
- **futures_prices**: Stores futures prices with trade_date, symbol, current_price, prior_close
- **options_prices**: Extends futures with expire_dt and moneyness fields
- Builds historical price database over time

## Usage

### Manual Processing
```python
from lib.trading.market_prices import MarketPriceStorage, FuturesProcessor

# Initialize
storage = MarketPriceStorage()
processor = FuturesProcessor(storage)

# Process a file
result = processor.process_file(Path("data/input/market_prices/futures/Futures_20250715_1400.csv"))
```

### Automated Monitoring
```bash
python scripts/run_market_price_monitor.py
```

This will:
1. Monitor `data/input/market_prices/futures/` and `data/input/market_prices/options/`
2. Process existing files on startup
3. Watch for new files and process them automatically
4. Log all processing activity

## File Format Requirements

### Futures Files
- Filename: `Futures_YYYYMMDD_HHMM.csv`
- Required columns: SYMBOL, PX_LAST, PX_SETTLE
- Symbols will have "U5" suffix added automatically

### Options Files
- Filename: `Options_YYYYMMDD_HHMM.csv`
- Required columns: SYMBOL, PX_LAST, PX_SETTLE, EXPIRE_DT, MONEYNESS
- Symbols should already be in Bloomberg format

## Database Schema

### futures_prices
```sql
CREATE TABLE futures_prices (
    id INTEGER PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    current_price REAL,
    prior_close REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, symbol)
);
```

### options_prices
```sql
CREATE TABLE options_prices (
    id INTEGER PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    current_price REAL,
    prior_close REAL,
    expire_dt DATE,
    moneyness TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, symbol)
);
```

## Processing Logic

### 2:00 PM Files
1. Validate timestamp is within 2pm window
2. Read PX_LAST column values
3. For futures: add U5 suffix to symbols
4. UPDATE existing rows for today's date with current_price
5. INSERT new rows if they don't exist

### 4:00 PM Files
1. Validate timestamp is within 4pm window
2. Read PX_SETTLE column values
3. For futures: add U5 suffix to symbols
4. INSERT rows for tomorrow's date with prior_close values
5. Existing rows for tomorrow are updated if present

## Error Handling

- Invalid file formats are logged and skipped
- Files outside time windows are ignored with warning
- Database errors are logged but don't crash the monitor
- Row-level tracking ensures partial failures can be resumed

## Configuration

Key settings in `constants.py`:
- `CHICAGO_TZ`: All times are in Chicago timezone
- `TIME_WINDOWS`: Defines processing windows and actions
- `FILE_PATTERNS`: Regex patterns for valid filenames
- `FUTURES_SUFFIX`: "U5" suffix for futures symbols

## Monitoring & Logging

The system provides detailed logging:
- File processing start/completion
- Row counts and processing statistics
- Time window validation results
- Database operations
- Error conditions

All operations are wrapped with the `@monitor` decorator for performance tracking. 