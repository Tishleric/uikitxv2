# Trade Processing Gap Analysis

## Existing System Overview

### Current Components
1. **TradePreprocessor** (`lib/trading/pnl_calculator/trade_preprocessor.py`)
   - Symbol translation (Actant → Bloomberg)
   - SOD detection (midnight trades)
   - Expiry detection (zero price)
   - Buy/Sell → signed quantity conversion
   - Position tracking integration
   - State tracking to avoid reprocessing

2. **TradeFileWatcher** (`lib/trading/pnl_calculator/trade_file_watcher.py`)
   - Monitors trade_ledger directory
   - Processes new and modified files
   - Handles 4pm CDT cutover logic
   - Uses watchdog for file system events

3. **PnLStorage** (`lib/trading/pnl_calculator/storage.py`)
   - SQLite database operations
   - Market prices storage
   - Processed trades tracking
   - P&L snapshots

## Gap Analysis

### ✅ Already Implemented (Reusable)
1. **File Watching**
   - Directory monitoring with watchdog
   - File change detection
   - Trade file pattern matching
   - 4pm CDT cutover logic

2. **Symbol Translation**
   - Actant → Bloomberg conversion
   - SymbolTranslator class already exists

3. **Edge Case Detection**
   - SOD detection (midnight timestamp)
   - Expiry detection (price = 0)
   - Both are flagged in current system

4. **Basic Processing**
   - CSV parsing
   - Buy/Sell → signed quantity
   - Timestamp parsing with timezone

5. **State Tracking**
   - File size/modification tracking
   - Prevents reprocessing

### ❌ Missing/Different from Requirements

1. **Database Schema Mismatch**
   ```
   Current:                    Required (CTO):
   - trade_id                  - Date
   - instrument_name          - Time  
   - trade_date               - Symbol (Bloomberg)
   - trade_timestamp          - Action (BUY/SELL)
   - quantity                 - Quantity (negative for sells)
   - price                    - Price
   - side                     - Fees
   - processed_at             - Counterparty
   - source_file              - trade_id
                              - Type (FUT/OPT)
   ```

2. **Processing Approach**
   - Current: Processes entire file each time
   - Required: Process only new rows (row-level tracking)

3. **Flagged Trade Storage**
   - Current: Marks with validation_status in same table
   - Required: Separate flagged_trades table

4. **Millisecond Precision for SOD**
   - Current: Only checks hour and minute
   - Required: Check down to millisecond (00:00:00.000)

5. **Counterparty Field**
   - Current: Not tracked
   - Required: Always 'FRGM'

6. **Instrument Type**
   - Current: Not explicitly stored
   - Required: FUT/OPT field

7. **Startup Processing**
   - Current: Processes ALL files synchronously on startup
   - Required: Smart incremental processing

## Decision: Amend or Reimplement?

### Analysis
**Pros of Amending:**
- File watching infrastructure works well
- Symbol translation is complete
- Edge case detection logic exists
- State tracking prevents full reprocessing
- Position tracking integration exists

**Pros of Reimplementing:**
- Database schema is fundamentally different
- Row-level tracking needs new approach
- Clean separation of concerns
- Avoid legacy complexity
- Implement all optimizations from start

### Recommendation: **Hybrid Approach**

**Keep and Enhance:**
1. Symbol translation (SymbolTranslator)
2. File watching pattern (but make it lazy)
3. Edge case detection logic

**Reimplement:**
1. Database schema and storage layer
2. Processing pipeline with row-level tracking
3. Separate flagged trades handling
4. Batch processing with transactions

## Implementation Plan

### Phase 1: New Storage Layer
```python
# Create new module: lib/trading/pnl_calculator/trade_storage_v2.py
class TradeStorageV2:
    - CTO schema implementation
    - Row-level tracking
    - Batch operations
    - Separate flagged_trades
```

### Phase 2: Enhanced Processor
```python
# Create new module: lib/trading/pnl_calculator/trade_processor_v2.py
class TradeProcessorV2:
    - Use existing SymbolTranslator
    - Row-level incremental processing
    - Millisecond SOD detection
    - Batch transactions
    - Better error handling
```

### Phase 3: Lazy File Watcher
```python
# Modify existing: lib/trading/pnl_calculator/trade_file_watcher.py
- Remove automatic startup processing
- Add manual trigger method
- Keep watchdog infrastructure
```

### Phase 4: Integration
```python
# Update: apps/dashboards/pnl/callbacks.py
- Remove automatic watcher start
- Add manual processing trigger
- Progress tracking UI
```

## Benefits of Hybrid Approach

1. **Faster Implementation**: Reuse proven components
2. **Lower Risk**: Keep working file watching
3. **Clean Architecture**: New storage/processing is separate
4. **Easy Rollback**: Old system remains intact
5. **Incremental Migration**: Can run both in parallel

## Migration Strategy

1. Implement new storage/processor alongside existing
2. Test with subset of files
3. Add switch to use new system
4. Run in parallel for validation
5. Cut over when confident
6. Remove old system later

This approach gives us the best of both worlds - we keep what works well and reimplement what needs fundamental changes. 