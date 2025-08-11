# Realized P&L Storage Locations in Production

## Overview

In production, realized P&L values are stored in multiple database tables within `trades.db`. Each table serves a specific purpose in tracking and reporting P&L.

## Primary Storage Tables

### 1. **realized_fifo** and **realized_lifo** Tables

These are the main tables that store individual trade realizations:

```sql
CREATE TABLE realized_fifo (
    symbol TEXT,
    sequenceIdBeingOffset TEXT,      -- ID of position being closed
    sequenceIdDoingOffsetting TEXT,   -- ID of trade doing the closing
    partialFull TEXT,                 -- 'partial' or 'full'
    quantity REAL,                    -- Quantity realized
    entryPrice REAL,                  -- Original entry price
    exitPrice REAL,                   -- Exit price
    realizedPnL REAL,                -- Calculated P&L amount
    timestamp TEXT                    -- When realization occurred
)
```

**Example Entry:**
```
symbol: TYU5 Comdty
sequenceIdBeingOffset: 20250721-1
sequenceIdDoingOffsetting: 20250721-2
partialFull: full
quantity: 1.0
entryPrice: 111.25
exitPrice: 111.21875
realizedPnL: 31.25
timestamp: 2025-07-21 13:28:32
```

### 2. **daily_positions** Table

Aggregates realized P&L by day and symbol:

```sql
CREATE TABLE daily_positions (
    date DATE,
    symbol TEXT,
    method TEXT,              -- 'fifo' or 'lifo'
    open_position REAL,       -- Net open position at EOD
    closed_position INTEGER,  -- Total quantity closed during day
    realized_pnl REAL,       -- Total realized P&L for the day
    unrealized_pnl REAL,     -- Unrealized P&L at EOD
    timestamp TEXT,
    PRIMARY KEY (date, symbol, method)
)
```

**Example Entry:**
```
date: 2025-07-21
symbol: TYU5 Comdty
method: fifo
open_position: 2.0
closed_position: 1
realized_pnl: 31.25
unrealized_pnl: 0.0
timestamp: 2025-07-21 16:00:00
```

### 3. **positions** Table

The master positions table includes cumulative realized P&L:

```sql
CREATE TABLE positions (
    symbol TEXT PRIMARY KEY,
    open_position REAL,
    closed_position REAL,
    fifo_realized_pnl REAL,    -- Total FIFO realized P&L
    fifo_unrealized_pnl REAL,
    lifo_realized_pnl REAL,    -- Total LIFO realized P&L
    lifo_unrealized_pnl REAL,
    -- ... other columns ...
)
```

This table is displayed in the FRGMonitor Live Positions tab.

## Data Flow

```
1. Trade Execution
   ↓
2. TradeLedgerWatcher processes trade
   ↓
3. process_new_trade() calculates realized P&L
   ↓
4. Inserts into realized_fifo/lifo table
   ↓
5. Updates daily_positions table
   ↓
6. PositionsAggregator aggregates to positions table
   ↓
7. FRGMonitor displays from positions table
```

## SQL Queries to Access Realized P&L

### Get all realizations for a symbol:
```sql
SELECT * FROM realized_fifo 
WHERE symbol = 'TYU5 Comdty'
ORDER BY timestamp DESC;
```

### Get daily realized P&L summary:
```sql
SELECT date, symbol, realized_pnl, closed_position
FROM daily_positions 
WHERE method = 'fifo'
ORDER BY date DESC;
```

### Get current cumulative realized P&L:
```sql
SELECT symbol, fifo_realized_pnl, lifo_realized_pnl
FROM positions
WHERE open_position != 0 OR closed_position != 0;
```

### Get detailed realization history with calculations:
```sql
SELECT 
    symbol,
    quantity,
    entryPrice,
    exitPrice,
    realizedPnL,
    CASE 
        WHEN entryPrice < exitPrice THEN 'Long Profit'
        WHEN entryPrice > exitPrice THEN 'Short Profit'
        ELSE 'Break Even'
    END as trade_type,
    timestamp
FROM realized_fifo
ORDER BY timestamp DESC
LIMIT 50;
```

## Key Points

1. **Permanent Storage**: All realized P&L values are permanently stored in `trades.db`

2. **Multiple Views**: The same P&L data is available at different aggregation levels:
   - Individual trades (`realized_fifo/lifo`)
   - Daily summaries (`daily_positions`)
   - Current totals (`positions`)

3. **Audit Trail**: The `realized_fifo/lifo` tables provide a complete audit trail showing:
   - Which positions were offset
   - When they were offset
   - Exact prices and calculations

4. **Real-time Updates**: As trades are processed, all three tables are updated in a single database transaction

5. **Historical Analysis**: The `daily_positions` table enables historical P&L analysis and reporting

This multi-table approach ensures data integrity, enables various reporting views, and maintains a complete audit trail of all P&L calculations.