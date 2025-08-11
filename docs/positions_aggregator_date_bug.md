# Positions Aggregator Date Filtering Bug

## Issue Summary
The positions aggregator incorrectly shows ALL historical closed positions when trades are from future dates (e.g., August 2025).

## Root Cause
In `lib/trading/pnl_fifo_lifo/positions_aggregator.py`:

1. **Line 70**: Correctly calculates trading day using `get_trading_day(datetime.now())`
2. **Lines 86, 95, 119, 134**: SQL queries ignore this and use `DATE('now', 'localtime')` instead

## Example
- Current time: August 6, 2025, 6:27 PM
- Trading day (correct): 2025-08-07 (after 5pm rolls to next day)
- SQLite 'now': 2025-08-06 (actual date)
- Result: No trades from 2025-08-07 match 2025-08-06, so ALL historical closed positions appear

## The Fix Needed
Replace `DATE('now', 'localtime')` with the calculated `current_trading_day` variable in the SQL WHERE clauses.

### Current (Buggy) Code:
```sql
WHERE 
    DATE(timestamp, 
         CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
              THEN '+1 day' 
              ELSE '+0 day' 
         END) = DATE('now', 'localtime')
```

### Fixed Code:
```sql
WHERE 
    DATE(timestamp, 
         CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
              THEN '+1 day' 
              ELSE '+0 day' 
         END) = ?
```
And pass `current_trading_day` as a parameter.

## Impact
- Shows 9+ historical closed positions instead of 0
- Close prices also affected (similar date comparison issue in dashboard)
- Only affects systems with future-dated trades

## Test Results
Running `tests/diagnostics/test_positions_date_bug.py`:
- Positions aggregator calculates: 2025-08-07
- SQL query filters for: 2025-08-06
- Result: 9 historical closed positions shown instead of 0

## Workaround
Until fixed, either:
1. Use trades with current dates (not future dates)
2. Manually filter closed positions in the UI
3. Apply the fix to use calculated trading day in SQL queries