# Unrealized P&L Storage Flow

## Overview

After the PositionsAggregator calculates unrealized P&L values, they are stored in the `positions` table in `trades.db`. This document traces the complete flow from calculation to storage.

## Storage Flow

### 1. **Calculation Phase**
The PositionsAggregator:
- Loads open positions from `trades_fifo/lifo` tables
- Loads current prices from `pricing` table
- Calls `calculate_unrealized_pnl()` for each symbol
- Sums up P&L values per symbol

### 2. **Cache Update Phase**
```python
# In _load_positions_from_db() around line 220:
self.positions_cache.loc[mask, 'fifo_unrealized_pnl'] = total_unrealized
self.positions_cache.loc[mask, 'fifo_unrealized_pnl_close'] = total_unrealized_close
self.positions_cache.loc[mask, 'lifo_unrealized_pnl'] = total_unrealized
self.positions_cache.loc[mask, 'lifo_unrealized_pnl_close'] = total_unrealized_close
```

### 3. **Queue for Database Write**
```python
# Line 257:
self.db_write_queue.put(self.positions_cache.copy())
```

### 4. **Database Write Phase**
A separate writer thread continuously processes the queue:
```python
# In _write_positions_to_db() starting at line 382:
cursor.execute("""
    INSERT OR REPLACE INTO positions (
        symbol, open_position, closed_position,
        delta_y, gamma_y, speed_y, theta, vega,
        fifo_realized_pnl, fifo_unrealized_pnl,
        lifo_realized_pnl, lifo_unrealized_pnl,
        fifo_unrealized_pnl_close, lifo_unrealized_pnl_close,
        last_updated, last_trade_update, last_greek_update,
        has_greeks, instrument_type
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (...))
```

## The `positions` Table Schema

```sql
CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT PRIMARY KEY,
    open_position REAL DEFAULT 0,
    closed_position REAL DEFAULT 0,
    delta_y REAL,
    gamma_y REAL,
    speed_y REAL,
    theta REAL,
    vega REAL,
    fifo_realized_pnl REAL DEFAULT 0,
    fifo_unrealized_pnl REAL DEFAULT 0,        -- Live unrealized P&L (FIFO)
    lifo_realized_pnl REAL DEFAULT 0,
    lifo_unrealized_pnl REAL DEFAULT 0,        -- Live unrealized P&L (LIFO)
    fifo_unrealized_pnl_close REAL DEFAULT 0,  -- Close unrealized P&L (FIFO)
    lifo_unrealized_pnl_close REAL DEFAULT 0,  -- Close unrealized P&L (LIFO)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trade_update TIMESTAMP,
    last_greek_update TIMESTAMP,
    has_greeks BOOLEAN DEFAULT 0,
    instrument_type TEXT
)
```

## Key P&L Columns

1. **`fifo_unrealized_pnl`** - Live unrealized P&L using FIFO method and current market prices
2. **`lifo_unrealized_pnl`** - Live unrealized P&L using LIFO method and current market prices
3. **`fifo_unrealized_pnl_close`** - Close unrealized P&L using FIFO and today's close prices
4. **`lifo_unrealized_pnl_close`** - Close unrealized P&L using LIFO and today's close prices

## Update Frequency

The `positions` table is updated:
- When new trades arrive (via Trade Ledger Watcher)
- When prices change (via price updates)
- When Greeks are recalculated (via Spot Risk system)

## Thread Safety

- Updates are queued to avoid database contention
- A dedicated writer thread handles all database writes
- Uses `INSERT OR REPLACE` to ensure atomic updates

## Access by Dashboard

The FRGMonitor dashboard queries this table directly:
```sql
SELECT symbol, open_position, closed_position,
       fifo_realized_pnl, fifo_unrealized_pnl,
       fifo_unrealized_pnl_close
FROM positions
WHERE open_position != 0 OR closed_position != 0
```

## Important Notes

1. **One row per symbol** - All positions for a symbol are aggregated
2. **Real-time updates** - Values change as market prices update
3. **Close P&L** - Only populated if today's close price exists
4. **Thread-safe** - Multiple processes can trigger updates safely