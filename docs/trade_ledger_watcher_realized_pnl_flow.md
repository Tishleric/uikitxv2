# TradeLedgerWatcher Realized P&L Flow

## Overview

The TradeLedgerWatcher is responsible for calculating **REALIZED P&L** when trades are executed. It watches CSV files and processes each trade through the FIFO engine.

## Process Flow

```
CSV Trade File → TradeLedgerWatcher → FIFO Engine → Realized P&L
```

## Detailed Steps

### 1. CSV File Detection
- Watches directory: `data/input/trade_ledger/`
- Detects new files or modifications
- File format: `trades_YYYYMMDD.csv`

### 2. Trade Processing

```python
# For each trade in the CSV:
trade = {
    'transactionId': row['tradeId'],
    'symbol': bloomberg_symbol,  # Translated from Actant
    'price': row['price'],
    'quantity': row['quantity'],
    'buySell': row['buySell'],
    'sequenceId': f"{date}-{sequence_number}",
    'time': row['marketTradeTime'],
    'fullPartial': 'full'
}
```

### 3. FIFO Matching

The `process_new_trade()` function:
1. Finds opposite positions (if Buy, find Sells to match)
2. Orders by sequenceId ASC (First-In-First-Out)
3. Matches quantities
4. Calculates realized P&L

### 4. Realized P&L Calculation

**For Long Positions (Buy then Sell):**
```
Realized P&L = (Exit Price - Entry Price) × Quantity × 1000
```

**For Short Positions (Sell then Buy):**
```
Realized P&L = (Entry Price - Exit Price) × Quantity × 1000
```

### 5. Database Updates

Updates three tables:
1. `trades_fifo` - Remaining open positions
2. `realized_fifo` - Realized trades with P&L
3. `daily_positions` - Daily summary

### 6. Redis Notification

After processing:
```python
redis_client.publish("positions:changed", "refresh")
```

This triggers the PositionsAggregator to recalculate unrealized P&L.

## Example Trade Flow

### Input CSV
```csv
tradeId,instrumentName,marketTradeTime,price,quantity,buySell
T001,TYU5,2024-01-15 09:00:00.000,112.50,10,B
T002,TYU5,2024-01-15 10:00:00.000,112.75,10,S
```

### Processing Steps

1. **Trade 1 (Buy)**:
   - Insert into `trades_fifo`
   - No realization (no opposite positions)

2. **Trade 2 (Sell)**:
   - Find Buy position to match
   - Calculate: (112.75 - 112.50) × 10 × 1000 = $2,500
   - Insert into `realized_fifo`
   - Remove matched position from `trades_fifo`

### Final State

**realized_fifo table:**
```
symbol | entryPrice | exitPrice | quantity | realizedPnL
TYU5   | 112.50     | 112.75    | 10       | 2500
```

**daily_positions table:**
```
date       | symbol | closed_position | realized_pnl
2024-01-15 | TYU5   | 10             | 2500
```

## Key Points

1. **Symbol Translation**: Actant symbols (e.g., "TYU5") are translated to Bloomberg format (e.g., "TYU5 Comdty")

2. **Sequence IDs**: Format is `YYYYMMDD-N` where N increments for each trade

3. **Partial Fills**: If sell quantity < buy quantity, creates partial realization

4. **Both Methods**: Each trade is processed through both FIFO and LIFO

5. **Transaction Integrity**: All updates happen in a single database transaction

## Error Handling

- Symbol translation failures: Falls back to original symbol
- Database errors: Rolls back entire transaction
- File read errors: Logs and skips file

## Testing

The unit test `test_trade_ledger_watcher_realized_pnl.py` mimics this exact process:
- Creates mock CSV files
- Processes them like the watcher
- Verifies realized P&L calculations
- Checks database state