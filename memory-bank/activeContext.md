# Active Context: Current Development State

## Last Updated: 2025-01-07

### Current Focus: Component Factory Implementation ✅ COMPLETED

Successfully implemented a backwards-compatible Dash component factory as requested by CTO. The factory provides sensible defaults for all components while maintaining 100% backwards compatibility with existing code.

#### What Was Created
- **`lib/components/factory/`** - New optional factory module
- **`component_factory.py`** - Main factory class with creation methods for all components
- **`defaults.py`** - Default configurations (empty data, page_size=10, etc.)
- **`templates.py`** - Convenience methods including:
  - `create_datatable_in_grid()` - CTO's specific request for DataTable in Grid
  - `create_form_grid()` - Form layout helper
  - `create_dashboard_layout()` - Dashboard structure helper

#### Key Features
- **100% Backwards Compatible**: No changes to existing component files
- **Optional Usage**: Factory is completely opt-in, existing code unchanged
- **Sensible Defaults**: All components get appropriate default values
- **Theme Injection**: Automatic theme application to all factory-created components
- **Dynamic Population**: Empty DataTables in Grids can be populated via callbacks
- **Identical Components**: Factory creates same instances as direct instantiation

#### Tested & Verified
- All existing imports continue to work
- Direct component creation unchanged
- Factory creates identical component instances
- Dynamic Grid+DataTable population works perfectly
- Comprehensive test suite created

#### Example Usage
```python
# Old way still works
table = DataTable(id="my-table", data=[], columns=[])

# New factory way (optional)
factory = DashComponentFactory()
table = factory.create_datatable(id="my-table")  # Gets all defaults

# CTO's specific request
grid = factory.create_datatable_in_grid(
    grid_id="dashboard-grid",
    table_id="sales-table",
    grid_width={"xs": 12, "md": 8}
)
```

### Current Focus: Scenario Ladder Standalone Package ✅ COMPLETED

Successfully created a standalone package for the scenario ladder application with all necessary dependencies. The package can be shared as a self-contained folder requiring minimal setup.

#### What Was Created
- **`scenario_ladder_standalone/`** - Complete standalone package
- **Modified Imports** - Changed to use `lib.` prefix for included libraries  
- **Adjusted Paths** - Updated project_root calculation for standalone context
- **Comprehensive Documentation** - README.md with installation, configuration, and usage instructions
- **Minimal Dependencies** - requirements.txt with only essential packages

#### Note for Second Pass
Monitor decorators were left in place but can be removed if needed. The package includes:
- All necessary component files (Button, DataTable, Grid)
- Trading modules (price formatter, CSV utilities, TT API)
- Data files (mock orders, sample SOD)
- Complete file structure documentation

### Previous Focus: AWS Cloud Deployment - Phase 1
- **Full plan location**: `infra/aws-cloud-development-plan.md`
- Starting Phase 1: Data Pipeline (S3 + Lambda + Redis/DynamoDB)
- Market data flow: Actant → S3 → Lambda → Redis/DynamoDB → Dashboard
- TT working orders: TT API → Lambda (scheduled) → S3/Redis

#### Phase 1 Prerequisites (Manual Steps Required):
1. **AWS Account Creation** - https://aws.amazon.com
   - Personal/company credit card required
   - Phone verification required
   - Choose us-east-1 region

2. **IAM Admin User Setup**
   - Create non-root admin user
   - Enable MFA
   - Save access credentials securely

3. **External Service Accounts**:
   - **TT API**: Generate credentials at https://api.tradingtechnologies.com
   - **Slack**: OAuth setup for CloudWatch alerts (optional)
   - **GitHub**: Add AWS credentials as secrets for CI/CD (later)

#### Phase 1 Tasks:
- [ ] Create 3 S3 buckets (actant-dev, tt-dev, monitoring-dev)
- [ ] Deploy Lambda functions (Actant processor, TT snapshot)
- [ ] Setup MemoryDB Redis cluster (13GB)
- [ ] Create DynamoDB tables (5 tables)
- [ ] Configure Secrets Manager entries
- [ ] Implement Lambda code
- [ ] End-to-end testing

### Previous Focus (Completed)
- Greek Analysis numerical calculations removed (January 9, 2025)
- Commented out all numerical (finite difference) calculations and displays
- Greek profile graphs now show only analytical (Bachelier model) results
- Greek profile tables show only analytical column
- Taylor error analysis shows only analytical methods (no Numerical + Cross)
- Previous updates: Input formats changed to decimal/years, Taylor errors as basis points

### Recently Completed Tasks

#### Taylor Approximation Error Display Update (2025-01-07) ✅
- Converted Taylor error display from absolute to percentage values
- Graph Y-axis now shows "Relative Prediction Error (%)" with % suffix on ticks  
- Table values display as percentages (e.g., "1.23%")
- Implemented safe division-by-zero handling
- Updated both graph and table views in Greek Analysis page

#### Fixed Import Path Issue (2025-01-09) ✅
- **Root Cause**: App.py was adding both project root and lib/ to sys.path
- **Problem**: Importing `from trading.pricing_monkey` vs `from lib.trading.pricing_monkey` created different module objects
- **Solution**: Changed all imports to use `lib.` prefix consistently
- **Result**: Trading functions now properly appear in Observatory with correct process groups

### Recently Completed
- Applied @monitor decorator to all 30 callbacks in app.py
- Added @monitor to 13 strategic functions across trading modules
- Fixed IndentationError in lib/monitoring/decorators/monitor.py line 246
- **Removed all _traced wrapper functions to fix process group assignment issue**
- **Added @monitor directly to setup_logging and shutdown_logging in lib/monitoring/logging/config.py**
- Fixed import paths to use consistent `lib.` prefix

### Active Changes
- All callbacks and strategic functions now properly use @monitor
- Process groups now correctly auto-derive from actual module names (e.g., `lib.trading.pricing_monkey.automation.pm_auto`)
- No legacy decorators remain in the codebase
- Observatory dashboard provides comprehensive visibility with proper process group filtering

### Known Working State
- @monitor decorator working correctly
- Observatory database receiving data
- Process groups properly assigned based on module names
- All trading functions visible in Observatory

### Next Steps
- Restart dashboard to see trading functions in Observatory with proper process groups
- Verify process group filtering buttons work correctly
- Monitor performance of key trading workflows

### Caveats
- No process groups explicitly declared per user request - auto-derived from module names
- All functions using vanilla @monitor() with no parameters
- Observatory is recording detailed trace data for all monitored functions

# Active Context: Strategic Monitor Decorator Application

## Current Status: ✅ COMPLETED (2025-01-06)
**Successfully applied @monitor() decorator to key functions across trading and lib modules**

### Phase 1: Main App.py Migration ✅ COMPLETED
1. **Legacy Decorator Removal** ✅
   - Replaced all @TraceCloser, @TraceTime, @TraceCpu, @TraceMemory decorators with @monitor()
   - Updated 30 callbacks to use @monitor() decorator
   - Updated 6 non-callback functions (logging functions, performance query functions)
   - Removed legacy decorator imports from line 65
   - Updated comment on line 6766 to reference @monitor instead of legacy decorators

2. **Verification** ✅
   - Created and ran analysis scripts to ensure 100% coverage
   - Confirmed all 30 callbacks now have @monitor() decorator
   - Verified no legacy decorators remain in the codebase
   - Cleaned up temporary analysis scripts

### Phase 2: Strategic Function Monitoring ✅ COMPLETED

**Trading Module Functions Applied:**
1. **Pricing Monkey** (`lib/trading/pricing_monkey/`)
   - ✅ `run_pm_automation()` - automation/pm_auto.py - Multi-option workflow orchestrator
   - ✅ `get_market_movement_data_df()` - processors/movement.py - Market data collection  
   - ✅ `get_market_movement_data()` - processors/movement.py - Main retrieval function

2. **Actant EOD** (`lib/trading/actant/eod/`)
   - ✅ `load_data_from_json()` - data_service.py - JSON to SQLite loader
   - ✅ `load_pricing_monkey_data()` - data_service.py - PM data integration

3. **Actant PnL** (`lib/trading/actant/pnl/`)
   - ✅ `parse_actant_csv_to_greeks()` - calculations.py - CSV to OptionGreeks converter
   - ✅ `parse_file()` - parser.py - CSV file parser
   - ✅ `load_latest_data()` - parser.py - Latest file loader

4. **Scenario Ladder** (`lib/trading/ladder/`)
   - ✅ `decimal_to_tt_bond_format()` - price_formatter.py - Price formatting
   - ✅ `csv_to_sqlite_table()` - csv_to_sqlite.py - Data persistence

5. **TT API** (`lib/trading/tt_api/`)
   - ✅ `create_request_id()` - utils.py - API request formatting
   - ✅ `get_token()` - token_manager.py - Auth token retrieval
   - ✅ `_acquire_token()` - token_manager.py - Token acquisition

### Benefits Achieved:
- Enhanced visibility into critical trading workflows
- Minimal performance impact (vanilla @monitor() without process groups)
- Strategic placement for maximum observability
- All functions now tracked in Observatory dashboard
- Fixed indentation error in monitor.py (line 246)

### Previous Work - Enhancement Plan (YAGNI Approach):

#### Phase 1: Core Improvements 🚧 IN PROGRESS
1. **Scrollable Table** ✅ - Fixed pagination (page_size=1000), increased scroll height to 700px, no horizontal scroll
2. **Auto-Refresh** ✅ - Add 5-second interval refresh with timestamp display
3. **Improved Output Naming** ✅ - Enhanced for most cases including navigation functions
4. **Process Group Filtering** ✅ - Joined tables correctly, split process display, persistent state
5. **Duration Column** ✅ - Added execution time display in milliseconds format

#### Completed Features (January 6, 2025):
- **Table Display**: Shows Process Group and Process (function name) in separate columns
- **No Horizontal Scroll**: Fixed column widths using style_data_conditional
- **Exception Column**: Added back to display exception information
- **Last Refresh Timestamp**: Shows under subtitle
- **Filter State Persistence**: Filters maintain state across auto-refresh
- **No Button Flashing**: Removed auto-refresh trigger from button creation
- **Navigation Output Naming**: Improved handling for navigation functions:
  - Content array → "content"
  - Active page → "active_page"
  - Style dictionaries → "{nav_name}_style" (e.g., "pricing_monkey_style", "analysis_style")
  - No more generic "result_0", "result_1", etc. for navigation
- **Duration Column**: ✅ Shows execution time in milliseconds with 1 decimal place
  - Added to both main and exception tables
  - Column widths adjusted to prevent horizontal scroll
  - Format: "123.4 ms"

#### Remaining Work:
- Child process visualization (needs detailed planning)
- Expected vs Actual data validation (consulting with CTO)

#### Phase 2: Future Enhancements (After Phase 1)
- Additional performance metrics
- Advanced filtering options

### Technical Details
- SQL queries use JOIN between data_trace and process_trace tables
- Process group extraction handles patterns like __main__.function correctly
- Filter buttons only recreate on manual refresh, not auto-refresh
- Exception handling includes graceful fallbacks for missing data
- Duration formatting shows milliseconds with 1 decimal place

### Previous Status: ✅ COMPLETED (2025-06-23)
**Table view error fixed: Removed invalid page_action parameter, tables now show all rows without pagination**

### Completed Tasks:
1. ✅ **Removed 11 individual Greek graphs** - The original 4x3 grid of individual Greeks has been removed
2. ✅ **Fixed callback errors** - Removed references to non-existent containers in callback
3. ✅ **Greek Profile Analysis remains** - The enhanced Greek profile visualization with all 12 Greeks stays
4. ✅ **Implemented table view for Greek profiles** - All 12 Greek profiles now have table views
5. ✅ **Added table view for Taylor approximation** - Taylor error analysis also has table view
6. ✅ **Proper view toggling** - Graph/Table toggle works correctly with new callback structure
7. ✅ **Fixed Container ID errors** - Added missing id parameters to Container components in table generation
8. ✅ **Removed table pagination** - Tables now show all data rows without pagination
   - Removed sampling logic (was showing every 5th point, now shows all points)  
   - Fixed DataTable error by removing invalid `page_action` parameter
   - Set `page_size=len(table_rows)` to show all rows without pagination
   - Removed fixed height constraints to allow full scrolling
9. ✅ **Hide graphs when table view is active** - Greek profile graphs and Taylor graph are hidden in table view
   - Wrapped Greek Profile Analysis and Taylor sections in new container (acp-greek-profile-graphs-container)
   - Updated toggle callback to control visibility of all three containers
   - Graph view shows: graph container + Greek profile graphs
   - Table view shows: table container only (hides Greek profile graphs)

### Implementation Details

#### View Updates
- Commented out the 11 individual Greek graph containers in the layout
- Updated callback to remove 11 Outputs for non-existent containers  
- Removed code that created empty divs for these graphs
- Dashboard now loads without errors

#### Table View Implementation
- Added new callback `acp_generate_table_view` that generates tables when in table view mode
- Added `profile_data` and `taylor_data` to store_data for table generation
- Tables display the same data as graphs (analytical and numerical values)
- Every 5th data point is shown to keep tables manageable
- Proper formatting with DataTable components in 4x3 grid layout
- Taylor approximation error table included at bottom of table view
- Table/Graph toggle determines which view to show

#### Why Tables Are Valuable
The table view provides complementary functionality to the graphs:
- **Precise Values**: Exact numerical Greek values at specific future prices
- **Side-by-side Comparison**: Easy comparison of analytical vs numerical calculations
- **Data Export Ready**: Table format makes it easy to copy values for further analysis
- **Accessibility**: Better for users who prefer numerical data over visual representations
- **Reference Points**: Clear identification of Greek values at specific price levels

#### Data Flow
1. Main callback calculates all Greek data and stores in `store_data`
2. View toggle callback switches between graph and table containers
3. Table generation callback creates tables when table view is selected
4. Tables use exact same data as graphs with same scaling and adjustments

### Status
The dashboard is now stable and running at http://localhost:8052/
- Greek Analysis page loads without errors
- Greek profile graphs show all 12 Greeks with analytical and numerical values
- Taylor approximation error analysis is displayed
- Table view shows placeholder 4x3 grid

### Original Greek Integration Project Summary
Successfully completed the complete replacement of Greek calculation system with CTO-approved Bachelier implementation from `lib/trading/bond_future_options/bachelier_greek.py`. The main dashboard maintains 100% UI compatibility while now using the new, more comprehensive Greek calculations.

### Final Integration Results

#### Phase 1 - Missing Greeks Implementation ✅
- Added `third_order_greeks()` function to bachelier_greek.py
- Implemented ultima (∂³V/∂σ³) and zomma (∂³V/∂F²∂σ)
- Fixed theta sign convention to be negative (time decay)
- Verified calculations match pricing_engine.py to 1e-8 precision

#### Phase 2 - Core Integration ✅
- Created `_get_all_bachelier_greeks()`

# Active Development Context

## Current State: Bond Future Options API Module Completed

### What We Just Built
1. **Simplified API Module** (`lib/trading/bond_future_options/api.py`):
   - `calculate_implied_volatility()` - Direct volatility calculation from market data
   - `calculate_greeks()` - All Greeks with one function call
   - `calculate_taylor_pnl()` - Taylor series PnL approximation
   - `quick_analysis()` - Complete analysis including risk metrics
   - `process_option_batch()` - CSV batch processing capability
   - Helper functions for price conversions (64ths ↔ decimal)

2. **Example Script** (`scripts/bond_options_csv_example.py`):
   - Demonstrates CSV input/output workflow
   - Shows single option and batch processing
   - Includes sample CSV generation
   - Ready for real-world data integration

3. **Key Design Decisions**:
   - **No changes to existing code** - API wraps existing functionality
   - **Mathematical consistency** - Uses same validated pricing engine
   - **Simple interfaces** - Hide complexity of model instantiation
   - **CSV-friendly** - Designed for easy external data integration

### API Usage Pattern
```python
# Simple one-liner for implied volatility
vol = calculate_implied_volatility(F, K, T, market_price)

# Get all Greeks at once
greeks = calculate_greeks(F, K, T, vol)

# Process CSV files
results = process_option_batch(csv_data)
```

### Next Steps for CSV Integration
The user can now:
1. Read option data from external CSV (F, K, T, market_price)
2. Calculate volatilities and Greeks using the API
3. Extend the CSV with the calculated values
4. Use the enriched data for further analysis/PnL calculations

### Recent Context
- Previously converted Taylor error display to percentage of option price
- Updated Greek Analysis inputs to decimal/year format
- Removed numerical methods from UI, keeping only analytical
- Migrated main dashboard to unified @monitor decorator

## Technical Notes
- API tested and verified: Vol=5.31, Delta=-26.25 for test case
- All functions handle edge cases (zero vol, expired options)
- Batch processing includes error handling per option
- Future DV01 properly integrated for all conversions