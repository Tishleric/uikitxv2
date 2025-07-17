# Progress Tracker

## Current Status (July 17, 2025)

### Recent Accomplishments
- ✅ Modified spot risk processing to read pre-calculated vtexp values from CSV files
- ✅ Added `load_vtexp_for_dataframe()` function to replace internal time calculation
- ✅ Updated parser to use vtexp CSV files from `data/input/vtexp/` directory
- ✅ Fixed position display in P&L Dashboard V2 (positions now visible)
- ✅ Integrated SymbolTranslator for proper Actant → Bloomberg mapping
- ✅ Updated get_market_price to use flexible timestamp lookup
- ✅ Verified that VBYN25C2 110.750 Comdty exists in market_prices table

### Active Issues - P&L Dashboard V2 Price Mapping

**Problem**: Options still show no prices despite correct symbol translation
- SymbolTranslator correctly maps XCMEOCADPS20250714N0VY2/110.75 → VBYN25C2 110.750 Comdty
- Price exists in database with px_settle = 0.015625
- But get_market_price returns None due to "#N/A Requesting Data..." values in price files

**Root Causes Identified**:
1. Price CSV files contain invalid data like "#N/A Requesting Data..." which causes float conversion errors
2. save_market_prices doesn't validate data before inserting
3. get_market_price tries to convert these invalid strings to float

**Next Steps**:
1. Update save_market_prices to skip rows with invalid price data
2. Clean existing market_prices table of invalid entries
3. Re-test price mapping with clean data

### Working Components
- Trade file detection and processing (17 positions created)
- Position display in UI with proper formatting
- Futures price mapping (TU shows price 103.17125)
- SymbolTranslator integration
- Database schema and storage layer
- File watchers on 5-second intervals
- Spot risk vtexp loading from pre-calculated CSV files

### Technical Details
- Database: data/output/pnl/pnl_tracker.db
- 3,305 market price records loaded (650 VBYN options)
- Using FIFO methodology for position tracking
- All using wrapped Dash components from lib/components
- Spot risk now reads vtexp from most recent file in data/input/vtexp/

### Key Learning
The price files from Bloomberg can contain invalid data that must be filtered during import. Need robust validation at data ingestion points. 

### July 17, 2025: Closed Position Tracking Implementation
**Status: Complete ✅**

Implemented Option 1 for closed position tracking as requested:

**Changes Made:**
1. **Database Schema Update:**
   - Added `closed_quantity` column to positions table
   - Created migration script `scripts/add_closed_quantity_column.py`
   - Successfully migrated existing database

2. **New Module: ClosedPositionTracker**
   - Created `lib/trading/pnl_calculator/closed_position_tracker.py`
   - Analyzes trade history from cto_trades table
   - Calculates cumulative positions day-by-day
   - Identifies when positions go to zero or flip signs
   - Updates positions table with closed quantities

3. **Controller Integration:**
   - Added `update_closed_positions()` method to PnLController
   - Added `get_positions_with_closed()` method for UI display
   - Integrated ClosedPositionTracker into controller initialization

4. **Test Script:**
   - Created `scripts/test_closed_positions.py` for verification
   - Confirms functionality is working correctly

**Key Features:**
- Tracks closed positions for current trading day
- Handles full closes (position → 0) and sign flips (long → short)
- Maintains closed position data even for fully closed symbols (position = 0)
- Ready for dashboard integration

**Next Steps:**
- Update P&L dashboard to display closed positions column
- Consider future migration to Option 3 (full position history) for historical tracking

## Master P&L Table Implementation (July 17, 2025)

### Phase 1: Symbol Column Creation ✅
**Status: Complete**

Created FULLPNL table in pnl_tracker.db with initial symbol column:

**Table Details:**
- Table name: FULLPNL
- Location: data/output/pnl/pnl_tracker.db
- Structure: symbol (TEXT PRIMARY KEY), created_at (TIMESTAMP)
- Records: 8 symbols from positions table
- All symbols in Bloomberg format (ending with "Comdty")

**Symbols Loaded:**
1. TYU5 Comdty (Future)
2. 3MN5P 110.000 Comdty (Put option)
3. 3MN5P 110.250 Comdty (Put option)
4. TYWN25P4 109.750 Comdty (Put option)
5. TYWN25P4 110.500 Comdty (Put option)
6. VBYN25P3 109.500 Comdty (Put option)
7. VBYN25P3 110.000 Comdty (Put option)
8. VBYN25P3 110.250 Comdty (Put option)

**Scripts Created:**
- `scripts/master_pnl_table/01_create_symbol_table.py` - Creates FULLPNL table
- `scripts/master_pnl_table/inspect_fullpnl.py` - Inspects table contents

**Next Steps:**
- Add open_position column from positions table
- Add bid/ask columns from spot risk data
- Continue building column by column

### Phase 2: Bid/Ask Columns ✅
**Status: Complete**

Added bid and ask columns to FULLPNL table by mapping Bloomberg symbols to Actant format:

**Mapping Logic:**
- Parse Bloomberg symbols (e.g., "VBYN25P3 110.250 Comdty" -> PUT, strike 110.25)
- Parse Actant keys (e.g., "XCME.ZN3.18JUL25.110:25.P" -> PUT, strike 110.25, expiry 18JUL25)
- Match based on:
  - Futures: TYU5 matches SEP25 (September)
  - Options: Match by type (PUT/CALL) and strike
  - Contract codes mapped to expiries (3M->18JUL25, VBY->21JUL25, TWN->23JUL25)

**Results:**
- 5 out of 8 symbols now have bid/ask data
- 4 symbols have both bid and ask (50%)
- 3 symbols still missing data (likely not in spot risk file)

**Scripts Created:**
- `scripts/master_pnl_table/03_add_bid_ask_with_mapping.py` - Maps and populates bid/ask

**Next Steps:**
- Add open_position column from positions table
- Add price columns (px_last, px_settle) from market prices
- Continue building column by column

### Phase 3: Price Column ✅
**Status: Complete**

Added price column to FULLPNL table using spot risk data:

**Price Logic:**
- Primary source: adjtheor column (adjusted theoretical price)
- Fallback: midpoint_price column
- Last resort: Calculate (bid + ask) / 2 if neither available

**Results:**
- 4 out of 8 symbols now have price data (50%)
- All prices came from calculated midpoint (adjtheor was not available)
- Price values match exactly with (bid + ask) / 2 for all populated rows
- Same symbols that have bid/ask also have price

**Current FULLPNL Contents:**
- TYU5 Comdty: bid=110.546875, ask=110.562500, price=110.554688
- 3MN5P 110.250 Comdty: bid=0.015625, ask=0.031250, price=0.023438
- VBYN25P3 110.000 Comdty: bid=0.015625, ask=0.031250, price=0.023438
- VBYN25P3 110.250 Comdty: bid=0.046875, ask=0.062500, price=0.054688

**Scripts Created:**
- `scripts/master_pnl_table/04_add_price.py` - Adds price column with adjtheor/midpoint logic

**Next Steps:**
- Add open_position column from positions table
- Add market price columns (px_last, px_settle) from market_prices database
- Add Greeks columns from spot risk calculated data

### Phase 4: px_last Column ✅
**Status: Complete**

Added px_last column to FULLPNL table from market_prices database:

**Mapping Logic:**
- Futures: Strip " Comdty" suffix and match (TYU5 Comdty → TYU5)
- Options: Match full symbol exactly (3MN5P 110.000 Comdty)
- Source: current_price column from futures_prices and options_prices tables

**Results:**
- 7 out of 8 symbols now have px_last data (87.5%)
- All options found matches in options_prices table
- Future TYU5 found in futures_prices table
- Only TYWN25P4 110.500 Comdty missing (not in market data)

**Price Comparison (where both exist):**
- TYU5: price=110.554688, px_last=110.200000 (diff=-0.354687)
- 3MN5P 110.250: price=0.023438, px_last=0.015625 (diff=-0.007812)
- VBYN25P3 110.000: price=0.023438, px_last=0.015625 (diff=-0.007812)
- VBYN25P3 110.250: price=0.054688, px_last=0.062500 (diff=+0.007812)

**Scripts Created:**
- `scripts/master_pnl_table/05_add_px_last.py` - Adds px_last from market_prices DB

**Next Steps:**
- Add px_settle column from market_prices database (prior_close)
- Add open_position column from positions table
- Add Greeks columns from spot risk calculated data

### Phase 5: px_settle Column ✅
**Status: Complete**

Added px_settle column to FULLPNL table from market_prices database:

**Mapping Logic:**
- Same as px_last: Strip " Comdty" for futures, exact match for options
- Source: prior_close column from futures_prices and options_prices tables  
- **Date Logic Fixed**: px_settle uses prior_close from date T+1 (which represents the close of date T)
- No longer hardcoded - dynamically determines trade dates from market_prices database
- **Bug Fixed**: Initial script was incorrectly detecting all symbols as futures due to faulty string parsing

**Results (final version):**
- 7 out of 8 symbols now have px_settle data (87.5%)
- All symbols except TYWN25P4 110.500 Comdty have prior_close values
- Using dynamic dates: T=2025-07-16, T+1=2025-07-17

**Price Comparisons (px_last vs px_settle):**
- TYU5 Comdty: 110.200 vs 110.200 (diff: 0.000) - flat
- 3MN5P 110.000: 0.000 vs 0.016 (diff: -0.016)
- 3MN5P 110.250: 0.016 vs 0.047 (diff: -0.031)
- TYWN25P4 109.750: 0.016 vs 0.047 (diff: -0.031)
- VBYN25P3 109.500: 0.001 vs 0.001 (diff: 0.000) - flat
- VBYN25P3 110.000: 0.016 vs 0.031 (diff: -0.016)
- VBYN25P3 110.250: 0.063 vs 0.078 (diff: -0.016)

**Scripts Created:**
- `scripts/master_pnl_table/06_add_px_settle.py` - Adds px_settle from prior_close with dynamic dates
- `scripts/master_pnl_table/diagnose_options_prior_close.py` - Diagnostic tool
- `scripts/master_pnl_table/reset_px_settle.py` - Reset utility

**Next Steps:**
- Add open_position column from positions table
- Add Greeks columns from spot risk calculated data

### Phase 6: open_position Column ✅
**Status: Complete**

Added open_position column to FULLPNL table from positions table:

**Mapping Logic:**
- Direct join on symbol: FULLPNL.symbol = positions.instrument_name
- Both tables use Bloomberg format (ending in "Comdty")
- Source: position_quantity column from positions table

**Results:**
- 8 out of 8 symbols have open_position data (100%)
- All positions are non-zero (no closed positions)
- Position breakdown:
  - 7 long positions (positive values)
  - 1 short position (3MN5P 110.250 with -200)
  - Largest position: TYU5 with 2000 contracts

**Position Details:**
- 3MN5P 110.000: 400 (long put)
- 3MN5P 110.250: -200 (short put)
- TYU5: 2000 (long future)
- TYWN25P4 109.750: 200 (long put)
- TYWN25P4 110.500: 2 (long put)
- VBYN25P3 109.500: 400 (long put)
- VBYN25P3 110.000: 200 (long put)
- VBYN25P3 110.250: 300 (long put)

**Scripts Created:**
- `scripts/master_pnl_table/07_add_open_position.py` - Adds position data
- `scripts/master_pnl_table/show_fullpnl_complete.py` - Display utility

**Next Steps:**
- Add Greeks columns from spot risk calculated data

### Phase 7: closed_position Column ✅
**Status: Complete**

Added closed_position column to FULLPNL table from positions table:

**Implementation Details:**
- First ran ClosedPositionTracker.update_closed_positions() to calculate closed quantities
- Then populated FULLPNL from positions.closed_quantity column
- Source: positions.closed_quantity (populated by ClosedPositionTracker)
- Tracks quantities closed during current trading day

**Results:**
- 8 out of 8 symbols have closed_position data (100%)
- All values are 0 (no positions were closed today)
- This is expected if no trades reduced positions to zero or flipped signs

**Technical Notes:**
- ClosedPositionTracker analyzes trade history from cto_trades
- Identifies when cumulative position goes to 0 or changes sign
- Updates positions.closed_quantity for current trading day only

**Scripts Created:**
- `scripts/master_pnl_table/08_add_closed_position.py` - Updates and adds closed position data

**Next Steps:**
- Add Greeks columns from spot risk calculated data

### Phase 8: delta_f Column (First Greek) ✅
**Status: SUCCESS (after switching to SQLite)**

Added delta_f column to FULLPNL table - resolved data quality issues by using SQLite database instead of CSV files.

**Implementation Details:**
- Updated script to use spot_risk SQLite database (`data/output/spot_risk/spot_risk.db`)
- Symbol mapping between Bloomberg (FULLPNL) and spot risk formats
- Futures: Hardcoded delta_f = 63.0
- Options: Retrieved from spot_risk_calculated.delta_F

**Results:**
- 6 out of 8 symbols populated (75%)
- Missing: Strikes 109.5 and 109.75 not in spot risk data (legitimate reason)
- Portfolio Total Delta: 125,866.11

**Scripts Created:**
- `scripts/master_pnl_table/09_add_delta_f.py` - Adds delta_f using SQLite database

### Phase 9: All Other Greeks ✅
**Status: SUCCESS**

Added all remaining Greek columns to FULLPNL table using spot_risk SQLite database.

**Greeks Added:**
- delta_y (Delta w.r.t yield)
- gamma_f (Gamma w.r.t futures) 
- gamma_y (Gamma w.r.t yield)
- speed_f (Speed w.r.t futures)
- theta_f (Theta w.r.t futures)
- vega_f (Vega in price terms)
- vega_y (Vega w.r.t yield)

**Note:** speed_y and theta_y don't exist in the database (removed from spec)

**Results:**
- Same 75% population rate (6 out of 8 symbols)
- Portfolio-Level Greeks:
  - Delta (futures): 125,866.11
  - Delta (yield): -8,435.13
  - Gamma (futures): 324.12
  - Gamma (yield): 3,672.48
  - Speed (futures): 89,852.90
  - Theta (futures): -52.33
  - Vega (price): 385.08
  - Vega (yield): 24,260.14

**Scripts Created:**
- `scripts/master_pnl_table/10_add_all_greeks.py` - Adds all available Greeks

### Phase 10: vtexp Column ✅
**Status: SUCCESS**

Added vtexp (time to expiry) column to FULLPNL table.

**Implementation Details:**
- Initial attempt retrieved incorrect values from raw_data JSON (4.17 years)
- Fixed by mapping Bloomberg symbols to vtexp_mappings table format
- Created symbol mappings: 3MN→18JUL25, VBYN→21JUL25, TYWN→23JUL25
- Futures excluded (no time to expiry concept)

**Results:**
- 7 out of 7 options successfully updated (100%)
- Correct vtexp values now in place:
  - 3MN5P options: 0.050 years (18.2 days)
  - VBYN25P3 options: 0.041667 years (15.2 days)
  - TYWN25P4 options: 0.041667 years (15.2 days)
- Average: 0.044048 years (16.1 days)

**Scripts Created:**
- `scripts/master_pnl_table/11_add_vtexp.py` - Initial vtexp column
- `scripts/master_pnl_table/12_fix_vtexp_values.py` - Fixes vtexp with correct mappings

**Next Steps:**
- Add expiry_date column
- Add P&L calculation columns
- Add DV01 column
- Add LIFO P&L tracking

## Known Issues & TODO
 