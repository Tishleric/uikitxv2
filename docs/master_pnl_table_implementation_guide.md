# Master P&L Table Implementation Guide

## Quick Start for New Context

This guide contains all critical information needed to build the master P&L table from scratch. The master table combines data from three SQLite databases to create a unified P&L view.

## Database Locations

### 1. P&L Database
- **Path**: `data/output/pnl/pnl_tracker.db`
- **Key Tables**:
  - `positions` - Current positions with FIFO tracking
  - `cto_trades` - All processed trades (CTO format)
  - `processed_trades` - Trade processing metadata

### 2. Spot Risk Database  
- **Path**: `data/output/spot_risk/spot_risk.db`
- **Key Tables**:
  - `spot_risk_raw` - Raw data with JSON in `raw_data` column
  - `spot_risk_calculated` - Calculated Greeks
  - `spot_risk_sessions` - Processing sessions

### 3. Market Prices Database
- **Path**: `data/output/market_prices/market_prices.db`
- **Key Tables**:
  - `futures_prices` - Futures market data
  - `options_prices` - Options market data

## Critical Implementation Quirks

### 1. Option Classification Issue
- **Problem**: Positions table has `is_option` field but it may be incorrectly set
- **Solution**: Options can be identified by presence of `option_strike` value
- **Fix Script**: `scripts/fix_option_classification.py` updates this field

### 2. Spot Risk Data Structure
- **Quirk**: The `spot_risk_raw` table stores bid/ask/adjtheor in JSON within `raw_data` column
- **Access Method**: Use SQLite's `json_extract()` function:
  ```sql
  json_extract(sr.raw_data, '$.bid') as bid,
  json_extract(sr.raw_data, '$.ask') as ask,
  json_extract(sr.raw_data, '$.adjtheor') as adjtheor
  ```

### 3. Symbol Format Requirements
- **Critical**: All joins depend on Bloomberg symbol format
- **Format**: `SYMBOL STRIKE Comdty` (e.g., "TYU5 Comdty", "VBYN25P3 110.250 Comdty")
- **Key Join**: `positions.instrument_name = spot_risk_raw.bloomberg_symbol`

### 4. DV01 Logic
- **Futures**: Always 63 (fixed value)
- **Options**: Use `delta_F` from `spot_risk_calculated` table
- **Implementation**:
  ```sql
  CASE 
      WHEN p.is_option = 0 THEN 63  -- Futures DV01
      ELSE sc.delta_F                -- Options DV01
  END as dv01
  ```

### 5. Missing Greek Columns
- **Available**: delta_F, delta_y, gamma_F, gamma_y, speed_F, theta_F, vega_price, vega_y
- **NOT Available**: speed_y, theta_y (these don't exist in the schema)

### 6. SQLite Attachment Syntax
- Must attach databases before joining:
  ```sql
  ATTACH DATABASE 'path/to/spot_risk.db' AS spot_risk;
  ATTACH DATABASE 'path/to/market_prices.db' AS market_prices;
  ```
- Then reference as: `spot_risk.table_name`, `market_prices.table_name`

### 7. Position Tracking State
- **Check**: PositionManager may have position tracking disabled
- **Location**: `lib/trading/pnl_calculator/position_manager.py`
- **Fix**: Use `scripts/fix_position_tracking.py` or SimpleTradeProcessor from `tyu5_pnl/`

## Master Table Creation SQL

```sql
CREATE TABLE master_pnl AS
SELECT 
    -- Primary identifier
    p.instrument_name as symbol,
    
    -- Position data
    p.position_quantity as open_position,
    p.avg_cost,
    p.total_realized_pnl,
    p.unrealized_pnl as pnl_live,
    p.is_option,
    p.option_strike,
    
    -- Spot risk prices (from JSON)
    json_extract(sr.raw_data, '$.bid') as bid,
    json_extract(sr.raw_data, '$.ask') as ask,
    COALESCE(json_extract(sr.raw_data, '$.adjtheor'), sr.midpoint_price) as price,
    
    -- Market prices
    CASE 
        WHEN p.is_option = 0 THEN mp_fut.current_price
        ELSE mp_opt.current_price
    END as px_last,
    
    -- Risk metrics
    CASE 
        WHEN p.is_option = 0 THEN 63
        ELSE sc.delta_F
    END as dv01,
    
    -- Greeks (only those that exist)
    sc.delta_F, sc.delta_y, sc.gamma_F, sc.gamma_y,
    sc.speed_F, sc.theta_F, sc.vega_price, sc.vega_y,
    sc.implied_vol,
    
    -- Metadata
    sr.bloomberg_symbol as spot_risk_symbol,
    sc.calculation_status as greek_calc_status

FROM positions p
LEFT JOIN spot_risk.spot_risk_raw sr 
    ON p.instrument_name = sr.bloomberg_symbol
LEFT JOIN spot_risk.spot_risk_calculated sc 
    ON sr.id = sc.raw_id
LEFT JOIN market_prices.futures_prices mp_fut
    ON p.instrument_name = mp_fut.symbol AND p.is_option = 0
LEFT JOIN market_prices.options_prices mp_opt
    ON p.instrument_name = mp_opt.symbol AND p.is_option = 1
```

## Common Data Issues

### 1. Missing Option Data
- **Symptom**: Options have NULL spot risk data
- **Cause**: Spot risk CSV files don't contain those option series
- **Example**: 3MN5P, VBYN25P3, TYWN25P4 series often missing

### 2. Empty Market Prices
- **Symptom**: px_last and px_settle are NULL
- **Cause**: Market price tables not populated
- **Solution**: Run market price file watcher with appropriate CSV files

### 3. Symbol Translation Failures
- **Location**: `lib/trading/actant/spot_risk/symbol_translator.py`
- **Format Issue**: Uses dots instead of colons (e.g., "XCME.ZN2.11JUL25.110.C")
- **Success Rate**: ~98.5% after fixes

### 4. vtexp Mapping
- **Source**: `data/input/vtexp/` directory
- **Format**: Most recent `vtexp_YYYYMMDD_HHMMSS.csv` file
- **Required For**: Greek calculations on options

## File Processing Order

1. **Trade Processing**: CSV → TradePreprocessor → positions table
2. **Spot Risk Processing**: CSV → SpotRiskGreekCalculator → spot_risk tables
3. **Market Prices**: CSV → PriceProcessor → market_prices tables
4. **Master Table**: Combines all three after processing

## Key Scripts

- `scripts/rebuild_master_pnl_table.py` - Creates the master table
- `scripts/fix_option_classification.py` - Fixes is_option field
- `scripts/check_database_status.py` - Verifies data population
- `scripts/force_full_repopulation.py` - Reprocesses all source files

## Testing the Implementation

1. Check positions exist: 
   ```sql
   SELECT COUNT(*) FROM positions;
   ```

2. Verify spot risk data:
   ```sql
   SELECT COUNT(*) FROM spot_risk_raw WHERE bloomberg_symbol IS NOT NULL;
   ```

3. Check Greek calculations:
   ```sql
   SELECT COUNT(*) FROM spot_risk_calculated WHERE calculation_status = 'success';
   ```

4. Validate master table:
   ```sql
   SELECT 
       SUM(CASE WHEN spot_risk_symbol IS NOT NULL THEN 1 ELSE 0 END) as with_spot_risk,
       SUM(CASE WHEN delta_f IS NOT NULL THEN 1 ELSE 0 END) as with_greeks
   FROM master_pnl;
   ```

## Implementation Checklist

- [ ] Ensure positions table is populated with correct is_option values
- [ ] Verify spot risk data contains required symbols
- [ ] Check vtexp mappings are available
- [ ] Create master table with proper JSON extraction
- [ ] Handle missing columns (speed_y, theta_y don't exist)
- [ ] Test joins on bloomberg_symbol format
- [ ] Implement DV01 logic (63 for futures, delta_F for options) 