# Bond Future Options Analytics

Production-ready Bachelier model implementation for bond future options Greeks and Taylor series P&L analysis.

## Package Contents
This minimal package contains 8 essential files:
- Core implementation: `pricing_engine.py`, `analysis.py`, `bachelier_greek.py`
- Clean API interface: `api.py`
- Package setup: `__init__.py`, `requirements.txt`
- Documentation: `README.md`, `example_usage.py`

## Quick Start

```python
# Current dashboard usage pattern
from lib.trading.bond_future_options import analyze_bond_future_option_greeks
from lib.trading.bond_future_options.bachelier_greek import generate_greek_profiles_data, generate_taylor_error_data

# Analyze option and get all Greeks
results = analyze_bond_future_option_greeks(
    future_dv01=0.063,
    future_convexity=0.002404,
    F=110.789062,        # Future price
    K=110.75,            # Strike price  
    T=0.0186508,         # Time to expiry (years)
    market_price=0.359375,  # Option price (decimal)
    option_type='put'
)

# Future cleaner API usage
from lib.trading.bond_future_options.api import quick_analysis
analysis = quick_analysis(110.789062, 110.75, 0.0186508, 0.359375)
```

## Core Files

### 1. `pricing_engine.py` (322 lines)
**Core Bachelier model implementation with all Greek calculations**

| Function/Class | Lines | Description |
|---------------|-------|-------------|
| `BondFutureOption` | 15-322 | Main pricing engine class |
| `__init__()` | 27-48 | Initialize with DV01, convexity, yield |
| `price()` | 50-73 | Bachelier option pricing |
| `implied_volatility()` | 75-95 | Newton-Raphson implied vol solver |
| `delta_F()` | 97-106 | Delta w.r.t. future price |
| `delta_y()` | 108-113 | Delta w.r.t. yield |
| `gamma_F()` | 115-124 | Gamma w.r.t. future price |
| `gamma_y()` | 126-131 | Gamma w.r.t. yield (key metric) |
| `vega_price()` | 133-142 | Vega w.r.t. price volatility |
| `vega_y()` | 144-149 | Vega w.r.t. yield volatility |
| `theta_F()` | 151-162 | Theta in future price space |
| `volga_price()` | 170-179 | Second-order vega (volga) |
| `vanna_F_price()` | 181-190 | Cross-Greek: delta-vega |
| `charm_F()` | 192-201 | Cross-Greek: delta-theta |
| `speed_F()` | 203-212 | Third-order price Greek |
| `color_F()` | 214-223 | Third-order time Greek |
| `ultima()` | 225-237 | Third-order vol Greek |
| `zomma()` | 239-251 | Cross-Greek: gamma-vega |

### 2. `analysis.py` (178 lines)
**High-level analysis functions used by dashboard**

| Function | Lines | Description |
|----------|-------|-------------|
| `solve_implied_volatility()` | 11-59 | Robust implied vol solver with diagnostics |
| `calculate_all_greeks()` | 61-111 | Calculate complete Greek set (scaled by 1000) |
| `analyze_bond_future_option_greeks()` | 113-178 | **Main dashboard function** - complete analysis |

### 3. `bachelier_greek.py` (335 lines)
**Greek profile and Taylor error analysis**

| Function | Lines | Description |
|----------|-------|-------------|
| `bachelier_price()` | 12-14 | Basic Bachelier formula |
| `analytical_greeks()` | 17-50 | Analytical Greek calculations |
| `numerical_greeks()` | 53-103 | Finite difference Greeks |
| `taylor_expand()` | 132-144 | Taylor series expansion |
| `generate_greek_profiles_data()` | 200-241 | **Dashboard function** - Greek curves |
| `generate_taylor_error_data()` | 244-305 | **Dashboard function** - Taylor accuracy |

### 4. `api.py` (389 lines) 
**Clean API for future use (not yet integrated in dashboard)**

| Function | Lines | Description |
|----------|-------|-------------|
| `calculate_implied_volatility()` | 28-87 | User-friendly vol calculation |
| `calculate_greeks()` | 90-143 | Simple Greek calculation interface |
| `calculate_taylor_pnl()` | 146-209 | Taylor P&L predictions |
| `quick_analysis()` | 212-283 | All-in-one analysis function |
| `process_option_batch()` | 286-359 | Batch processing for multiple options |

### 5. `__init__.py`
**Package initialization - exports key functions for convenient importing**
- Exports `analyze_bond_future_option_greeks` from analysis module
- Provides `BondFutureOption` class from pricing_engine

### 6. `example_usage.py`
**Complete working examples showing both current and future usage patterns**
- Demonstrates current dashboard pattern (what production uses)
- Shows future API pattern (cleaner interface)
- Includes verification that both patterns produce identical results
- Provides batch processing example with multiple strikes

### 7. `requirements.txt`
**Minimal dependencies needed to run the package**
```
numpy>=1.20.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0  # Optional, for visualization
```

## Example: Current Dashboard Pattern

```python
# This is what the dashboard currently does
from lib.trading.bond_future_options import analyze_bond_future_option_greeks
from lib.trading.bond_future_options.bachelier_greek import generate_greek_profiles_data, generate_taylor_error_data

# 1. Full Greek analysis at current point
results = analyze_bond_future_option_greeks(
    future_dv01=0.063,
    future_convexity=0.002404,
    F=110.789062,
    K=110.75,
    T=0.0186508,
    market_price=0.359375,
    option_type='put'
)

print(f"Implied Vol: {results['implied_volatility']:.2f}")
print(f"Delta (Y-space): {results['current_greeks']['delta_y']:.2f}")
print(f"Gamma (Y-space): {results['current_greeks']['gamma_y']:.2f}")

# 2. Generate Greek profiles across price range
profile_data = generate_greek_profiles_data(
    K=110.75,
    sigma=results['implied_volatility'],
    tau=0.0186508,
    F_range=(108, 113)
)

# 3. Generate Taylor approximation error analysis
taylor_data = generate_taylor_error_data(
    K=110.75,
    sigma=results['implied_volatility'],
    tau=0.0186508,
    dF=0.1,      # 10 cent shock
    dSigma=0.01, # 1 vol point shock
    dTau=0.01,   # Time decay
    F_range=(108, 113)
)
```

## Key Greek Definitions

**First Order:**
- `delta_y`: Change in option value per basis point yield change (×1000)
- `gamma_y`: Change in delta per basis point yield change (×1000)
- `vega_y`: Change in option value per yield vol point (×1000)
- `theta_F`: Daily time decay (×1000)

**Second Order:**
- `volga_price`: Convexity of vega
- `vanna_F_price`: Cross-sensitivity of delta to volatility
- `charm_F`: Cross-sensitivity of delta to time

**Third Order:**
- `speed_F`, `color_F`, `ultima`, `zomma`: Higher-order sensitivities

## Dependencies
- numpy, pandas, scipy
- matplotlib (optional, for visualization examples)

## Notes
- All Greeks are scaled by 1000 for display (except delta_F)
- Bachelier model assumes normal distribution (not lognormal)
- Suitable for bond futures where negative prices are theoretically possible
- Time to expiry should be in years (e.g., 7 days = 7/365) 