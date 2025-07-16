# Trade Processing System Design

## Overview
A high-performance, resilient trade processing system that ensures each trade is processed exactly once with minimal latency, transforming trade data into the CTO's required format.

## Core Principles
1. **Persistence** - Process once and only once, survive restarts
2. **Latency** - Near real-time processing of new trades
3. **Adjustment** - Transform to CTO's required schema with proper edge case handling

## System Architecture

### 1. Trade Detection Layer

**File Watcher Component**
- Monitor `data/input/trade_ledger/` directory continuously
- Detect new CSV files matching pattern `trades_YYYYMMDD.csv`
- Detect modifications to existing CSV files using:
  - File size changes
  - Last modified timestamp
  - File hash for definitive change detection

**Change Detection Strategy**
- Store file metadata: `(filename, size, last_modified, hash, last_processed_row)`
- For new files: Process all rows
- For existing files: Process only rows after `last_processed_row`
- Never reprocess rows already in database

### 2. Trade Processing Pipeline

#### Stage 1: Raw Trade Ingestion
```
Input: CSV row from trade_ledger
Output: Validated trade record with flags

Process:
1. Parse CSV row with columns: tradeId, instrumentName, marketTradeTime, buySell, quantity, price
2. Validate all required fields are present and non-null
3. Parse marketTradeTime to datetime object
4. Flag special cases:
   - SOD trades: timestamp has 00:00:00.000 (exact to millisecond)
   - Exercised options: price == 0.0
5. Create raw trade record with flags
```

#### Stage 2: Trade Transformation
```
Input: Validated trade record
Output: CTO-formatted trade record

Process:
1. Symbol translation (Actant → Bloomberg)
   - Parse Actant symbol format
   - Lookup Bloomberg equivalent
   - Cache translation for performance
2. Extract instrument type:
   - Options: Contains 'OCAD' or 'OPAD' 
   - Futures: Contains 'FFDPS'
3. Adjust quantity:
   - If buySell == 'S': quantity = -abs(quantity)
   - If buySell == 'B': quantity = abs(quantity)
4. Set fixed values:
   - Counterparty = 'FRGM'
   - Fees = 0.0
5. Map tradeId to trade_id field
```

#### Stage 3: Trade Storage
```
Input: CTO-formatted trade record
Output: Persisted trade in SQLite

Process:
1. Begin database transaction
2. Check if trade_id already exists (idempotency)
3. If new: Insert into appropriate table
   - Normal trades → trades table
   - Flagged trades → flagged_trades table
4. Update processing_metadata with new row count
5. Commit transaction
```

### 3. Database Schema

```sql
-- Main trades table (CTO format)
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,                    -- Extracted from marketTradeTime
    time TIME NOT NULL,                    -- Extracted from marketTradeTime
    symbol TEXT NOT NULL,                  -- Bloomberg symbol (translated)
    action TEXT NOT NULL,                  -- 'BUY' or 'SELL' (from buySell)
    quantity INTEGER NOT NULL,             -- Negative for sells
    price DECIMAL(10,6) NOT NULL,          -- From price column
    fees DECIMAL(10,2) DEFAULT 0.0,        -- Always 0 for now
    counterparty TEXT DEFAULT 'FRGM',      -- Always 'FRGM'
    trade_id TEXT UNIQUE NOT NULL,         -- Original tradeId from CSV
    type TEXT NOT NULL,                    -- 'FUT' or 'OPT'
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_date (date),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_id (trade_id)
);

-- Flagged trades table (SOD and exercised options)
CREATE TABLE flagged_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT UNIQUE NOT NULL,
    flag_type TEXT NOT NULL,              -- 'SOD' or 'EXERCISED'
    original_data TEXT NOT NULL,          -- JSON of original CSV row
    reason TEXT NOT NULL,                 -- Human-readable reason
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Original fields for reference
    instrument_name TEXT NOT NULL,
    market_trade_time TIMESTAMP NOT NULL,
    buy_sell TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,6) NOT NULL
);

-- Processing metadata for recovery and monitoring
CREATE TABLE processing_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    last_processed_row INTEGER NOT NULL DEFAULT 0,
    total_rows_in_file INTEGER,
    last_processed_at TIMESTAMP NOT NULL,
    processing_started_at TIMESTAMP,
    
    UNIQUE(filename)
);

-- Symbol mapping cache for performance
CREATE TABLE symbol_mapping (
    actant_symbol TEXT PRIMARY KEY,
    bloomberg_symbol TEXT NOT NULL,
    instrument_type TEXT NOT NULL CHECK(instrument_type IN ('FUT', 'OPT')),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing errors for monitoring
CREATE TABLE processing_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    raw_data TEXT NOT NULL,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Edge Case Detection

#### SOD (Start of Day) Trades
**Detection Logic:**
```python
def is_sod_trade(timestamp: datetime) -> bool:
    """
    SOD trades have EXACT midnight timestamp to millisecond precision.
    Format: YYYY-MM-DD 00:00:00.000
    """
    return (timestamp.hour == 0 and 
            timestamp.minute == 0 and 
            timestamp.second == 0 and 
            timestamp.microsecond == 0)
```

**Handling:**
- Flag with `flag_type = 'SOD'`
- Store in `flagged_trades` table
- Include reason: "Start of day position restoration"
- Exclude from all P&L calculations

#### Exercised Options
**Detection Logic:**
```python
def is_exercised_option(price: float, instrument_name: str) -> bool:
    """
    Exercised options have price exactly 0.0 and are option instruments.
    """
    is_option = 'OCAD' in instrument_name or 'OPAD' in instrument_name
    return is_option and price == 0.0
```

**Handling:**
- Flag with `flag_type = 'EXERCISED'`
- Store in `flagged_trades` table
- Include reason: "Option exercised at expiry"
- Exclude from P&L calculations
- Monitor for potential follow-up transactions

### 5. Symbol Translation

#### Actant Symbol Format
```
Options: XCMEO[C/P]ADPS{YYYYMMDD}N0{UNDERLYING}/{STRIKE}
Futures: XCMEFFDPSX{YYYYMMDD}U0{CONTRACT}
```

#### Translation Logic
```python
def translate_symbol(actant_symbol: str) -> tuple[str, str]:
    """
    Returns (bloomberg_symbol, instrument_type)
    """
    # Check cache first
    if cached := lookup_cache(actant_symbol):
        return cached
    
    # Parse components
    if 'OCAD' in actant_symbol or 'OPAD' in actant_symbol:
        # Option translation logic
        instrument_type = 'OPT'
        bloomberg_symbol = translate_option(actant_symbol)
    elif 'FFDPS' in actant_symbol:
        # Future translation logic
        instrument_type = 'FUT'
        bloomberg_symbol = translate_future(actant_symbol)
    else:
        raise ValueError(f"Unknown instrument type: {actant_symbol}")
    
    # Cache result
    cache_translation(actant_symbol, bloomberg_symbol, instrument_type)
    return bloomberg_symbol, instrument_type
```

### 6. Performance Optimizations

1. **Batch Processing**
   - Process up to 1000 rows per transaction
   - Reduces database overhead significantly

2. **Smart Indexing**
   - Primary indexes on date, symbol for P&L queries
   - Unique index on trade_id for duplicate prevention

3. **Connection Management**
   - Single persistent connection per worker
   - WAL mode for concurrent reads

4. **Incremental Processing**
   - Track exact row number processed
   - Skip to new rows on file changes

5. **Memory Efficiency**
   - Stream CSV processing (no full file load)
   - Process in chunks of 1000 rows

### 7. Error Handling & Recovery

#### Transaction Safety
- All database operations in transactions
- Rollback on any error
- Last processed row only updated on success

#### Duplicate Prevention
- Unique constraint on trade_id
- Check existence before insert
- Log duplicates for investigation

#### Partial Processing Recovery
```python
def resume_processing(filename: str):
    """Resume processing from last successful row"""
    metadata = get_processing_metadata(filename)
    if metadata:
        start_row = metadata.last_processed_row + 1
        process_file_from_row(filename, start_row)
    else:
        process_file_from_beginning(filename)
```

#### Validation Error Handling
- Log errors to `processing_errors` table
- Continue processing other rows
- Daily error report for review

### 8. Monitoring & Health Checks

#### Real-time Metrics
- Files pending processing
- Processing lag (seconds since file modified)
- Rows processed per second
- Error rate (errors per 1000 rows)

#### Data Quality Checks
- Symbol translation success rate
- Duplicate trades detected
- SOD trades per day
- Exercised options per day
- Missing required fields

#### Health Dashboard Components
```
┌─────────────────────────────────────┐
│ Trade Processing Health Dashboard   │
├─────────────────────────────────────┤
│ Files Processed Today: 5            │
│ Total Trades: 12,456                │
│ Processing Lag: 0.3s                │
│ Error Rate: 0.01%                   │
├─────────────────────────────────────┤
│ Special Cases Today:                │
│ - SOD Trades: 45                    │
│ - Exercised Options: 2              │
├─────────────────────────────────────┤
│ Last Error: 2025-01-15 14:32:10     │
│ Type: Symbol translation failed      │
│ Symbol: XCMEOCADPS20250714N0VY2/XYZ │
└─────────────────────────────────────┘
```

### 9. Implementation Phases

#### Phase 1: Core Pipeline (Week 1)
- File watcher with change detection
- Basic CSV parsing and validation
- Database schema creation
- Processing metadata tracking

#### Phase 2: Transformation (Week 1-2)
- Symbol translation with caching
- Quantity adjustment for sells
- Type detection (FUT/OPT)
- CTO format mapping

#### Phase 3: Edge Cases (Week 2)
- SOD detection and flagging
- Exercise detection and flagging
- Error logging system
- Validation reporting

#### Phase 4: Performance & Monitoring (Week 3)
- Batch processing optimization
- Health dashboard
- Performance metrics
- Alert system

### 10. Testing Strategy

#### Unit Tests
- Symbol translation accuracy
- Edge case detection logic
- Quantity adjustment rules
- Date/time parsing

#### Integration Tests
- End-to-end file processing
- Database transaction handling
- Error recovery scenarios
- Duplicate prevention

#### Performance Tests
- Large file processing (100k+ rows)
- Concurrent file updates
- Database query performance
- Memory usage under load

### 11. Future Enhancements

1. **Real-time Streaming**: Direct feed integration
2. **Cloud Storage**: S3/Azure blob support
3. **Multi-region**: Distributed processing
4. **ML Anomaly Detection**: Identify unusual trades
5. **API Gateway**: RESTful access to trade data 