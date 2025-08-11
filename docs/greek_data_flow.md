# Greek Data Flow Architecture

## Overview
Greeks are calculated by the spot_risk_watcher service and passed in-memory to the positions_aggregator via Redis/Arrow. They are NOT persisted in the database.

## Data Flow

### 1. Greek Calculation (spot_risk_watcher)
- Monitors spot risk CSV files
- Calculates Greeks using parallel processing
- Publishes results to Redis channel `actant:greeks` using Apache Arrow serialization

### 2. Greek Reception (positions_aggregator)
- Subscribes to Redis channel `actant:greeks`
- Receives Greek data packages
- Stores in memory: `self.greek_data_cache`
- Applies position weighting and updates `self.positions_cache`

### 3. Database Design
- The `positions` table has Greek columns (delta_y, gamma_y, etc.)
- These columns remain empty/NULL in normal operation
- Greeks are maintained only in memory for performance

### 4. Price Update Flow (Fixed)
When prices update:
1. `update_current_price()` publishes "positions:changed" to Redis
2. positions_aggregator receives signal
3. Calls `_load_positions_from_db()` which:
   - Loads positions from database
   - **Restores Greeks from `self.greek_data_cache`** (the fix)
   - Calculates new P&L values
   - Writes to database (with preserved Greeks)

## Key Points

- Greeks are ephemeral - calculated fresh each time spot risk data arrives
- Database is used for positions and P&L, not Greeks
- The in-memory cache (`greek_data_cache`) is the source of truth for Greeks
- Price updates no longer overwrite Greeks thanks to the preservation logic

## Troubleshooting

If Greeks appear to be missing:
1. Check if spot_risk_watcher is running and processing files
2. Verify Redis is running and messages are being published
3. Confirm positions_aggregator is subscribed to the correct channel
4. Check logs for Greek data reception messages