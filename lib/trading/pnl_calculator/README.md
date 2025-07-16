# P&L Calculator - CTO Integration

This module provides P&L tracking functionality with preparation for CTO's calculation engine integration.

## Current Status: Pass 3 Complete ✅

### Completed Passes:
1. **Pass 1**: Isolated calculations (all methods return mock data with "CTO_INTEGRATION" comments)
2. **Pass 2**: Enhanced data persistence with row-level trade tracking
3. **Pass 3**: New storage schema and enhanced logging

### Pass 3 Implementation Details:

#### New CTO Table Schema
Added `cto_trades` table matching CTO's exact requirements:
```sql
CREATE TABLE cto_trades (
    Date DATE,              -- Trade date
    Time TIME,              -- Trade time  
    Symbol TEXT,            -- Bloomberg symbol
    Action TEXT,            -- 'BUY' or 'SELL'
    Quantity INTEGER,       -- Negative for sells
    Price REAL,             -- Decimal price
    Fees REAL,              -- Trading fees
    Counterparty TEXT,      -- Always 'FRGM'
    tradeID TEXT,           -- Unique trade ID
    Type TEXT,              -- 'FUT' or 'OPT'
    source_file TEXT,       -- Source CSV filename
    is_sod INTEGER,         -- 1 if SOD trade
    is_exercise INTEGER     -- 1 if exercise/assignment
)
```

#### Enhanced Logging
- File processing start/end with detailed stats
- Edge case detection warnings (SOD, exercise)
- Row-by-row processing progress
- Summary statistics after completion

### Next Steps: Market Price Processing

## Market Price Processing System Design

### Overview
Process market price data arriving 3 times daily (2pm, 3pm, 4pm CDT) but only use 2pm and 4pm files. The system will follow the same architectural patterns as the trade ledger processor.

### Data Flow Timeline
**Daily Timeline Example (July 12, 2025):**
- 8:00 AM: Database has row for July 12 with only `prior_close` (from July 11's 4pm file)
- 2:00 PM: July 12 file arrives → UPDATE July 12 row with `current_price` from PX_LAST
- 3:00 PM: File arrives → IGNORE
- 4:00 PM: July 12 file arrives → INSERT new row for July 13 with `prior_close` from PX_SETTLE

### Database Schema

#### Futures Prices Table
```sql
CREATE TABLE futures_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,           -- The trading day this price is for
    symbol TEXT NOT NULL,               -- Bloomberg symbol (with U5 suffix)
    current_price REAL,                 -- From 2pm PX_LAST
    prior_close REAL,                   -- From previous day's 4pm PX_SETTLE
    last_updated TIMESTAMP,             -- When this row was last updated
    UNIQUE(trade_date, symbol)
);
```

#### Options Prices Table
```sql
CREATE TABLE options_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,           -- The trading day this price is for
    symbol TEXT NOT NULL,               -- Bloomberg symbol (already correct)
    current_price REAL,                 -- From 2pm PX_LAST
    prior_close REAL,                   -- From previous day's 4pm PX_SETTLE
    expire_dt DATE,                     -- Expiration date
    moneyness REAL,                     -- Moneyness value
    last_updated TIMESTAMP,             -- When this row was last updated
    UNIQUE(trade_date, symbol)
);
```

#### File Processing Tracker
```sql
CREATE TABLE price_file_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,          -- Filename
    file_type TEXT NOT NULL,            -- 'futures' or 'options'
    file_timestamp TIMESTAMP NOT NULL,   -- Timestamp from filename
    window_type TEXT NOT NULL,          -- '2pm' or '4pm'
    total_rows INTEGER NOT NULL,
    processed_rows INTEGER NOT NULL,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    UNIQUE(source_file)
);
```

### Processing Logic

#### For 2pm Files (PX_LAST → current_price):
1. Parse filename, verify it's in 2pm window (13:45-14:30)
2. Extract date from filename
3. For each row in CSV:
   - Futures: Add U5 suffix to symbol
   - UPDATE the row for that trade_date with current_price

#### For 4pm Files (PX_SETTLE → prior_close for next day):
1. Parse filename, verify it's in 4pm window (15:45-16:30)
2. Extract date from filename
3. Calculate next_trade_date = date + 1 day
4. For each row in CSV:
   - Futures: Add U5 suffix to symbol
   - INSERT new row for next_trade_date with prior_close

#### 3pm Files: Detect and skip entirely

### Implementation Plan

#### Phase 1: Core Infrastructure
1. Create market_prices package structure
2. Implement storage.py with schema and basic operations
3. Add constants.py with time windows and configuration

#### Phase 2: Processors
1. Implement FuturesProcessor with:
   - Time window validation
   - U5 suffix handling
   - Row-level update logic
2. Implement OptionsProcessor with:
   - Same time window logic
   - Extra fields (expire_dt, moneyness)

#### Phase 3: File Monitoring
1. Create FileMonitor using existing patterns
2. Add row-level tracking to prevent reprocessing
3. Handle the daily 2pm→4pm progression

#### Phase 4: Integration & Testing
1. Create test scripts
2. Add comprehensive logging
3. Integrate with existing UI if needed

### Key Design Decisions
1. **Separate Tables:** Futures and options have different schemas
2. **Row-Level Tracking:** Use price_file_tracker table to prevent reprocessing
3. **Trade Date Logic:** Each row represents a trading day
4. **Bloomberg Symbols:** Apply U5 suffix only to futures
5. **Time Window Strictness:** Only process files within ±15 minutes of 2pm/4pm 