# Live PnL and Close PnL Implementation

## Overview
The system maintains two parallel P&L calculations:
- **Live PnL**: Real-time P&L using current market prices
- **Close PnL**: P&L using today's official close prices (when available)

## Data Flow

### 1. Price Updates Trigger Calculations
When `update_current_price()` is called:
1. Price is written to `pricing` table with `price_type='now'`
2. Redis publishes "positions:changed" signal
3. PositionsAggregator receives signal and:
   - Recalculates `fifo_unrealized_pnl` using 'now' prices
   - Recalculates `fifo_unrealized_pnl_close` using 'close' prices (if today's close exists)
   - Writes updated values to `positions` table
   - Calls `update_daily_positions_unrealized_pnl()` to update daily positions

### 2. Live Positions Tab (FRGMonitor)
Shows real-time position data from `positions` table:
- **Live PnL** = `fifo_realized_pnl + fifo_unrealized_pnl`
  - Always visible, updates with each price change
  - Uses `price_type='now'` for unrealized calculation
  
- **Close PnL** = `fifo_realized_pnl + fifo_unrealized_pnl_close`
  - Only visible when today's close price exists
  - Uses `price_type='close'` for unrealized calculation
  - Shows NULL if close price is not from today

### 3. Daily Positions Tab
Shows historical daily P&L from `daily_positions` table:
- **Total P&L** = `realized_pnl + unrealized_pnl`
  - `realized_pnl`: Accumulated throughout the day from trades
  - `unrealized_pnl`: Updated only when today's close prices are available
  - Represents the official Close P&L for each day

## Key Tables and Columns

### positions table
- `fifo_realized_pnl`: Realized P&L from closed trades
- `fifo_unrealized_pnl`: Unrealized P&L using current prices ('now')
- `fifo_unrealized_pnl_close`: Unrealized P&L using close prices

### daily_positions table
- `realized_pnl`: Accumulated realized P&L for the day
- `unrealized_pnl`: Unrealized P&L using close prices (Close PnL unrealized component)
- One row per symbol/method/date

### pricing table
- `price_type='now'`: Current market prices
- `price_type='close'`: Official close prices
- `timestamp`: Used to verify close price is from today

## Process Alignment

### Live PnL Process ✓
1. Price update → `update_current_price()`
2. Redis signal → PositionsAggregator
3. Calculate unrealized using 'now' prices
4. Update `positions.fifo_unrealized_pnl`
5. Dashboard shows Live PnL immediately

### Close PnL Process ✓
1. Close price arrives → `update_current_price()` with `price_type='close'`
2. Redis signal → PositionsAggregator
3. Check if close price is from today
4. If yes: Calculate unrealized using 'close' prices
5. Update `positions.fifo_unrealized_pnl_close`
6. Update `daily_positions.unrealized_pnl`
7. Dashboard shows Close PnL (both tabs)

## Important Notes

1. **Timing**: Close prices typically arrive at 2pm CT for futures/options
2. **Historical**: Daily Positions tab shows historical Close PnL values
3. **Real-time**: Live Positions tab shows both Live and Close PnL
4. **Validation**: System only uses close prices from current trading day