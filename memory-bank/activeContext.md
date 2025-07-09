# Active Context

## Last Updated: 2025-01-07

## Current Focus: Spot Risk Integration
Successfully implemented Greek calculator with robust implied volatility solver for spot risk positions.

### Key Achievements
1. **Parser Implementation** ✅
   - Parses Actant CSV with mixed futures/options
   - Normalizes columns and numeric values
   - Intelligent sorting (futures first, then by expiry/strike)

2. **Time to Expiry Calculation** ✅
   - Integrated bachelier.py logic
   - CME expiry conventions (VY/WY at 14:00, ZN at 16:30)
   - Business year fractions calculated correctly

3. **Greek Calculator with Robust Solver** ✅
   - Fixed convergence issues in Newton-Raphson solver
   - Added iteration limits (100-200 max)
   - Better initial guesses based on moneyness
   - Bounds checking (0.1 to 1000 volatility)
   - Looser tolerance (1e-6) for practical convergence
   - Zero derivative checks prevent division by zero
   - Minimum price safeguards for deep OTM options
   - Successfully calculates all Greeks for 50 options in ~0.5s

### Next Steps
1. Create data service layer with caching and filtering
2. Add 'Spot Risk Monitor' tab to main dashboard
3. Implement DataTable with all positions and Greeks
4. Add filtering controls
5. Create summary cards for total position and net Greeks
6. Implement file watcher for auto-updates
7. Create comprehensive test suite

### Technical Details
- Using bond_future_options API with safeguards
- Default DV01=63.0, convexity=0.0042 for ZN futures  
- Model-View-Controller separation maintained
- All Greek calculations include full suite: delta_F/y, gamma_F/y, vega_price/y, theta_F, volga, vanna, charm, speed, color, ultima, zomma

---

## Previous Focus: Component Factory Implementation ✅ COMPLETED

Successfully implemented a backwards-compatible Dash component factory as requested by CTO. The factory provides sensible defaults for all components while maintaining 100% backwards compatibility with existing code.

### What Was Created
- **`lib/components/factory/`** - New optional factory module
- **`component_factory.py`** - Main factory class with creation methods for all components
- **`defaults.py`** - Default configurations (empty data, page_size=10, etc.)
- **`templates.py`** - Convenience methods including:
  - `create_datatable_in_grid()` - CTO's specific request for DataTable in Grid
  - `create_form_grid()` - Form layout helper
  - `create_dashboard_layout()` - Dashboard structure helper

### Key Features
- **100% Backwards Compatible**: No changes to existing component files
- **Optional Usage**: Factory is completely opt-in, existing code unchanged
- **Sensible Defaults**: All components get appropriate default values
- **Theme Injection**: Automatic theme application to all factory-created components
- **Dynamic Population**: Empty DataTables in Grids can be populated via callbacks
- **Identical Components**: Factory creates same instances as direct instantiation

### Tested & Verified
- All existing imports continue to work
- Direct component creation unchanged
- Factory creates identical component instances
- Dynamic Grid+DataTable population works perfectly
- Comprehensive test suite created

### Example Usage
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

---

## Previous Focus: Scenario Ladder Standalone Package ✅ COMPLETED

Successfully created a standalone package for the scenario ladder application with all necessary dependencies. The package can be shared as a self-contained folder requiring minimal setup.

### What Was Created
- **`scenario_ladder_standalone/`** - Complete standalone package
- **Modified Imports** - Changed to use `lib.` prefix for included libraries  
- **Adjusted Paths** - Updated project_root calculation for standalone context
- **Comprehensive Documentation** - README.md with installation, configuration, and usage instructions
- **Minimal Dependencies** - requirements.txt with only essential packages

### Note for Second Pass
Monitor decorators were left in place but can be removed if needed. The package includes:
- All necessary component files (Button, DataTable, Grid)
- Trading modules (price formatter, CSV utilities, TT API)
- Data files (mock orders, sample SOD)
- Complete file structure documentation

---

## Previous Focus: AWS Cloud Deployment - Phase 1
- **Full plan location**: `infra/aws-cloud-development-plan.md`
- Starting Phase 1: Data Pipeline (S3 + Lambda + Redis/DynamoDB)
- Market data flow: Actant → S3 → Lambda → Redis/DynamoDB → Dashboard
- TT working orders: TT API → Lambda (scheduled) → S3/Redis

### Phase 1 Prerequisites (Manual Steps Required):
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

### Phase 1 Tasks:
- [ ] Create 3 S3 buckets (actant-dev, tt-dev, monitoring-dev)
- [ ] Deploy Lambda functions (Actant processor, TT snapshot)
- [ ] Setup MemoryDB Redis cluster (13GB)
- [ ] Create DynamoDB tables (5 tables)
- [ ] Configure Secrets Manager entries
- [ ] Implement Lambda code
- [ ] End-to-end testing

---

## Previous Focus (Completed)
- Greek Analysis numerical calculations removed (January 9, 2025)
- Commented out all numerical (finite difference) calculations and displays
- Greek profile graphs now show only analytical (Bachelier model) results
- Greek profile tables show only analytical column
- Taylor error analysis shows only analytical methods (no Numerical + Cross)
- Previous updates: Input formats changed to decimal/years, Taylor errors as basis points