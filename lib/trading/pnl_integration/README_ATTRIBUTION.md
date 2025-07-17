# Bachelier P&L Attribution Enhancement

## Overview

This enhancement adds Greeks-based P&L attribution to TYU5 Excel output using the Bachelier model for bond future options. The attribution breaks down option P&L into components: delta, gamma, vega, theta, and speed effects.

## Features

### New Columns in Positions Sheet

When attribution is enabled, the following columns are added to the Positions sheet:

- **delta_pnl**: P&L from futures price movement (linear)
- **gamma_pnl**: P&L from futures price movement (non-linear)
- **vega_pnl**: P&L from implied volatility changes
- **theta_pnl**: P&L from time decay
- **speed_pnl**: P&L from third-order price effects
- **residual**: Unexplained P&L (actual - predicted)
- **total_attributed_pnl**: Sum of all attribution components
- **implied_vol_current**: Current implied volatility
- **implied_vol_prior**: Prior implied volatility
- **attribution_calculated**: Whether attribution was successful (Yes/No)

## Usage

### Enable Attribution (Default)

```python
from lib.trading.pnl_integration import TYU5Service

# Attribution is enabled by default
service = TYU5Service()
output_file = service.calculate_pnl()
```

### Disable Attribution

```python
# To disable attribution (reverts to original behavior)
service = TYU5Service(enable_attribution=False)
output_file = service.calculate_pnl()
```

### Requirements

1. **Expiration Calendar**: The file `lib/trading/pnl/tyu5_pnl/core/ExpirationCalendar.csv` must be present
2. **Market Prices**: Both current and prior prices must be available for options and underlying futures
3. **Option Positions**: Attribution only applies to options (futures positions show zeros)

## How It Works

1. After TYU5 completes its calculation and creates the Excel file
2. The service reads the Positions and Market_Prices sheets
3. For each option position:
   - Calculates time to expiry using CME calendar
   - Computes implied volatilities (current and prior)
   - Calculates Greeks using prior market state
   - Decomposes P&L into attribution components
4. Enhances the Positions sheet with attribution columns
5. Preserves all other sheets unchanged

## Error Handling

- If attribution fails for any position, that row shows zeros
- If the expiration calendar is missing, attribution is skipped
- If market prices are incomplete, affected positions show no attribution
- The original TYU5 calculation always completes regardless of attribution errors

## Performance

- Adds approximately 1-2 seconds to calculation time
- Scales linearly with number of option positions
- No impact when `enable_attribution=False`

## Testing

Run the test script to verify attribution:

```bash
python test_tyu5_attribution.py
```

This will:
1. Run TYU5 with attribution enabled
2. Verify attribution columns are present
3. Display sample attribution values
4. Test with attribution disabled to ensure clean reversion 