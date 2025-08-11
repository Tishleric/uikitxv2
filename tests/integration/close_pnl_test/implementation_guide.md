# Close PnL Implementation Guide

## Overview
This document provides the exact code changes needed to implement close PnL calculation that parallels the live PnL methodology.

## Validation Results
✅ All tests passed successfully
- Live PnL calculations remain unchanged
- Close PnL uses identical methodology with 'close' prices
- NULL displayed when today's close price unavailable
- No impact on daily_positions table

## Required Code Changes

### 1. Database Schema Update

Add migration script to update positions table:

```sql
-- Add columns for close-based unrealized PnL
ALTER TABLE positions ADD COLUMN fifo_unrealized_pnl_close REAL DEFAULT 0;
ALTER TABLE positions ADD COLUMN lifo_unrealized_pnl_close REAL DEFAULT 0;
```

### 2. Update data_manager.py

In `lib/trading/pnl_fifo_lifo/data_manager.py`, modify the positions table creation (lines 106-128):

```python
positions_schema = """
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
    fifo_unrealized_pnl REAL DEFAULT 0,
    lifo_realized_pnl REAL DEFAULT 0,
    lifo_unrealized_pnl REAL DEFAULT 0,
    fifo_unrealized_pnl_close REAL DEFAULT 0,      -- NEW
    lifo_unrealized_pnl_close REAL DEFAULT 0,      -- NEW
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trade_update TIMESTAMP,
    last_greek_update TIMESTAMP,
    has_greeks BOOLEAN DEFAULT 0,
    instrument_type TEXT
)
"""
```

### 3. Update PositionsAggregator

In `lib/trading/pnl_fifo_lifo/positions_aggregator.py`:

#### a) Modify _load_positions_from_db() (lines 106-140):

Add initialization for close PnL columns:
```python
# Add placeholder columns for unrealized P&L and Greeks
self.positions_cache['fifo_unrealized_pnl'] = 0.0
self.positions_cache['lifo_unrealized_pnl'] = 0.0
self.positions_cache['fifo_unrealized_pnl_close'] = 0.0     # NEW
self.positions_cache['lifo_unrealized_pnl_close'] = 0.0     # NEW
```

Replace the unrealized PnL calculation section (lines 119-135) with:
```python
# Calculate unrealized P&L for all positions
price_dicts = load_pricing_dictionaries(conn)

for method in ['fifo', 'lifo']:
    positions_df = view_unrealized_positions(conn, method)
    if not positions_df.empty:
        for symbol in positions_df['symbol'].unique():
            symbol_positions = positions_df[positions_df['symbol'] == symbol]
            
            # Calculate LIVE unrealized PnL
            unrealized_list = calculate_unrealized_pnl(symbol_positions, price_dicts, 'live')
            total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
            
            # Calculate CLOSE unrealized PnL
            total_unrealized_close = 0.0
            
            # Check if we have today's close price
            today = datetime.now().strftime('%Y-%m-%d')
            close_query = """
            SELECT price, timestamp 
            FROM pricing 
            WHERE symbol = ? AND price_type = 'close'
            """
            close_result = conn.execute(close_query, (symbol,)).fetchone()
            
            if close_result and close_result[1] and close_result[1].startswith(today):
                # Create modified price dict with close price as 'now'
                close_price_dicts = price_dicts.copy()
                close_price_dicts['now'] = price_dicts.get('close', {}).copy()
                
                # Calculate unrealized with close prices
                unrealized_close_list = calculate_unrealized_pnl(
                    symbol_positions, close_price_dicts, 'live'
                )
                total_unrealized_close = sum(u['unrealizedPnL'] for u in unrealized_close_list)
            
            # Update the cache
            mask = self.positions_cache['symbol'] == symbol
            if mask.any():
                self.positions_cache.loc[mask, f'{method}_unrealized_pnl'] = total_unrealized
                self.positions_cache.loc[mask, f'{method}_unrealized_pnl_close'] = total_unrealized_close
```

#### b) Modify _update_positions_with_greeks() (lines 243-250):

Add close PnL columns to reset:
```python
# Reset Greek columns before updating
self.positions_cache['delta_y'] = None
self.positions_cache['gamma_y'] = None
self.positions_cache['speed_y'] = None
self.positions_cache['theta'] = None
self.positions_cache['vega'] = None
self.positions_cache['has_greeks'] = False
self.positions_cache['instrument_type'] = None
# Note: Don't reset close PnL columns here - they persist from load
```

#### c) Modify _write_positions_to_db() (lines 289-310):

Update the INSERT statement to include close PnL columns:
```python
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
""", (
    row['symbol'],
    row['open_position'],
    row['closed_position'],
    row.get('delta_y'),
    row.get('gamma_y'),
    row.get('speed_y'),
    row.get('theta'),
    row.get('vega'),
    row['fifo_realized_pnl'],
    row['fifo_unrealized_pnl'],
    row['lifo_realized_pnl'],
    row['lifo_unrealized_pnl'],
    row.get('fifo_unrealized_pnl_close', 0),      # NEW
    row.get('lifo_unrealized_pnl_close', 0),      # NEW
    now,
    now if pd.notna(row.get('fifo_realized_pnl')) else None,
    now if pd.notna(row.get('has_greeks')) and row['has_greeks'] else None,
    row.get('has_greeks', False),
    row.get('instrument_type')
))
```

### 4. Update FRGMonitor Callback

In `apps/dashboards/main/app.py`, modify the `update_positions_table` callback (lines 3411-3572):

#### a) Remove time-based logic (lines 3428-3456) and replace with:

```python
# Get current Chicago time for display
chicago_tz = pytz.timezone('America/Chicago')
now_cdt = datetime.now(chicago_tz)
today_str = now_cdt.strftime('%Y-%m-%d')

# Dynamically determine UTC offset for SQLite
utc_offset = now_cdt.utcoffset()
if utc_offset:
    offset_hours = int(utc_offset.total_seconds() / 3600)
    date_modifier = f"'{offset_hours} hours'"
else:
    date_modifier = "'0 hours'"
```

#### b) Update the main query (starting at line 3458):

```python
# Fetch positions data
query = f"""
SELECT 
    p.symbol,
    p.instrument_type,
    p.open_position,
    p.closed_position,
    p.delta_y,
    p.gamma_y,
    p.speed_y,
    p.theta,
    (p.theta / 252.0) as theta_decay_pnl,
    p.vega,
    p.fifo_realized_pnl,
    p.fifo_unrealized_pnl,
    (p.fifo_realized_pnl + p.fifo_unrealized_pnl) as pnl_live,
    p.lifo_realized_pnl,
    p.lifo_unrealized_pnl,
    CASE WHEN p.instrument_type = 'FUTURE' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS non_gamma_lifo,
    CASE WHEN p.instrument_type = 'OPTION' THEN (p.lifo_realized_pnl + p.lifo_unrealized_pnl) ELSE NULL END AS gamma_lifo,
    p.last_updated,
    pr_now.price as live_px,
    pr_close.price as close_px,
    -- Close PnL: show only if close price is from today
    CASE 
        WHEN pr_close.timestamp LIKE DATE('now', {date_modifier}) || '%' 
        THEN (p.fifo_realized_pnl + p.fifo_unrealized_pnl_close)
        ELSE NULL 
    END as pnl_close
FROM positions p
LEFT JOIN pricing pr_now ON p.symbol = pr_now.symbol AND pr_now.price_type = 'now'
LEFT JOIN pricing pr_close ON p.symbol = pr_close.symbol AND pr_close.price_type = 'close'
WHERE p.open_position != 0 OR p.closed_position != 0
ORDER BY p.symbol
"""
```

## Testing the Implementation

1. Run database migration to add new columns
2. Restart PositionsAggregator service
3. Verify live PnL values remain unchanged
4. Check that close PnL appears when close prices are available
5. Confirm NULL displays for symbols without today's close price

## Key Benefits

- **Consistency**: Close PnL uses exact same calculation methodology as live PnL
- **Performance**: Pre-calculated values, no on-the-fly computation in UI
- **Simplicity**: No complex time windows, just data availability
- **Reliability**: No dependency on daily_positions table for close PnL