# Active Context

## Current Focus: FULLPNL Automation & TYU5 Migration Planning

### Date: November 2024

#### FULLPNL Automation Documentation
- **Created**: `docs/fullpnl_automation_prompt.md` - Comprehensive guide for automating FULLPNL table building
- **Updated**: Added reference to `docs/pnl_data_structure_mapping.md` as authoritative source
- **Key Point**: The automation design must follow the master P&L table schema in pnl_data_structure_mapping.md

#### TYU5 Migration Analysis
- **Created**: `docs/tyu5_migration_analysis_prompt.md` - Deep analysis prompt for migrating tyu5_pnl system
- **Challenge**: Two parallel P&L systems exist:
  1. TradePreprocessor (simple FIFO) → feeds SQLite positions table
  2. TYU5 P&L (sophisticated with Greeks) → outputs to Excel only
- **Goal**: Integrate TYU5 to feed positions database while preserving advanced features

#### Key Integration Considerations
1. **Symbol Format**: Need unified approach (Bloomberg standard)
2. **Data Model**: TYU5 has richer model (lot tracking, attribution)
3. **Calculations**: Must preserve Bachelier model and Greek calculations
4. **Database Schema**: May need enhancement for advanced features

### Previous Work (Preserved for Context)

## Current Status (Updated)

### vtexp Mapping Fixed - Simplified Approach
- **Issue**: Complex symbol conversion was failing for 90% of options
- **Root Cause**: Trying to convert between different symbol formats was error-prone
- **Solution**: Match by expiry date only (e.g., "21JUL25")
- **Changes Made**:
  1. Simplified vtexp_mapper.py to extract and match by expiry date
  2. All options with same expiry date share same vtexp value
  3. Works for all product types (ZN, VY, WY variants)
- **Result**: 100% mapping success rate in testing

### Symbol Translation Fixed
- **Issue**: Colon notation in strikes (e.g., 110:75) not recognized
- **Solution**: Updated regex pattern and strike conversion logic
- **Result**: All symbols now translate correctly

### vtexp Pipeline Status

### Date: July 16, 2025

Successfully integrated TYU5 P&L calculation engine with UIKitXv2 data stores. The entire pipeline is now working end-to-end with automatic Excel generation and dashboard display.

### Critical Fixes Applied (July 16, 2025):

1. **Data Reprocessing Fix (3:15 PM)**:
   - **Issue**: Tracking tables weren't being dropped
   - **Fix**: Updated DataReprocessor to drop `trade_processing_tracker`, `file_processing_log`, and `price_file_tracker`
   - **Result**: Clean reprocessing now works properly

2. **Auto-Trigger Fix (3:18 PM)**:
   - **Issue**: `'TYU5Service' object has no attribute 'run_calculation'`
   - **Fix**: Changed method call from `run_calculation()` to `calculate_pnl()`
   - **Result**: TYU5 automatically triggers after trade processing

3. **Dashboard Display Fix (3:20 PM)**:
   - **Issue**: Tabs showed empty even though Excel data was being read
   - **Fix**: Removed `.render()` call in callbacks - Tabs component handles rendering
   - **Result**: Dashboard now displays all Excel sheets correctly

4. **File Detection Fix (3:35 PM)**:
   - **Issue**: New Excel files weren't being detected
   - **Fix**: TYU5ExcelReader now always checks for latest file instead of caching
   - **Result**: Dashboard updates when new trades create new Excel files

### Working Integration Details:
- **Package Structure**: lib/trading/pnl_integration/ completely separate from pnl_calculator
- **TYU5 Adapter**: Successfully queries and transforms data:
  - Fixed: Uses single market_prices table (not separate futures/options tables)
  - Fixed: Maps columns correctly (Symbol, Current_Price, Prior_Close)
  - Symbol mapping: TY → TYU5 for futures, options already in correct format
- **TYU5 Service**: Orchestrates calculations with Excel output working
- **Test Results**: ✅ Successfully generated tyu5_pnl_all_20250716_115316.xlsx

### Architecture:
```
[CSV Files] → [Database] → [TYU5 Adapter] → [TYU5 Engine] → [Excel Output]
                   ↓
            - cto_trades table (13 trades loaded)
            - market_prices table (248 prices loaded)
```

### Output Validation:
- Excel file contains 5 sheets: Summary, Positions, Trades, Risk_Matrix, Position_Breakdown
- Positions calculated correctly (e.g., VBYN25C2 options with various strikes)
- All P&L values computing (Unrealized, Daily, Total)

### Fixed Issues (July 16, 2025):
1. ✅ Options Price Storage - Fixed date parsing (M/D/YYYY) and moneyness (ITM/OTM) conversion
2. ✅ Trade Type Detection - Now properly identifies CALL/PUT options from symbol patterns
3. ✅ Processing Success - Only reports success if all records processed without errors
4. ✅ All 250 options prices now stored correctly (vs only 4 before)

### Completed Tasks (July 16, 2025 - Phase 2):
1. ✅ Dashboard Integration - P&L tab displays TYU5 Excel data with 6 summary cards and 4 data tables
2. ✅ Auto-refresh - Dashboard updates every 5 seconds (reduced from 30s for <10s latency)
3. ✅ Automatic TYU5 Trigger - TradePreprocessor now triggers TYU5 after processing trades
4. ✅ UI Polish - DataTables now show all rows without pagination, fit to width

### TYU5 Auto-Trigger Integration:
- **Location**: lib/trading/pnl_calculator/trade_preprocessor.py
- **Behavior**: After successful trade processing, automatically runs TYU5 calculation
- **Error Handling**: TYU5 failures logged but don't break trade processing
- **Latency**: <10 seconds from trade processing to dashboard update (5s refresh interval)

### Data Reprocessing Feature (July 16, 2025):
- **UI**: "Drop & Reprocess All Data" button in P&L dashboard (danger styling)
- **Safety**: Requires double-click within 5 seconds to prevent accidents
- **Backend**: lib/trading/pnl_integration/data_reprocessor.py
- **Process**:
  1. Drops all tables (cto_trades, processed_trades, futures_prices, options_prices, market_prices)
  2. Recreates empty tables with schema
  3. Reprocesses all futures prices from CSV files
  4. Reprocesses all options prices from CSV files
  5. Reprocesses all trades (which triggers TYU5 automatically)
- **Feedback**: Real-time status updates showing progress and results
- **Time**: ~5-7 seconds for full reprocessing

### Critical Fix Applied (July 16, 2025 - 3:50 PM):

5. **P&L Dashboard Tab Update Fix**:
   - **Issue**: Dashboard wasn't updating despite Excel files being created and console indicating success
   - **Root Cause**: Callback was returning dbc.Tab components directly, but the wrapped Tabs component expects tuple format
   - **Fix Applied**:
     - Changed callback Output from `"children"` to `"tabs"` property
     - Modified callback to return tuples `(label, content)` instead of dbc.Tab components
     - Removed unnecessary dbc import
   - **Additional Fix (3:55 PM)**: Container objects were not JSON serializable
     - Added `.render()` call to Container objects before passing to Tabs component
     - Now returns rendered Dash components instead of BaseComponent instances
   - **Final Fix (4:15 PM)**: DataTables inside dynamically created tabs weren't updating
     - **Root Cause**: Dash loses track of dynamically created components inside tabs
     - **Solution**: Create DataTables once in initial layout, update only their data properties
     - Changed from recreating entire tab components to updating DataTable `data` and `columns` properties
     - Each DataTable now has fixed ID and receives updates directly via callback outputs
   - **Result**: Dashboard now correctly displays and updates Excel data in tabs every 5 seconds

### Completed Enhancement (July 16, 2025 - 4:30 PM):

6. **Bachelier P&L Attribution Integration**:
   - **Feature**: Added Greeks-based P&L attribution to TYU5 Excel output
   - **Implementation**:
     - Created `lib/trading/pnl_integration/bachelier_attribution.py` service
     - Enhanced TYU5Service with `enable_attribution` flag (easily revertible)
     - Positions sheet now includes: delta_pnl, gamma_pnl, vega_pnl, theta_pnl, speed_pnl, residual
     - Uses Bachelier model for bond future options with CME expiration calendar
   - **Key Features**:
     - Feature flag allows easy enable/disable (`enable_attribution=True/False`)
     - Graceful degradation if data missing or calculation fails
     - Preserves all existing TYU5 functionality
     - Excel formatting with proper number formats for attribution columns
   - **Testing**: Created `test_tyu5_attribution.py` to verify enhancement

### Critical Fix Applied (July 16, 2025 - 5:30 PM):

7. **P&L Zero Values Fix**:
   - **Issue**: All P&L values showing as 0 despite having trade data
   - **Root Cause**: TYU5 module expects a Market_Prices sheet in Excel input, but none was provided
   - **Fix Applied**:
     - Enhanced TYU5Adapter to query market prices from database tables (futures_prices, options_prices)
     - Added `get_market_prices_for_symbols()` method to match trade symbols with market data
     - Fixed symbol format matching (handles "TYU5 Comdty" → "TYU5" for futures)
     - Modified `prepare_excel_data()` to include market prices from database
   - **Result**: P&L calculations now show proper values for positions with market prices
   
### Critical Fix Applied (July 16, 2025 - 6:15 PM):

8. **Options P&L Symbol Mapping Fix**:
   - **Issue**: Options showing 0 P&L despite having prices in database
   - **Root Cause**: Symbol format mismatch - trades transformed to CME format (VY3N5) but DB has Bloomberg format (VBYN25P3)
   - **Fix Applied**:
     - Added `_convert_cme_to_bloomberg_base()` method for reverse symbol mapping
     - Enhanced market price lookup to convert CME symbols back to Bloomberg for DB queries
     - Maintains proper symbol format throughout the data flow
   - **Result**: Options now show proper P&L values when market prices differ from entry prices
   - **Example**: Two options now show -$1,562.50 P&L each, total options P&L: -$3,125.00

### UI Enhancement Applied (July 16, 2025 - 6:30 PM):

9. **P&L Dashboard DataTable Styling**:
   - **Changes**:
     - Increased container max width to 1800px for better use of screen space
     - Enhanced DataTable styling with larger fonts (14px) and increased padding (12px)
     - Added monospace font for numeric columns for better alignment
     - Improved column formatting: $ prefix for P&L/fees, 6 decimals for prices, no decimals for quantities
     - Added proper header styling with bold text and border separation
     - Maintained horizontal scroll capability while maximizing visible content
   - **Result**: More legible and professional-looking data tables

### Remaining Tasks:
1. ⏳ Fix date-specific filtering (market_prices table missing trade_date column)
2. ⏳ CSV output not supported by TYU5 (Excel only)

---

## Latest Update: Spot Risk SQLite Storage (January 12, 2025)

### Completed Enhancement:
Successfully added SQLite database storage to the spot risk processing pipeline while maintaining existing CSV output.

### Implementation Details:
1. **Created SpotRiskDatabaseService** (`lib/trading/actant/spot_risk/database.py`):
   - Session management for tracking processing runs
   - Raw data storage with JSON serialization
   - Calculated Greeks storage with proper mapping
   - WAL mode for concurrent access
   - Transaction safety and error handling

2. **Modified File Watcher** (`lib/trading/actant/spot_risk/file_watcher.py`):
   - Added database service initialization
   - Create session when processing starts
   - Store raw data after CSV parsing
   - Store calculated Greeks after calculation
   - Update session status on completion/failure
   - CSV output remains unchanged (additive change)

3. **Database Schema** (from existing `schema.sql`):
   - `spot_risk_sessions`: Track processing sessions
   - `spot_risk_raw`: Store original data with JSON
   - `spot_risk_calculated`: Store calculated Greeks
   - Proper indexes for performance

### Testing:
- Created test script: `scripts/test_spot_risk_db.py`
- Database location: `data/output/spot_risk/spot_risk.db`
- Successfully creates sessions and stores data

### Key Benefits:
- Historical data retention for analysis
- Efficient querying vs CSV scanning
- Session tracking for audit trail
- Foundation for future UI enhancements
- No impact on existing CSV functionality 