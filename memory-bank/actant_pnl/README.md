# Actant PnL Analysis Dashboard

A comprehensive dashboard for comparing option pricing methods: Actant software output vs Taylor Series approximations.

## 🎯 Project Overview

This project was created to analyze and visualize the accuracy of Taylor Series expansions in approximating option prices compared to Actant's proprietary pricing software. The dashboard allows traders and quants to:

- **Compare Pricing Methods**: Side-by-side analysis of Actant vs Taylor Series (TS0 and TS-0.25) 
- **Visualize PnL Differences**: Interactive graphs and tables showing pricing discrepancies
- **Analyze Multiple Expirations**: Support for different option expiration dates
- **Real-time Data Integration**: Parse CSV files exported from Actant software

## 🏗️ Architecture & Implementation Journey

### Phase 1: Excel Formula Extraction & Analysis
**Goal**: Understand the Excel-based calculations and extract formulas for Python implementation.

**Key Files**:
- `excel_formula_extractor.py` - Extracts formulas from Excel workbook using openpyxl
- `formula_documentation.md` - Complete mapping of 475+ Excel formulas 
- `formula_analysis_summary.md` - High-level summary of key calculation patterns
- `formula_mappings.json` - Structured formula data for reference

**Key Learnings**:
- Excel's Taylor Series formulas: `=ATM_PRICE + DELTA*(SHOCK_DIFF) + 0.5*GAMMA*(SHOCK_DIFF)^2`
- Two approaches: TS0 (from ATM) and TS-0.25 (from neighboring point)
- Critical reference points: Column Q (ATM), specific rows for Greeks data

### Phase 2: CSV Data Pipeline
**Goal**: Create robust parsing for Actant CSV exports with proper shock unit conversion.

**Key Files**:
- `csv_parser.py` - Core parsing logic with ActantCSVParser, ActantFileMonitor, ActantDataFile
- `pnl_calculations.py` - OptionGreeks dataclass and Taylor Series calculations  
- `data_formatter.py` - Format data for display components
- `test_csv_parser.py` - Validation scripts for parsing logic

**Critical Discovery**: 
- **Shock Unit Conversion**: 0.25 shock units = 4 basis points (not 16 as initially assumed)
- **Formula**: `shocks * 4.0` converts Actant shock units to basis points
- **ATM Detection**: Find index where shock ≈ 0 for proper PnL reference point

**Key Learnings**:
- CSV structure: Expiration column groups different contract expirations
- 'w/o first' rows should be filtered out (contain zero data)
- Proper data validation prevents downstream calculation errors

### Phase 3: Frontend Dashboard Implementation
**Goal**: Build interactive dashboard using wrapped UIKitXv2 components.

**Key Files**:
- `pnl_dashboard.py` - Main dashboard application with PnLDashboard class
- `test_dashboard.py` - Frontend component testing
- `run_demo.py` - Easy demo launcher
- `phase3_implementation.md` - Documentation of frontend approach
- `phase3_error_fix.md` - Critical fix documentation

**Major Technical Issue Encountered**:
```python
# ❌ WRONG: Using wrapper objects directly
return Container(children=[...])

# ✅ CORRECT: Must call .render() method  
return Container(children=[...]).render()
```

**Root Cause**: UIKitXv2 wrapped components are wrapper classes that require `.render()` to return actual Dash components.

**Components Fixed**:
- Container, Grid, Button, DataTable, Graph, Loading, ListBox
- All component creation methods updated to call `.render()`
- Updated deprecated `app.run_server()` to `app.run()`

### Phase 4: Data Integration & Real-time Functionality  
**Goal**: Connect frontend to real CSV data with accurate calculations.

**Key Files**:
- `debug_data_pipeline.py` - Step-by-step pipeline debugging
- `verify_data_integration.py` - End-to-end integration testing
- `final_dashboard_test.py` - Comprehensive functionality validation

**Final Integration Issues Resolved**:
1. **Path Resolution**: Changed relative paths to absolute paths using `Path().resolve()`
2. **Initial State**: Set proper default expiration instead of None
3. **Data Loading Verification**: Added comprehensive error checking and logging

## 📁 File Reference Guide

### Core Application Files
| File | Purpose | Key Functions |
|------|---------|---------------|
| `pnl_dashboard.py` | Main Dash application | PnLDashboard class, layout creation, callbacks |
| `csv_parser.py` | Parse Actant CSV files | ActantCSVParser, file monitoring, data validation |
| `pnl_calculations.py` | Taylor Series calculations | OptionGreeks dataclass, TaylorSeriesPricer, PnLCalculator |
| `data_formatter.py` | Format data for display | Excel-style DataFrames, graph preparation |

### Data Files
| File | Purpose | Notes |
|------|---------|-------|
| `GE_XCME.ZN_20250610_103938.csv` | Sample Actant export | 196 rows, 28 columns, multiple expirations |
| `actantpnl.xlsx` | Reference Excel workbook | Contains original formulas and analysis structure |

### Testing & Validation
| File | Purpose | Focus Area |
|------|---------|------------|
| `test_csv_parser.py` | CSV parsing validation | Data loading, Greeks extraction |
| `test_dashboard.py` | Frontend component testing | Import validation, component rendering |
| `debug_data_pipeline.py` | Step-by-step debugging | Data flow verification |
| `verify_data_integration.py` | End-to-end testing | Complete pipeline validation |
| `final_dashboard_test.py` | Comprehensive testing | Web server, data integration |

### Documentation & Analysis  
| File | Purpose | Content |
|------|---------|---------|
| `formula_documentation.md` | Complete Excel formula mapping | 1,094 lines, 475+ formulas |
| `formula_analysis_summary.md` | High-level formula patterns | Key calculation methods |
| `phase3_implementation.md` | Frontend development log | Component architecture, patterns |
| `phase3_error_fix.md` | Critical fix documentation | .render() method requirement |

### Utility Scripts
| File | Purpose | Usage |
|------|---------|-------|
| `run_demo.py` | Launch dashboard demo | `python run_demo.py` |
| `quick_test.py` | Fast functionality check | Validates core features |
| `test_excel_read.py` | Excel file validation | Basic openpyxl testing |

## 🔧 Technical Implementation Details

### Data Pipeline Flow
```
CSV File → ActantCSVParser → OptionGreeks → PnLCalculator → Dashboard Display
```

### Key Calculations
1. **Shock Conversion**: `shock_bp = shock_units * 4.0`
2. **Taylor Series (TS0)**: `price = atm_price + delta*shock_diff + 0.5*gamma*shock_diff²`
3. **Taylor Series (TS-0.25)**: Uses neighboring point as expansion center
4. **PnL Calculation**: `pnl = current_price - atm_price`

### Dashboard Features
- **Toggle Controls**: Graph/Table view, Call/Put options
- **Expiration Selection**: ListBox with Actant EOD tab styling
- **Real-time Updates**: Reactive Dash callbacks
- **Dark Theme**: Consistent with UIKitXv2 "Black Cat Dark" palette

## 🎓 Key Learnings & Mistakes

### 1. Component Wrapper Pattern
**Mistake**: Directly using wrapped component objects in Dash layout
**Learning**: Always call `.render()` method on UIKitXv2 wrapped components
**Impact**: Dashboard failed to load until fixed

### 2. Shock Unit Conversion
**Mistake**: Initially assumed 1 shock = 16 basis points  
**Learning**: Correct conversion is 0.25 shock = 4 basis points
**Impact**: All PnL calculations were wrong until corrected

### 3. Data Structure Assumptions
**Mistake**: Assumed simple array structures in CSV
**Learning**: Actant CSV has complex multi-expiration structure with filtering needs
**Impact**: Required sophisticated parsing logic

### 4. Path Resolution Issues
**Mistake**: Using relative paths that failed in different execution contexts
**Learning**: Use `Path().resolve()` for robust absolute path handling
**Impact**: File loading failures in production environment

### 5. Initial State Management
**Mistake**: Setting default values to None instead of valid selections
**Learning**: Always provide valid defaults for better UX
**Impact**: Empty dropdowns and confusing initial state

## 🚀 Usage Instructions

### Quick Start
```bash
cd NEW
python run_demo.py
# Open http://localhost:8050
```

### Manual Launch
```bash
cd NEW  
python pnl_dashboard.py
# Dashboard available at http://localhost:8050
```

### Testing
```bash
# Test data pipeline
python debug_data_pipeline.py

# Test frontend components  
python test_dashboard.py

# Comprehensive validation
python verify_data_integration.py
```

## 📊 Current Capabilities

✅ **Fully Functional**:
- Real CSV data loading and parsing
- Accurate Taylor Series calculations matching Excel
- Interactive dashboard with toggle controls  
- Multiple expiration support
- Graph and table visualizations
- Dark theme integration

🔄 **Ready for Enhancement**:
- File monitoring for live updates
- Additional pricing methods
- Export functionality
- Advanced filtering options

## 🔮 Future Enhancements

1. **Real-time File Monitoring**: Auto-refresh when new CSV files arrive
2. **Additional Taylor Series Methods**: Higher-order expansions, different reference points
3. **Performance Analytics**: Aggregate error metrics, trending analysis
4. **Export Capabilities**: Save analysis results to Excel/PDF
5. **Advanced Filtering**: Date ranges, strike filters, volatility bands

---

This project demonstrates a complete data analysis pipeline from Excel formula extraction through interactive dashboard deployment, with robust error handling and comprehensive testing throughout. 