"""
Demonstration of Greek Profile Analysis for Bond Future Options
This script shows how to use the refactored code to generate Greek profiles
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from trading.bond_future_options import analyze_bond_future_option_greeks

# Run the analysis with default parameters
print("=== Running Bond Future Option Analysis ===\n")
results = analyze_bond_future_option_greeks()

# Extract results
model = results['model']
implied_vol = results['implied_volatility']
current_greeks = results['current_greeks']
greek_profiles = results['greek_profiles']

print(f"\n=== Analysis Results ===")
print(f"Implied Price Volatility: {implied_vol:.6f}")
print(f"Implied Yield Volatility: {model.convert_price_to_yield_volatility(implied_vol):.6f}")

# Convert Greek profiles to DataFrame for easy analysis
df_profiles = pd.DataFrame(greek_profiles)

# Display first few rows
print(f"\n=== Greek Profiles (First 5 rows) ===")
print(df_profiles.head())

# Create output directory if it doesn't exist
output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

# Save to CSV
csv_filename = os.path.join(output_dir, 'greek_profiles_full.csv')
df_profiles.to_csv(csv_filename, index=False)
print(f"\nGreek profiles saved to {csv_filename}")

# Create basic plots for key Greeks
print("\n=== Creating Greek Profile Plots ===")

# Extract all parameters for the enhanced title
strike = 110.75  # Strike price
expiry_days = (4.7/252.) * 252  # Convert T back to days
dv01 = model.future_dv01
convexity = model.future_convexity
yield_level = model.yield_level
current_F = 110.789062
yield_vol = model.convert_price_to_yield_volatility(implied_vol)

# Setup figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Create comprehensive multi-line title
title_lines = [
    'Bond Future Option Greek Profiles',
    f'Strike: {strike:.3f} | Expiry: {expiry_days:.1f} days | Type: PUT',
    f'DV01: {dv01:.4f} | Convexity: {convexity:.6f} | Yield Level: {yield_level:.2%}',
    f'Current F: {current_F:.3f} | Implied Vol: {implied_vol:.2f} (Price) / {yield_vol:.2f} (Yield)'
]
fig.suptitle('\n'.join(title_lines), fontsize=12)

# Plot Delta (Y-Space instead of F-Space)
ax = axes[0, 0]
ax.plot(df_profiles['F'], df_profiles['delta_y'], 'b-', linewidth=2)
ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
ax.axvline(x=110.75, color='r', linestyle='--', alpha=0.3, label='Strike')
ax.set_xlabel('Future Price')
ax.set_ylabel('Delta (Y-Space) × 1000')
ax.set_title('Delta Profile')
ax.grid(True, alpha=0.3)
ax.legend()

# Plot Gamma
ax = axes[0, 1]
ax.plot(df_profiles['F'], df_profiles['gamma_y'], 'g-', linewidth=2)
ax.axvline(x=110.75, color='r', linestyle='--', alpha=0.3, label='Strike')
ax.set_xlabel('Future Price')
ax.set_ylabel('Gamma (Y-Space) x1000')
ax.set_title('Gamma Profile')
ax.grid(True, alpha=0.3)
ax.legend()

# Plot Vega
ax = axes[1, 0]
ax.plot(df_profiles['F'], df_profiles['vega_y'], 'm-', linewidth=2)
ax.axvline(x=110.75, color='r', linestyle='--', alpha=0.3, label='Strike')
ax.set_xlabel('Future Price')
ax.set_ylabel('Vega (Y-Space) x1000')
ax.set_title('Vega Profile')
ax.grid(True, alpha=0.3)
ax.legend()

# Plot Theta
ax = axes[1, 1]
ax.plot(df_profiles['F'], df_profiles['theta_F'], 'c-', linewidth=2)
ax.axvline(x=110.75, color='r', linestyle='--', alpha=0.3, label='Strike')
ax.set_xlabel('Future Price')
ax.set_ylabel('Theta (F-Space) x1000')
ax.set_title('Theta Profile')
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()
png_filename = os.path.join(output_dir, 'greek_profiles.png')
plt.savefig(png_filename, dpi=150)
print(f"Greek profile plots saved to {png_filename}")

# Additional analysis: Find key points
current_F = 110.789062
strike = 110.75

print(f"\n=== Key Analysis Points ===")
print(f"Current Future Price: {current_F:.6f}")
print(f"Strike Price: {strike:.6f}")
print(f"Moneyness: {current_F - strike:.6f}")

# Find ATM row
atm_idx = (df_profiles['F'] - strike).abs().idxmin()
atm_row = df_profiles.iloc[atm_idx]
print(f"\nATM Greeks (F={atm_row['F']:.1f}):")
print(f"  Delta: {atm_row['delta_y']:.4f}")
print(f"  Gamma: {atm_row['gamma_y']:.4f}")
print(f"  Vega: {atm_row['vega_y']:.4f}")

# Show how Greeks can be used for scenario analysis
print(f"\n=== Scenario Analysis ===")
scenarios = [
    ("Down 5 points", current_F - 5),
    ("Down 2 points", current_F - 2),
    ("Current", current_F),
    ("Up 2 points", current_F + 2),
    ("Up 5 points", current_F + 5)
]

for label, F_scenario in scenarios:
    # Find closest F in profiles
    idx = (df_profiles['F'] - F_scenario).abs().idxmin()
    row = df_profiles.iloc[idx]
    print(f"\n{label} (F={row['F']:.1f}):")
    print(f"  Delta: {row['delta_y']:.4f}")
    print(f"  Gamma: {row['gamma_y']:.4f}")
    print(f"  Vega: {row['vega_y']:.4f}")

print("\n=== Demo Complete ===")
print("The refactored code successfully separates:")
print("1. Implied volatility solving")
print("2. Greek calculations") 
print("3. Profile generation across price scenarios")
print("\nThis enables flexible analysis and visualization of option risk profiles.") 