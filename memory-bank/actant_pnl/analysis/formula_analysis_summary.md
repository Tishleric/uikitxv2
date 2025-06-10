# Actant PnL Formula Analysis Summary

## Overview
The Excel workbook calculates PnL comparisons between:
1. **Actant** - Direct option pricing software output
2. **TS0** - Taylor Series expansion from the at-the-money (ATM) point
3. **TS-0.25** - Taylor Series expansion from the neighboring -0.25 point

## Data Structure

### Input Data (Rows 1-15)
- Row 1: Headers (strike offsets from -3 to +3 in 0.25 increments)
- Rows 2-15: Option Greeks and prices for XCME.ZN
  - `ab_sDeltaPathCallPct` - Call delta percentage
  - `ab_sDeltaPathPutPct` - Put delta percentage  
  - `ab_sDeltaPathDV01Call` - Call DV01 (dollar value of 01)
  - `ab_sDeltaPathDV01Put` - Put DV01
  - `ab_sGammaPathDV01` - Gamma DV01
  - `ab_VegaDV01` - Vega DV01
  - `ab_Theta` - Theta
  - `ab_F` - Forward price
  - `ab_K` - Strike price
  - `ab_R` - Interest rate
  - `ab_T` - Time to expiry
  - `ab_Vol` - Implied volatility
  - `ab_sCall` - Call price
  - `ab_sPut` - Put price

### Key Formulas

#### 1. Taylor Series from ATM (TS0)
For Calls (Row 20):
```excel
=$Q$20+$Q$4*(X18-$Q$18)+0.5*$Q$6*(X18-$Q$18)*(X18-$Q$18)
```

Python equivalent:
```python
def taylor_series_from_atm(atm_price, atm_delta, atm_gamma, shock, atm_shock=0):
    """
    Calculate option price using 2nd order Taylor series expansion from ATM.
    
    Args:
        atm_price: Option price at ATM
        atm_delta: Delta (DV01) at ATM  
        atm_gamma: Gamma (DV01) at ATM
        shock: Current shock level in basis points
        atm_shock: ATM shock level (typically 0)
    
    Returns:
        Estimated option price
    """
    shock_diff = shock - atm_shock
    return atm_price + atm_delta * shock_diff + 0.5 * atm_gamma * shock_diff**2
```

#### 2. Taylor Series from Neighbor (TS-0.25)
For Calls (Row 21):
```excel
=X14+X4*(Y18-X18)+0.5*X6*(Y18-X18)*(Y18-X18)
```

Python equivalent:
```python
def taylor_series_from_neighbor(neighbor_price, neighbor_delta, neighbor_gamma, 
                               current_shock, neighbor_shock):
    """
    Calculate option price using 2nd order Taylor series from neighboring point.
    
    Args:
        neighbor_price: Option price at neighboring point
        neighbor_delta: Delta (DV01) at neighboring point
        neighbor_gamma: Gamma (DV01) at neighboring point
        current_shock: Current shock level in basis points
        neighbor_shock: Neighboring point shock level
    
    Returns:
        Estimated option price
    """
    shock_diff = current_shock - neighbor_shock
    return neighbor_price + neighbor_delta * shock_diff + 0.5 * neighbor_gamma * shock_diff**2
```

#### 3. PnL Calculations
```excel
# Actant PnL (Row 26/40)
=X19-$Q$19  # Current price - ATM price

# TS0 PnL (Row 27/41)  
=X20-$Q$20  # TS0 price - TS0 ATM price

# TS-0.25 PnL (Row 28/42)
=X21-$Q$21  # TS-0.25 price - TS-0.25 ATM price
```

Python equivalent:
```python
def calculate_pnl(prices_array, atm_index):
    """Calculate PnL relative to ATM position."""
    atm_price = prices_array[atm_index]
    return prices_array - atm_price
```

## Cell Mappings

### Critical Reference Points
- **Column Q (index 16)**: ATM position (shock = 0)
- **Row 18/32**: Shock values in basis points
- **Row 4**: Call Delta DV01 values
- **Row 5**: Put Delta DV01 values  
- **Row 6**: Gamma DV01 values
- **Row 14**: Call prices from Actant
- **Row 15**: Put prices from Actant

### Python Data Structure
```python
@dataclass
class OptionData:
    """Store option data for a single expiration."""
    shocks: np.array  # Strike offsets in basis points
    call_prices: np.array  # Actant call prices
    put_prices: np.array  # Actant put prices
    call_delta_dv01: np.array  # Call delta DV01
    put_delta_dv01: np.array  # Put delta DV01
    gamma_dv01: np.array  # Gamma DV01
    vega_dv01: np.array  # Vega DV01
    theta: np.array  # Theta
    forward: float  # Forward price
    strike: float  # Strike price
    time_to_expiry: float  # Time to expiry
    
    @property
    def atm_index(self) -> int:
        """Find index of ATM position (shock = 0)."""
        return np.where(self.shocks == 0)[0][0]
```

## Implementation Notes

1. **Shock Convention**: Shocks are in basis points (bp). Need to confirm if these need conversion.

2. **Neighbor Selection**: For TS-0.25, the formula uses the value from the column to the right (next higher shock).

3. **Edge Cases**: Need to handle boundary conditions where neighbor might not exist.

4. **Percentage vs Decimal**: Some values like delta are stored as percentages (need to verify units). 