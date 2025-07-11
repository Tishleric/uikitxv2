# Active Context

This file tracks the current focus and next steps for the UIKitXv2 project.

## Current State (Phase 11: Observatory & Robustness)

### Completed Tasks
- ✅ Observatory dashboard with real-time monitoring
- ✅ Decorator-based performance tracking (@monitor)
- ✅ SQLite-backed logging with flowTrace table
- ✅ UI components wrapper library with consistent theming
- ✅ Actant EOD/SOD processing modules
- ✅ TT REST API integration for ladder functionality
- ✅ Scenario Ladder with live/demo mode toggle
- ✅ Actant PnL dashboard with Greeks calculation
- ✅ Spot Risk dashboard with Greek profiles visualization
- ✅ Improved ATM detection logic for Spot Risk graphs
- ✅ Greek profile pre-computation for performance optimization

### Latest Changes (2024-12-21)

#### Spot Risk Greek Profile Pre-computation
Added asynchronous Greek profile pre-computation to improve graph rendering performance:
- **Implementation**: Greek profiles are automatically computed and saved to CSV when data is loaded
- **Storage Format**: Profiles saved as `greek_profiles_YYYYMMDD_HHMMSS.csv` with columns:
  - expiry, strike, greek_name, value, atm_strike, sigma, tau, future_price
- **Caching**: `generate_greek_profiles_by_expiry()` now checks for cached profiles first
- **Greeks Included**: delta, gamma, vega, theta, volga, vanna, charm, speed, color, ultima, zomma
- **Performance**: Eliminates on-demand computation delays during graph rendering
- **Files Modified**:
  - `apps/dashboards/spot_risk/controller.py` - Added methods:
    - `save_greek_profiles_to_csv()` - Save computed profiles
    - `load_greek_profiles_from_csv()` - Load cached profiles
    - `pre_compute_greek_profiles()` - Compute all standard Greeks
  - Modified `load_csv_data()` to trigger pre-computation
  - Modified `generate_greek_profiles_by_expiry()` to use cache

#### Spot Risk ATM Plotting Fix (Surgical Change)
Fixed the ATM line plotting to always use the rounded future price:
- **Problem**: ATM line was showing at 111.25 (only available strike) instead of 110.75 (rounded future)
- **Solution**: Always return rounded future price as ATM, regardless of available strikes
- **Result**: ATM line now consistent at 110.75 across all expiries

#### Spot Risk Graph Generation Fix
Fixed critical issue where Greek profile graphs weren't generating:
- **Problem**: Future price was searched within each expiry group, but futures might not share the same expiry as options
- **Solution**: Find future price globally from entire dataset before grouping by expiry
- **Implementation**:
  - `generate_greek_profiles_by_expiry()` now finds global future price first
  - Passes this global price to `_find_atm_strike_for_expiry()` for each expiry
  - Added validation to skip expiries with no valid strikes
- **Result**: All expiries now use consistent ATM detection based on the underlying future price

#### Spot Risk ATM Detection Update
Modified the at-the-money (ATM) strike detection logic in the Spot Risk dashboard:
- **Old Behavior**: Used Python's `round()` function which implements banker's rounding (round half to even)
- **New Behavior**: Uses standard rounding to nearest 0.25 increment for treasury bond pricing convention
- **Implementation**: Changed from `round(future_price * 4) / 4` to `int(future_price * 4 + 0.5) / 4`
- **Rounding Behavior**:
  - 110.000 to 110.124 → 110.00
  - 110.125 to 110.374 → 110.25  
  - 110.375 to 110.624 → 110.50
  - 110.625 to 110.874 → 110.75
  - 110.875 to 110.999 → 111.00
- **Files Modified**:
  - `apps/dashboards/spot_risk/controller.py` - Updated both occurrences of the rounding logic
  - `tests/actant_spot_risk/test_atm_detection.py` - Created comprehensive tests
- **Result**: ATM detection now follows treasury bond market conventions

### Next Steps
1. Continue testing Greek profile pre-computation with various data sets
2. Add performance metrics to track cache hit rates
3. Consider adding profile invalidation logic if model parameters change
4. Monitor file system usage for profile CSV files

## Next Priority Tasks

1. **Integration Testing Suite**
   - Create automated tests for all dashboard entry points
   - Add integration tests for data flow between modules
   - Ensure import system remains stable

2. **Documentation Updates**
   - Update inline documentation to reflect new package structure
   - Create API documentation for key modules
   - Update README with current architecture

3. **Performance Optimization**
   - Profile dashboard startup times
   - Optimize Greek calculation performance
   - Implement caching for expensive operations

4. **Error Handling Improvements**
   - Add better error recovery in data processing
   - Improve user-facing error messages
   - Add retry logic for external API calls

## Known Issues

1. **Main App Linter Errors**: Various import resolution warnings in `apps/dashboards/main/app.py`
2. **Type Checking**: Several type inference issues in pandas operations
3. **Performance**: Greek calculations can be slow for large datasets

## Tech Debt

1. **Test Coverage**: Need comprehensive test suite for new observatory features
2. **Documentation**: Some modules lack proper docstrings
3. **Code Duplication**: Some Greek calculation logic is duplicated across modules

## Architecture Notes

- All dashboards now follow MVC pattern with clear separation
- Monitoring via @monitor decorator captures performance metrics
- Observatory dashboard provides real-time system visibility
- Component library ensures UI consistency across all dashboards