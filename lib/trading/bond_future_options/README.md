# Bond Future Options Pricing Library

A comprehensive library for pricing bond future options using the Bachelier (normal distribution) model, with support for full Greek calculations and multiple model versions.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Code                          │
│         (Your application, dashboard, scripts)          │
└────────────────────┬───────────────────────────────────┘
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────────┐
│            GreekCalculatorAPI (Facade)                  │
│         Simple, high-level interface                    │
└────────────────────┬───────────────────────────────────┘
                     │ Delegates to
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ModelFactory                               │
│         Creates model instances                         │
└────────────────────┬───────────────────────────────────┘
                     │ Creates
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Model Implementation (e.g., BachelierV1)        │
│         Implements OptionModelInterface                 │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Simplest Usage - High-Level API

```python
from lib.trading.bond_future_options import GreekCalculatorAPI

# Create API instance
api = GreekCalculatorAPI()

# Single option
result = api.analyze({
    'F': 110.75,            # Future price
    'K': 110.5,             # Strike price
    'T': 0.05,              # Time to expiry (years)
    'market_price': 0.359375,  # Market price (decimal)
    'option_type': 'put'    # 'put' or 'call'
})

print(f"Implied Vol: {result['volatility']:.2f}")
print(f"Delta: {result['greeks']['delta_y']:.2f}")

# Batch processing
options = [
    {'F': 110.75, 'K': 110.5, 'T': 0.05, 'market_price': 0.359375},
    {'F': 110.75, 'K': 111.0, 'T': 0.05, 'market_price': 0.453125},
]
results = api.analyze(options)
```

### Direct API Functions (Legacy Support)

```python
from lib.trading.bond_future_options import calculate_implied_volatility, calculate_greeks

# Calculate implied volatility
vol = calculate_implied_volatility(
    F=110.75, K=110.5, T=0.05, 
    market_price=0.359375,
    future_dv01=0.063  # Optional parameters
)

# Calculate Greeks
greeks = calculate_greeks(
    F=110.75, K=110.5, T=0.05,
    volatility=vol
)
```

### Model Selection (Future-Proof)

```python
# Use specific model version
result = api.analyze(option_data, model='bachelier_v1')

# Custom model parameters
result = api.analyze(
    option_data,
    model_params={'future_dv01': 0.08, 'future_convexity': 0.003}
)
```

## File Descriptions

### Core Files

- **`pricing_engine.py`** - Core BondFutureOption class with Bachelier pricing formulas
- **`bachelier.py`** - Pure Bachelier model mathematical implementation
- **`analysis.py`** - Newton-Raphson solver and high-level analysis functions

### API Layer

- **`api.py`** - Direct API functions with all safeguards (implied vol, Greeks, batch)
- **`greek_calculator_api.py`** - High-level facade for simple usage (**RECOMMENDED**)
- **`option_model_interface.py`** - Protocol defining standard model interface

### Factory/Models

- **`model_factory.py`** - Factory for creating model instances by name
- **`models/bachelier_v1.py`** - Current Bachelier implementation (v1.0)

### Greek Calculations

- **`bachelier_greek.py`** - Analytical Greek calculations and profile generation
- **`numerical_greeks.py`** - Finite difference methods (validation only)
- **`greek_validator.py`** - Greek validation and PnL attribution tools

## Greeks Calculated

All Greeks are calculated analytically using the Bachelier model:

- **delta_F** - Price delta (∂V/∂F)
- **delta_y** - Yield delta (∂V/∂y) - scaled by 1000
- **gamma_y** - Yield gamma (∂²V/∂y²) - scaled by 1000
- **vega_y** - Yield vega (∂V/∂σ_y) - scaled by 1000
- **theta_F** - Price theta (∂V/∂t) - daily, scaled by 1000
- **volga_price** - Volatility gamma (∂²V/∂σ²) - scaled by 1000
- **vanna_F_price** - Cross derivative (∂²V/∂F∂σ) - scaled by 1000
- **charm_F** - Delta decay (∂²V/∂F∂t) - scaled by 1000
- **speed_F** - Gamma derivative (∂³V/∂F³) - scaled by 1000
- **color_F** - Gamma decay (∂³V/∂F²∂t) - scaled by 1000
- **ultima** - Vomma derivative (∂³V/∂σ³) - scaled by 1000
- **zomma** - Gamma sensitivity to vol (∂³V/∂F²∂σ) - scaled by 1000

## Key Parameters

### Default Bond Future Parameters
- **future_dv01**: 0.063 (10-year Treasury note typical)
- **future_convexity**: 0.002404
- **yield_level**: 0.05

### Solver Parameters
- **tolerance**: 1e-6 (convergence criterion)
- **max_iterations**: 100
- **min_price_safeguard**: 1/64 (deep OTM protection)
- **max_implied_vol**: 1000

## Error Handling

All functions include comprehensive error handling:

```python
result = api.analyze(option_data)

if result['success']:
    print(f"Vol: {result['volatility']}")
else:
    print(f"Error: {result['error_message']}")
```

Common errors:
- Arbitrage violations (price < 95% intrinsic value)
- Convergence failures
- Price below minimum safeguard
- Volatility outside bounds

## Advanced Usage

### Creating Models Directly

```python
from lib.trading.bond_future_options import ModelFactory

# Create model with custom parameters
model = ModelFactory.create_model(
    'bachelier_v1',
    future_dv01=0.08,
    future_convexity=0.003
)

# Use model directly
vol = model.calculate_implied_vol(F=110.75, K=110.5, T=0.05, market_price=0.359375)
greeks = model.calculate_greeks(F=110.75, K=110.5, T=0.05, volatility=vol)
```

### Price Conversions

```python
from lib.trading.bond_future_options import convert_price_to_64ths, convert_64ths_to_price

# Convert decimal to 64ths
price_64ths = convert_price_to_64ths(0.359375)  # Returns 23.0

# Convert 64ths to decimal
price_decimal = convert_64ths_to_price(23.0)    # Returns 0.359375
```

## Example: Complete Workflow

```python
from lib.trading.bond_future_options import GreekCalculatorAPI

# Initialize
api = GreekCalculatorAPI()

# Option data
option = {
    'F': 110.7890625,       # 110 + 25.25/32
    'K': 110.75,            # 110 + 24/32
    'T': 0.018650794,       # 4.7/252
    'market_price': 0.359375,  # 23/64
    'option_type': 'put'
}

# Analyze
result = api.analyze(option)

# Display results
if result['success']:
    print(f"Implied Volatility: {result['volatility']:.2f}")
    print(f"Model Version: {result['model_version']}")
    print("\nGreeks:")
    for name, value in result['greeks'].items():
        print(f"  {name}: {value:.4f}")
else:
    print(f"Calculation failed: {result['error_message']}")
```

## Testing

Run tests to verify functionality:

```bash
# Test API alignment
python tests/bond_future_options/test_api_alignment.py

# Test factory/facade
python tests/bond_future_options/test_factory_facade.py
```

## Future Model Versions

To add a new model version:

1. Create a class implementing `OptionModelInterface`
2. Register it with the factory
3. Use it via the API:

```python
# Future usage
result = api.analyze(option_data, model='bachelier_v2')
``` 