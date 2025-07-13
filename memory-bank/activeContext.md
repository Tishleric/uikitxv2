# Active Context

## Current State (2025-02-10)
✅ **COMPLETE**: Both P&L dashboards are now integrated and working

### Latest Changes
1. **P&L Tracking Added as New Tab**:
   - Fixed Container serialization issue by adding `.render()` to `create_pnl_content()`
   - Added "PnL Tracking" button to sidebar navigation
   - Updated navigation callback to handle the new tab
   - Added case in `get_page_content()` for "pnl-tracking"
   - Registered P&L Tracking callbacks at app startup

2. **SQL Column Name Fixes** (Latest):
   - Fixed `get_daily_pnl_summary()`: Changed `instrument` to `instrument_name`
   - Fixed `get_trade_history()`: Changed `market_trade_time` to `trade_timestamp`
   - Added `side` column to trade history SELECT query
   - Updated side display logic to use actual DB value ('B'/'S')

3. **Both Dashboards Working**:
   - **Actant PnL**: Original Taylor Series comparison dashboard
   - **PnL Tracking**: New FIFO P&L tracking system with real-time updates

### Technical Summary
- Fixed the `TypeError: Object of type Container is not JSON serializable` by ensuring `create_pnl_content()` returns rendered Dash components
- Navigation system updated with all necessary outputs/inputs for the new tab
- Both dashboards work independently without conflicts
- File watchers and real-time updates functioning correctly

---

## Previous Work
✅ **COMPLETE**: P&L Dashboard Integration (Phase 2)

## What We Just Completed
1. **P&L Controller** (`lib/trading/pnl_calculator/controller.py`)
   - Thin wrapper around P&L service
   - Handles UI data transformation
   - Manages file watchers
   - Formats P&L as dollar amounts with red/green coloring

2. **Dashboard Views** (`apps/dashboards/pnl/`)
   - Created modular P&L dashboard with tabs:
     - Positions: Current positions with P&L breakdown
     - Daily P&L: Historical daily summaries
     - P&L Chart: Cumulative and daily P&L visualization
     - Trade History: Recent trades with details
   - Used wrapped components throughout
   - Applied consistent theming

3. **Dashboard Integration**
   - Added P&L tab to main dashboard navigation
   - Registered callbacks at app startup
   - 20-second auto-refresh interval
   - Manual refresh button
   - File watcher status indicators

## Test Results
- All imports working correctly
- Controller initializes successfully
- Summary stats retrieving properly
- File watchers starting correctly
- Database tables created as expected

## Next Immediate Steps
1. Test with real trade CSV data
2. Verify market price integration
3. Check UI responsiveness and performance
4. Document any edge cases found

## Key Technical Decisions Made
- Used per-date calculator instances for daily isolation
- Direct SQL queries in controller for efficiency
- 20-second refresh to balance responsiveness and performance
- Wrapper callbacks to match file watcher signature
- Storage instance shared between service and controller

---

## Spot Risk Y-Space Greek Profiles

### Problem Addressed (2025-01-13)
- Greek profile graphs were showing F-space values regardless of the selected space toggle
- Y-axis values didn't match expected ranges (e.g., delta should be 0-63 in Y-space with DV01=0.063)

### Solution Implemented
1. Added `_transform_greeks_to_y_space()` method to SpotRiskController
   - Applies proper Y-space transformations from pricing_engine.py
   - Includes 1000x scaling from analysis.py
   - Handles all Greek types with correct formulas

2. Modified `generate_greek_profiles_by_expiry()` to apply transformations when `greek_space == 'y'`
   - Retrieves DV01 and convexity from calculator
   - Determines option type per expiry for accurate delta handling
   - Transforms Greeks after profile generation but before display

### Technical Details
- DV01 converted from basis points (63.0) to decimal (0.063) for calculations
- All Y-space Greeks scaled by 1000 after transformation
- Transformation formulas match pricing_engine.py exactly:
  - delta_y = delta_F * DV01
  - gamma_y = gamma_F * (DV01)² + delta_F * convexity
  - vega_y = vega_F * DV01
  - theta_y = theta_F (scaled only)
  - Other Greeks follow similar patterns

### Verification  
- Test script confirmed delta ranges 12.6-50.4 in Y-space (expected 0-63)
- All transformations produce correct magnitudes
- Existing CSV processing pipeline remains unchanged (already correct)

### Current Status: Y-Space Transformation Fixed

#### Problem Identified & Resolved (2025-01-13)
- **Root Cause**: Cached Greek profiles were returned without Y-space transformation
- **Issue**: Early return at line ~648 bypassed transformation logic at line ~860

#### Solution Implemented
Added Y-space transformation to cached profile processing:
1. **Location**: Inside cached profile loop after `filtered_greeks` is populated
2. **Implementation**: Mirrors fresh profile transformation pattern
   - Checks if `greek_space == 'y'`
   - Gets DV01/convexity from calculator
   - Determines option type from expiry data
   - Calls `_transform_greeks_to_y_space()`

#### Code Changes
- **File**: `apps/dashboards/spot_risk/controller.py`
- **Lines Added**: ~15 lines after line 621
- **Pattern**: Reuses exact same transformation logic as fresh profiles

### Expected Results
- Delta in Y-space: 0-63 range (with DV01=0.063)
- Gamma in Y-space: Scaled by DV01² with convexity adjustment
- All Greeks properly transformed when Y-space is selected
- Works for both cached and fresh profile generation

## Next Steps
1. Test Y-space toggle functionality
2. Verify correct value ranges in graphs
3. Remove debug logging once confirmed working

---

## UI Flickering Fix (2025-01-13 Update)

### Problem
- UI was flickering due to file watcher interval checking every 1 second
- Even with proper `PreventUpdate` guards, the frequent interval caused visual flickering

### Solution
- Increased file watcher interval from 1000ms to 5000ms (5 seconds)
- Simple one-line change in `views.py`
- Still responsive enough for position updates while eliminating flickering

### Implementation
- File: `apps/dashboards/spot_risk/views.py`
- Changed: `interval=1000` → `interval=5000` in `spot-risk-file-watcher-interval`
- Result: 5x reduction in callback frequency, smooth UI experience

---

## Model Parameters Display (2025-01-13 Update)

### Feature Added
- Added model parameters display section between header and filters
- Shows: Future Price, DV01, Convexity, and Implied Volatility per expiry group
- Displays actual values used in calculations (Convexity = 0.0042)

### Implementation
1. **View Component** (`views.py`):
   - Added `model_params`