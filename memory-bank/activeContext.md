# Active Context

## Current Focus: Spot Risk Y-Space Greek Profiles

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
   - Added `model_params` Container with concise inline display
   - Placed between `header_section` and `control_panel`

2. **Callback** (`callbacks.py`):
   - Added `update_model_parameters` callback
   - Extracts future price from futures row
   - Uses actual calculator values: DV01=63.0, Convexity=0.0042
   - Calculates average implied vol per expiry for options with positions
- Filters by options (itype C or P) with non-zero positions
- Displays as decimal values (e.g., 0.7550) matching table format
- Label clearly indicates it's an average ("Avg Implied Vol")

### Display Format
```
Model Parameters: Future Price: 110.7500 • DV01: 63.0 • Convexity: 0.0042 • Avg Implied Vol: 11JUL25: 0.7550, 14JUL25: 0.7425
```

---

## Put Option Delta Fix (2025-01-13 Update)

### Problem Identified
- Put option Greek profiles were showing positive delta values (same as calls)
- Expected: Put deltas should be negative (-1 to 0 in F-space, ~-63 to 0 in Y-space)

### Root Cause
- `bachelier_greek.py` generates Greeks using analytical formulas for **call options only**
- No put adjustments were being applied to the generated profiles

### Solution Implemented
1. **New Method**: `_adjust_greeks_for_put()` in SpotRiskController
   - Applies put-call parity: `delta_put = delta_call - 1`
   - Other Greeks remain mostly unchanged

2. **Applied in Two Paths**:
   - **Fresh Generation**: After `generate_greek_profiles_data()` call (~line 875)
   - **Cached Profiles**: After loading cached Greeks (~line 630)

3. **Option Type Determination**:
   - Checks `itype` counts per expiry
   - If only 'P' (no 'C') → apply put adjustments
   - Otherwise → treat as calls (default)

### Technical Implementation
- Put adjustments applied to **F-space Greeks** before any Y-space transformation
- Option type determined once and reused for Y-space transformation
- Debug logging tracks adjustments: `[DEBUG PUT ADJUSTMENT]`

### Expected Results
- Put deltas: -1 to 0 in F-space (negative values)
- Put deltas in Y-space: ~-63 to 0 (after DV01 transformation)
- Clear visual distinction between call and put profiles