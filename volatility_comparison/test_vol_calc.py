"""
Test volatility calculation to match UI
"""

from bond_option_pricer import solve_bond_future_option, calculate_bond_option_volatility

# Test case from the UI Greek Analysis
F = 110.789062
K = 110.75
days_to_expiry = 4.7
market_price_64ths = 23
option_type = 'put'

print("Test Case (from UI):")
print(f"Future Price: {F}")
print(f"Strike: {K}")
print(f"Days to Expiry: {days_to_expiry}")
print(f"Market Price (64ths): {market_price_64ths}")
print(f"Market Price (decimal): {market_price_64ths/64.0:.6f}")
print(f"Option Type: {option_type}")
print()

# Method 1: Using solve_bond_future_option directly
result = solve_bond_future_option(
    F=F,
    K=K,
    T=days_to_expiry/252.0,
    price=market_price_64ths/64.0,
    option_type=option_type
)

print("Direct solve_bond_future_option result:")
print(f"  Price Volatility: {result['price_volatility']:.6f}")
print(f"  Yield Volatility: {result['yield_volatility']:.6f}")
print(f"  Yield Volatility %: {result['yield_volatility']:.2f}%")
print()

# Method 2: Using calculate_bond_option_volatility
yield_vol = calculate_bond_option_volatility(F, K, days_to_expiry, market_price_64ths, option_type=option_type)
print("calculate_bond_option_volatility result:")
print(f"  Yield Volatility: {yield_vol:.6f}")
print(f"  Yield Volatility %: {yield_vol:.2f}%")
print()

# Let's try with some PM data
print("\nTest with PM data:")
F_pm = 111.1797  # Parsed underlying
K_pm = 111.25    # Strike
days_pm = 26     # Days from PM
market_price_pm = 22.0  # 64ths from PM

result_pm = solve_bond_future_option(
    F=F_pm,
    K=K_pm,
    T=days_pm/252.0,
    price=market_price_pm/64.0,
    option_type='call'  # PM shows calls
)

print(f"PM Example - 1st 10y note 0out call:")
print(f"  Future: {F_pm}, Strike: {K_pm}, Days: {days_pm}")
print(f"  Market Price: {market_price_pm}/64ths = {market_price_pm/64.0:.6f}")
print(f"  Price Volatility: {result_pm['price_volatility']:.6f}")
print(f"  Yield Volatility: {result_pm['yield_volatility']:.6f}")
print(f"  Yield Volatility %: {result_pm['yield_volatility']:.2f}%")

# The issue might be that the market quotes are already in yield vol terms
# Let's see what price vol gives us the PM market vol
print("\nReverse calculation - what price vol gives us 8.85% yield vol?")
target_yield_vol = 8.85 / 100  # Convert percentage to decimal
model = result_pm['model']
price_vol_from_yield = model.convert_yield_to_future_price_volatility(target_yield_vol)
print(f"  Target yield vol: {target_yield_vol:.4f} ({target_yield_vol*100:.2f}%)")
print(f"  Equivalent price vol: {price_vol_from_yield:.6f}") 