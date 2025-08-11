# Greek Configuration Guide

This document explains how to configure which Greeks are calculated in the spot risk watcher for performance optimization.

## Overview

The Greek configuration system allows you to selectively enable/disable Greek calculations to improve performance. By default, only essential Greeks are calculated.

## Default Configuration

The following Greeks are enabled by default:
- **delta_F, delta_y** - First-order price sensitivity
- **gamma_F, gamma_y** - Second-order price sensitivity
- **speed_F, speed_y** - Third-order price sensitivity (gamma change rate)
- **theta_F** - Time decay
- **vega_y** - Volatility sensitivity (required for positions aggregator)

The following Greeks are disabled by default for performance:
- **vega_price** - Price volatility sensitivity
- **volga_price** - Vega convexity
- **vanna_F_price** - Delta-vega cross sensitivity
- **charm_F** - Delta decay
- **color_F** - Gamma decay
- **ultima** - Vomma convexity
- **zomma** - Gamma-vega cross sensitivity

## Configuration Methods

### 1. Environment Variable

Set the `SPOT_RISK_GREEKS_ENABLED` environment variable with a comma-separated list of Greeks:

```bash
# Windows PowerShell
$env:SPOT_RISK_GREEKS_ENABLED = "delta_F,delta_y,gamma_F,gamma_y,theta_F,speed_F,vega_y"

# Linux/Mac
export SPOT_RISK_GREEKS_ENABLED="delta_F,delta_y,gamma_F,gamma_y,theta_F,speed_F,vega_y"
```

### 2. Programmatic Configuration

```python
from lib.trading.actant.spot_risk.greek_config import GreekConfiguration
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator

# Custom configuration
config = GreekConfiguration({
    'delta_F': True,
    'delta_y': True,
    'gamma_F': True,
    'gamma_y': True,
    'theta_F': True,
    'speed_F': True,
    'vega_y': True,
    # All others will be False
})

# Use with calculator
calculator = SpotRiskGreekCalculator(greek_config=config)
```

## Performance Impact

Based on testing with 20 options:
- **Full Greeks (15 enabled)**: ~0.43 seconds
- **Minimal Greeks (7 enabled)**: ~0.17 seconds
- **Performance improvement**: ~60%

## Important Notes

1. **Required Greeks**: The following Greeks are required for the positions aggregator and will be automatically enabled:
   - delta_y, gamma_y, speed_y, theta_F, vega_y

2. **Derived Greeks**: `speed_y` is calculated from `speed_F`, so enabling `speed_F` automatically provides `speed_y`.

3. **Backward Compatibility**: All existing code handles missing Greeks gracefully. Disabled Greeks are set to NaN in DataFrames and NULL in databases.

4. **Aggregation**: The `calculate_aggregates()` method only aggregates enabled Greeks, setting disabled ones to NaN in aggregate rows.

## Monitoring Configuration

The spot risk watcher logs the active Greek configuration on startup:

```
Greek configuration initialized: 8 Greeks enabled
Enabled Greeks: delta_F, delta_y, gamma_F, gamma_y, speed_F, speed_y, theta_F, vega_y
```

## Example: Production Configuration

For production use with focus on essential risk metrics:

```bash
# Enable only critical Greeks for risk management
$env:SPOT_RISK_GREEKS_ENABLED = "delta_F,delta_y,gamma_F,gamma_y,theta_F,speed_F,vega_y"
```

For comprehensive Greek analysis (e.g., research/backtesting):

```bash
# Enable all Greeks
$env:SPOT_RISK_GREEKS_ENABLED = "delta_F,delta_y,gamma_F,gamma_y,vega_price,vega_y,theta_F,volga_price,vanna_F_price,charm_F,speed_F,color_F,ultima,zomma"
```

## Troubleshooting

1. **Missing Greeks in Output**: Check that the Greek is enabled in configuration.

2. **Positions Aggregator Issues**: Ensure required Greeks (delta_y, gamma_y, speed_y, theta_F, vega_y) are enabled.

3. **Performance Not Improved**: Verify configuration is loaded by checking logs for "Greek configuration initialized" message.