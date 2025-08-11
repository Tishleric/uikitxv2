# Exact Code Path: Unrealized P&L Insertion into Positions Table

## Complete Flow with Line Numbers

### 1. **Trigger: Redis Signal Received**
**File**: `positions_aggregator.py`
**Line 249**: `if channel == "positions:changed":`

### 2. **Load and Calculate P&L**
**Line 253**: `self._load_positions_from_db()`

Inside `_load_positions_from_db()`:
- **Line 194-195**: Calculate live unrealized P&L
  ```python
  unrealized_list = calculate_unrealized_pnl(symbol_positions, price_dicts, 'live')
  total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
  ```

- **Line 214-216**: Calculate close unrealized P&L (if close price exists)
  ```python
  unrealized_close_list = calculate_unrealized_pnl(symbol_positions, close_price_dicts, 'live')
  total_unrealized_close = sum(u['unrealizedPnL'] for u in unrealized_close_list)
  ```

### 3. **Update In-Memory Cache**
**Lines 221-222**: Store calculated values in DataFrame
```python
self.positions_cache.loc[mask, f'{method}_unrealized_pnl'] = total_unrealized
self.positions_cache.loc[mask, f'{method}_unrealized_pnl_close'] = total_unrealized_close
```

### 4. **Queue for Database Write**
**Line 258**: `self.db_write_queue.put(self.positions_cache.copy())`

### 5. **Writer Thread Picks Up**
**File**: `positions_aggregator.py` (in `_db_writer_thread`)
**Line 432**: `positions_df_to_write = self.db_write_queue.get()`
**Line 438**: `self._write_positions_to_db(positions_df_to_write)`

### 6. **Database Insertion**
**In `_write_positions_to_db()` starting at line 371:**

**Line 374**: Create database connection
```python
conn = sqlite3.connect(self.trades_db_path)
```

**Lines 382-412**: Execute INSERT for each position
```python
cursor.execute("""
    INSERT OR REPLACE INTO positions (
        symbol, open_position, closed_position,
        delta_y, gamma_y, speed_y, theta, vega,
        fifo_realized_pnl, fifo_unrealized_pnl,      # Line 386
        lifo_realized_pnl, lifo_unrealized_pnl,      # Line 387
        fifo_unrealized_pnl_close, lifo_unrealized_pnl_close,  # Line 388
        last_updated, last_trade_update, last_greek_update,
        has_greeks, instrument_type
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    row['symbol'],                           # Line 393
    row['open_position'],                    # Line 394
    row['closed_position'],                  # Line 395
    row['delta_y'],                          # Line 396
    row['gamma_y'],                          # Line 397
    row['speed_y'],                          # Line 398
    row['theta'],                            # Line 399
    row['vega'],                             # Line 400
    row['fifo_realized_pnl'],               # Line 401
    row['fifo_unrealized_pnl'],             # Line 402 ← FIFO unrealized P&L
    row['lifo_realized_pnl'],               # Line 403
    row['lifo_unrealized_pnl'],             # Line 404 ← LIFO unrealized P&L
    row.get('fifo_unrealized_pnl_close', 0), # Line 405 ← FIFO close P&L
    row.get('lifo_unrealized_pnl_close', 0), # Line 406 ← LIFO close P&L
    now,                                     # Line 407
    now,                                     # Line 408
    now if row['has_greeks'] else None,     # Line 409
    1 if row['has_greeks'] else 0,          # Line 410
    row['instrument_type']                   # Line 411
))
```

**Line 414**: Commit the transaction
```python
conn.commit()
```

## Key Points

1. **Thread Safety**: The insertion happens in a dedicated writer thread to avoid database contention
2. **Atomic Updates**: Uses `INSERT OR REPLACE` to ensure each symbol has exactly one row
3. **All P&L Types**: Inserts both live and close P&L for both FIFO and LIFO methods
4. **Timestamps**: Updates `last_updated` and `last_trade_update` with current time

## The Four Unrealized P&L Values Inserted

1. **`fifo_unrealized_pnl`** (line 402) - Live P&L using FIFO method
2. **`lifo_unrealized_pnl`** (line 404) - Live P&L using LIFO method  
3. **`fifo_unrealized_pnl_close`** (line 405) - Close P&L using FIFO method
4. **`lifo_unrealized_pnl_close`** (line 406) - Close P&L using LIFO method

## Database Location

- **Database**: `trades.db`
- **Table**: `positions`
- **Primary Key**: `symbol` (one row per symbol)