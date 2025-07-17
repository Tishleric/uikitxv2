# Automating the FULLPNL Master P&L Table Building Process

## Context
You are tasked with designing and implementing an automated system for building and maintaining the FULLPNL master P&L table. This table consolidates data from multiple sources to provide a comprehensive view of positions, market prices, and risk metrics (Greeks) for a trading portfolio.

**IMPORTANT**: The authoritative reference for this implementation is `docs/pnl_data_structure_mapping.md`. This document contains:
- Complete Master P&L Table Schema with all 30+ columns
- Detailed data source mappings and join strategies  
- Implementation phases with prerequisites
- Known issues and quirks

Please review that document thoroughly before proceeding. The information below supplements but does not replace the comprehensive mapping.

## Current Manual Process Overview

### Data Flow Architecture
```
1. Trade Data → TradeFileWatcher → TradePreprocessor → positions table
2. Market Prices → PriceFileWatcher → market_prices tables  
3. Spot Risk Data → SpotRiskWatcher → SpotRiskGreekCalculator → spot_risk.db
4. All sources → FULLPNL table (manual scripts)
```

### Key Databases and Tables
- **P&L Database**: `data/output/pnl/pnl_tracker.db`
  - `positions` table: Current positions and P&L
  - `cto_trades` table: Processed trades
  - `FULLPNL` table: Master consolidated view
  
- **Spot Risk Database**: `data/output/spot_risk/spot_risk.db`
  - `spot_risk_raw`: Raw instrument data
  - `spot_risk_calculated`: Calculated Greeks
  - `vtexp_mappings`: Time to expiry mappings
  - `spot_risk_sessions`: Processing sessions

- **Market Prices Database**: `data/output/market_prices/market_prices.db`
  - `futures_prices`: Future price data
  - `options_prices`: Option price data

## Current Implementation Scripts

### Phase-by-Phase Scripts Created
1. **Symbol Column**: `scripts/master_pnl_table/01_create_symbol_table.py`
   - Creates FULLPNL table with symbols from positions table
   
2. **Bid/Ask**: `scripts/master_pnl_table/03_add_bid_ask_with_mapping.py`
   - Maps Bloomberg to Actant format for spot risk data lookup
   
3. **Price**: `scripts/master_pnl_table/04_add_price.py`
   - Uses hierarchy: adjtheor → midpoint_price → (bid+ask)/2
   
4. **px_last**: `scripts/master_pnl_table/05_add_px_last.py`
   - From market_prices database (2pm snapshot)
   
5. **px_settle**: `scripts/master_pnl_table/06_add_px_settle.py`
   - Prior close from market_prices (T+1 logic)
   
6. **open_position**: `scripts/master_pnl_table/07_add_open_position.py`
   - Direct from positions.position_quantity
   
7. **closed_position**: `scripts/master_pnl_table/08_add_closed_position.py`
   - Requires ClosedPositionTracker execution first
   
8. **delta_f**: `scripts/master_pnl_table/09_add_delta_f.py`
   - Uses SQLite database (not CSV) for data quality
   - Futures hardcoded to 63.0
   
9. **All Greeks**: `scripts/master_pnl_table/10_add_all_greeks.py`
   - Adds: delta_y, gamma_f, gamma_y, speed_f, theta_f, vega_f, vega_y
   - Note: speed_y and theta_y don't exist in database
   
10. **vtexp**: `scripts/master_pnl_table/11_add_vtexp.py` + `12_fix_vtexp_values.py`
    - Initial script pulled wrong values from raw_data JSON
    - Fix script maps to vtexp_mappings table

## Critical Learnings and Quirks

### Symbol Format Challenges
1. **Multiple formats in use**:
   - Bloomberg: "VBYN25P3 110.250 Comdty"
   - Actant: "XCME.ZN3.18JUL25.110:25.P"
   - vtexp_mappings: "XCME.ZN2.18JUL25" or "XCME.ZN.JUL25"

2. **Contract code mappings discovered**:
   ```
   3M/3MN → 18JUL25
   VBY/VBYN → 21JUL25  
   TWN/TYWN → 23JUL25
   ```

3. **Strike price format differences**:
   - Bloomberg: 110.250
   - Actant: 110:25 (colon notation)

### Data Quality Issues Encountered
1. **Spot Risk CSV files**: 
   - Many rows with `greek_calc_success=True` but NaN values
   - Placeholder values of 20.0 instead of calculated Greeks
   - Solution: Use SQLite database instead

2. **vtexp values**:
   - raw_data JSON contains incorrect values (4.165972 years)
   - vtexp_mappings table has correct values (0.04-0.05 years)
   - Requires complex symbol mapping

3. **Missing data patterns**:
   - Strikes 109.5 and 109.75 consistently missing from spot risk
   - 75% data availability is typical

### Date/Time Logic
1. **px_last**: Current price from 2pm CDT snapshot
2. **px_settle**: Prior close - requires T+1 date logic
3. **Data freshness**: Different sources update at different frequencies

## Automation Design Recommendations

### Core Automation Components

1. **Master Orchestrator Class**
   ```python
   class FULLPNLBuilder:
       def __init__(self):
           self.pnl_db_path = "data/output/pnl/pnl_tracker.db"
           self.spot_risk_db_path = "data/output/spot_risk/spot_risk.db"
           self.market_prices_db_path = "data/output/market_prices/market_prices.db"
           
       def build_or_update(self):
           # Check if FULLPNL exists, create if not
           # For each column, check if needs update
           # Run appropriate population logic
   ```

2. **Symbol Mapping Service**
   ```python
   class SymbolMapper:
       def bloomberg_to_actant(self, bloomberg_symbol: str) -> str
       def bloomberg_to_vtexp_key(self, bloomberg_symbol: str) -> str
       def extract_contract_info(self, symbol: str) -> dict
   ```

3. **Data Source Interfaces**
   ```python
   class SpotRiskDataSource:
       def get_bid_ask(self, symbol_info: dict) -> tuple
       def get_greeks(self, symbol_info: dict) -> dict
       def get_vtexp(self, symbol_info: dict) -> float
   ```

4. **Update Strategies**
   - **Full rebuild**: Recreate entire table
   - **Incremental update**: Update only changed rows
   - **Column refresh**: Update specific columns

### Trigger Mechanisms

1. **Time-based triggers**:
   - After market close for px_settle
   - After 2pm for px_last
   - When new spot risk session completes

2. **Event-based triggers**:
   - New trades processed → update positions
   - New spot risk file → update Greeks
   - Market prices updated → update px_last/px_settle

3. **Dependency tracking**:
   - closed_position depends on ClosedPositionTracker
   - Greeks depend on spot_risk_calculated
   - vtexp depends on vtexp_mappings

### Error Handling and Monitoring

1. **Data validation**:
   - Greeks should be within reasonable ranges
   - vtexp should be < 1 year for near-term options
   - Positions should match between tables

2. **Missing data handling**:
   - Log symbols without spot risk data
   - Use NULL for genuinely missing data
   - Track data coverage metrics

3. **Audit trail**:
   - Log each update with timestamp
   - Track data sources used
   - Record any mapping failures

## Implementation Approach

### Phase 1: Consolidate Existing Scripts
1. Extract common functions (symbol parsing, database connections)
2. Create unified configuration for paths and mappings
3. Build reusable data source adapters

### Phase 2: Build Core Framework
1. Implement SymbolMapper with all format conversions
2. Create DataSourceManager for unified data access
3. Build FULLPNLBuilder orchestrator

### Phase 3: Add Automation
1. Implement trigger system
2. Add incremental update logic
3. Create monitoring dashboard

### Phase 4: Production Hardening
1. Add comprehensive error handling
2. Implement retry logic for transient failures
3. Create alerting for data quality issues

## Configuration Requirements

```yaml
# config/fullpnl_config.yaml
databases:
  pnl: "data/output/pnl/pnl_tracker.db"
  spot_risk: "data/output/spot_risk/spot_risk.db"
  market_prices: "data/output/market_prices/market_prices.db"

symbol_mappings:
  contract_to_expiry:
    "3M": "18JUL25"
    "3MN": "18JUL25"
    "VBY": "21JUL25"
    "VBYN": "21JUL25"
    "TWN": "23JUL25"
    "TYWN": "23JUL25"

greeks:
  futures_delta: 63.0
  available_columns:
    - delta_f
    - delta_y
    - gamma_f
    - gamma_y
    - speed_f
    - theta_f
    - vega_f
    - vega_y

update_schedule:
  px_last: "14:00"  # 2pm CDT
  px_settle: "16:30"  # After 4pm close
  spot_risk: "continuous"  # When new files arrive
```

## Testing Strategy

1. **Unit tests** for each component:
   - Symbol mapping accuracy
   - Date logic for px_settle
   - Greek calculations

2. **Integration tests**:
   - Full table build from empty
   - Incremental updates
   - Missing data scenarios

3. **Data quality tests**:
   - Greeks within expected ranges
   - vtexp values reasonable
   - Position reconciliation

## Monitoring and Alerting

1. **Key metrics to track**:
   - Data completeness percentage
   - Update latency
   - Mapping failure rate
   - Greek calculation success rate

2. **Alerts to implement**:
   - Missing critical data sources
   - Unusual Greek values
   - Position mismatches
   - Update failures

## Critical Prerequisites

### Position Data Population
**Note**: The positions table is currently populated via the TradePreprocessor pipeline. However, there is a more sophisticated P&L tracking system at `lib/trading/pnl/tyu5_pnl/` that includes:
- Advanced FIFO position tracking with short position support
- P&L attribution using Bachelier model
- Greek calculations and risk matrices

This tyu5_pnl system is not currently wired to populate the SQLite positions database. A separate migration effort is needed to:
1. Integrate tyu5_pnl with the existing database schema
2. Preserve its advanced calculation capabilities
3. Ensure symbol format compatibility

See `docs/tyu5_migration_analysis_prompt.md` for detailed migration strategy.

## Next Steps

1. Review and think critically to validate the automation design
2. Prioritize which components to build first
3. Determine acceptable data staleness for each column
4. Define SLAs for update frequency
5. Plan rollout strategy (parallel run with manual process)

## Additional Considerations

- **Performance**: With proper indexing, updates should complete in seconds
- **Scalability**: Design should handle 1000s of positions
- **Maintainability**: Clear separation of concerns for easy updates
- **Auditability**: Complete trail of data lineage and transformations

This automation will transform a manual 10-script process into a reliable, monitored system that maintains data quality while reducing operational overhead. 