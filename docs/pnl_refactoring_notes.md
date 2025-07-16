# P&L Refactoring Notes

## Overview
This document tracks all changes made to prepare the P&L tracking system for CTO's calculation engine integration.

**Strategy**: Complete replacement of calculation logic while preserving data flow infrastructure.

## Pass 1: Comment Out Trade Processing Logic

### Files Modified
1. **lib/trading/pnl_calculator/trade_preprocessor.py**
   - Status: COMPLETED
   - Changes:
     - Commented out position tracking updates (lines 177-237)
     - Enhanced SOD detection to check milliseconds (lines 145-150)
     - Kept symbol translation, Buy/Sell conversion, validation
     - Added mock columns for compatibility
   - Rollback: All original code preserved in comments

2. **lib/trading/pnl_calculator/calculator.py**
   - Status: COMPLETED (from previous passes)
   - Changes:
     - Commented out FIFO calculations
     - Return mock data for all calculation methods
   - Rollback: All original code preserved in comments

3. **lib/trading/pnl_calculator/position_manager.py**
   - Status: COMPLETED
   - Changes:
     - Commented out position tracking logic in process_trade (lines 137-237)
     - Return mock PositionUpdate with PENDING status
     - Fixed monitor decorator import
   - Rollback: All original code preserved in comments

### Integration Points Identified
1. **TradePreprocessor.process_trade_file()**: Processes raw CSV, does symbol translation
2. **PositionManager.process_trade()**: Currently returns mock data 
3. **PnLCalculator**: All calculation methods return mock data

### Pass 1 Testing
- [x] Code changes complete
- [x] Verify imports still work (TradePreprocessor, PositionManager)
- [x] Fixed monitor decorator issues for both modules
- [ ] Test that trade processing runs without errors (manual test needed)

## Pass 2: Enhance File Watching & Row-Level Tracking

### Files Modified
1. **lib/trading/pnl_calculator/storage.py**
   - Status: COMPLETED
   - Changes:
     - Added `trade_processing_tracker` table for row-level deduplication
     - Added methods: `get_processed_trades_for_file()`, `record_processed_trade()`, etc.
     - Tracks each trade by source file and trade ID to prevent reprocessing
   
2. **lib/trading/pnl_calculator/trade_preprocessor.py**
   - Status: COMPLETED
   - Changes:
     - Enhanced process_trade_file() to use row-level tracking
     - Only processes new trades (by row number and trade ID)
     - Added helper methods: `_read_trade_csv()`, `_preprocess_trade()`
     - SOD detection now checks millisecond precision (00:00:00.000)
   
3. **apps/dashboards/pnl/callbacks.py**
   - Status: COMPLETED
   - Changes:
     - Disabled automatic file watcher startup at module load
     - Added lazy loading - watchers start on first dashboard access
     - Prevents processing all historical files at app startup

## Pass 3: New Storage Schema

### CTO's Required Schema
```sql
CREATE TABLE processed_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    symbol TEXT NOT NULL,      -- Bloomberg format
    action TEXT NOT NULL,       -- BUY/SELL
    quantity INTEGER NOT NULL,  -- Negative for sells
    price REAL NOT NULL,
    fees REAL DEFAULT 0,
    counterparty TEXT DEFAULT 'FRGM',
    trade_id TEXT,
    type TEXT NOT NULL,         -- FUT/OPT
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Separate tables for special cases
CREATE TABLE sod_trades (
    trade_id INTEGER PRIMARY KEY,
    original_timestamp TEXT,
    FOREIGN KEY (trade_id) REFERENCES processed_trades(id)
);

CREATE TABLE exercised_options (
    trade_id INTEGER PRIMARY KEY,
    original_price REAL,
    FOREIGN KEY (trade_id) REFERENCES processed_trades(id)
);
```

### Processing Rules
1. **SOD Detection**: timestamp == midnight to the millisecond
2. **Exercise Detection**: price == 0.0 exactly
3. **Symbol Translation**: Actant → Bloomberg via existing translator
4. **Quantity Sign**: Negative for sells, positive for buys

## Pass 4: Mock Output Format

### CTO's Expected Output Structure
```python
{
    "positions": {
        "ZNH5": {
            "quantity": 10,
            "avg_cost": 110.25,
            "realized_pnl": 1250.00,
            "unrealized_pnl": -312.50
        }
    },
    "daily_pnl": {
        "2024-01-15": {
            "realized": 625.00,
            "unrealized": -156.25,
            "total": 468.75
        }
    },
    "trades_processed": 47,
    "last_update": "2024-01-15T16:00:00"
}
```

## Pass 5: Integration Points

### Input Interface (after preprocessing)
```python
def process_trades_for_calculation(trades: List[ProcessedTrade]) -> None:
    """
    Interface for CTO's calculation engine
    
    Args:
        trades: List of preprocessed trades with all required fields
    """
    # CTO's code will go here
    pass
```

### Output Interface (before UI)
```python
def get_calculation_results() -> Dict[str, Any]:
    """
    Interface to retrieve calculation results
    
    Returns:
        Dictionary matching CTO's output structure
    """
    # CTO's code will provide this
    pass
```

## Change Log

### 2024-XX-XX - Initial Setup
- Created documentation structure
- Defined 5-pass approach
- Specified integration interfaces

---
**Remember**: Update this document after each change for easy rollback if needed. 