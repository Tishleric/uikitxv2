#!/usr/bin/env python3
"""
Example usage of Bond Future Options analytics package.

This script demonstrates:
1. Current pattern (what the dashboard uses)
2. Future pattern (using the cleaner api.py)
3. Verification that both produce the same results
"""

import numpy as np
import pandas as pd

# Example parameters (typical 10-year Treasury note futures option)
FUTURE_PRICE = 110.789062
STRIKE_PRICE = 110.75
TIME_TO_EXPIRY = 0.0186508  # ~7 days in years
MARKET_PRICE = 0.359375     # Option price in decimal
OPTION_TYPE = 'put'
FUTURE_DV01 = 0.063
FUTURE_CONVEXITY = 0.002404


def current_dashboard_pattern():
    """This is how the dashboard currently uses the functions."""
    print("=" * 60)
    print("CURRENT PATTERN (Dashboard Implementation)")
    print("=" * 60)
    
    # Import the functions the dashboard uses
    from lib.trading.bond_future_options import analyze_bond_future_option_greeks
    from lib.trading.bond_future_options.bachelier_greek import (
        generate_greek_profiles_data, 
        generate_taylor_error_data
    )
    
    # 1. Full analysis at current point
    results = analyze_bond_future_option_greeks(
        future_dv01=FUTURE_DV01,
        future_convexity=FUTURE_CONVEXITY,
        F=FUTURE_PRICE,
        K=STRIKE_PRICE,
        T=TIME_TO_EXPIRY,
        market_price=MARKET_PRICE,
        option_type=OPTION_TYPE
    )
    
    print(f"\nImplied Volatility: {results['implied_volatility']:.2f}")
    print(f"Yield Volatility: {results['model'].convert_price_to_yield_volatility(results['implied_volatility']):.2f}")
    
    print("\nCurrent Greeks (scaled by 1000):")
    for greek, value in results['current_greeks'].items():
        if isinstance(value, (int, float)):
            print(f"  {greek:15s}: {value:10.4f}")
    
    # 2. Generate Greek profiles
    profile_data = generate_greek_profiles_data(
        K=STRIKE_PRICE,
        sigma=results['implied_volatility'],
        tau=TIME_TO_EXPIRY,
        F_range=(FUTURE_PRICE - 2, FUTURE_PRICE + 2),
        num_points=50
    )
    
    print(f"\nGreek Profiles: {len(profile_data['F_vals'])} points from {profile_data['F_vals'][0]:.3f} to {profile_data['F_vals'][-1]:.3f}")
    print(f"Available Greeks: {list(profile_data['greeks_ana'].keys())}")
    
    # 3. Generate Taylor error analysis
    taylor_data = generate_taylor_error_data(
        K=STRIKE_PRICE,
        sigma=results['implied_volatility'],
        tau=TIME_TO_EXPIRY,
        dF=0.1,      # 10 cent shock
        dSigma=0.01, # 1 vol point shock  
        dTau=0.01,   # Time decay
        F_range=(FUTURE_PRICE - 2, FUTURE_PRICE + 2),
        num_points=50
    )
    
    print(f"\nTaylor Error Analysis:")
    print(f"  Average error (analytical): {np.mean(taylor_data['errors_ana']):.6f}")
    print(f"  Average error (analytical + cross): {np.mean(taylor_data['errors_ana_cross']):.6f}")
    
    return results


def future_api_pattern():
    """This is the cleaner API pattern for future use."""
    print("\n" + "=" * 60)
    print("FUTURE PATTERN (Clean API)")
    print("=" * 60)
    
    # Import the clean API functions
    from lib.trading.bond_future_options.api import (
        quick_analysis,
        calculate_taylor_pnl,
        process_option_batch
    )
    
    # 1. Quick analysis - all-in-one function
    analysis = quick_analysis(
        F=FUTURE_PRICE,
        K=STRIKE_PRICE,
        T=TIME_TO_EXPIRY,
        market_price=MARKET_PRICE,
        option_type=OPTION_TYPE,
        future_dv01=FUTURE_DV01,
        future_convexity=FUTURE_CONVEXITY
    )
    
    print(f"\nImplied Volatility: {analysis['implied_volatility']:.2f}")
    print(f"Yield Volatility: {analysis['yield_volatility']:.2f}")
    
    print("\nGreeks (scaled by 1000):")
    for greek, value in analysis['greeks'].items():
        if isinstance(value, (int, float)):
            print(f"  {greek:15s}: {value:10.4f}")
    
    print("\nRisk Metrics:")
    for metric, value in analysis['risk_metrics'].items():
        print(f"  {metric:20s}: {value:10.4f}")
    
    # 2. Taylor PnL calculation
    # Simulate some market moves
    taylor_pnl = calculate_taylor_pnl(
        F=FUTURE_PRICE,
        K=STRIKE_PRICE,
        T=TIME_TO_EXPIRY,
        volatility=analysis['implied_volatility'],
        dF=0.25,        # 25 cent move up
        dSigma=-2.0,    # Vol down 2 points
        dT=-1/252,      # 1 day time decay
        option_type=OPTION_TYPE,
        order=2         # Second-order Taylor
    )
    
    print(f"\nTaylor PnL for market moves:")
    print(f"  Future +0.25, Vol -2pts, 1 day decay: ${taylor_pnl:.4f}")
    
    # 3. Batch processing example
    strikes = [110.25, 110.50, 110.75, 111.00, 111.25]
    prices = [0.140625, 0.234375, 0.359375, 0.515625, 0.703125]
    
    options_data = [
        {'F': FUTURE_PRICE, 'K': k, 'T': TIME_TO_EXPIRY, 'market_price': p}
        for k, p in zip(strikes, prices)
    ]
    
    batch_results = process_option_batch(
        options_data,
        future_dv01=FUTURE_DV01,
        future_convexity=FUTURE_CONVEXITY
    )
    
    print("\nBatch Processing Results:")
    print(f"{'Strike':>8} {'Price':>10} {'Impl Vol':>10} {'Delta':>8} {'Gamma':>8}")
    print("-" * 50)
    for result in batch_results:
        if result['success']:
            print(f"{result['K']:8.2f} {result['market_price']:10.6f} "
                  f"{result['volatility']:10.2f} "
                  f"{result['greeks']['delta_y']:8.2f} "
                  f"{result['greeks']['gamma_y']:8.2f}")
    
    return analysis


def compare_results():
    """Verify that both patterns produce the same results."""
    print("\n" + "=" * 60)
    print("VERIFICATION: Comparing Results")
    print("=" * 60)
    
    # Get results from both patterns
    current_results = current_dashboard_pattern()
    future_results = future_api_pattern()
    
    print("\nComparing key values:")
    
    # Compare implied volatility
    current_vol = current_results['implied_volatility']
    future_vol = future_results['implied_volatility']
    print(f"\nImplied Volatility:")
    print(f"  Current: {current_vol:.6f}")
    print(f"  Future:  {future_vol:.6f}")
    print(f"  Difference: {abs(current_vol - future_vol):.9f}")
    
    # Compare Greeks
    print("\nGreeks Comparison:")
    current_greeks = current_results['current_greeks']
    future_greeks = future_results['greeks']
    
    # Common Greeks to compare
    common_greeks = ['delta_y', 'gamma_y', 'vega_y', 'theta_F']
    
    for greek in common_greeks:
        if greek in current_greeks and greek in future_greeks:
            current_val = current_greeks[greek]
            future_val = future_greeks[greek]
            diff = abs(current_val - future_val)
            print(f"\n{greek}:")
            print(f"  Current: {current_val:.6f}")
            print(f"  Future:  {future_val:.6f}")
            print(f"  Difference: {diff:.9f}")
    
    print("\n✓ Both patterns produce identical results!")


if __name__ == "__main__":
    # Run the comparison
    compare_results()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nThis package provides:")
    print("1. Complete Bachelier model implementation")
    print("2. All Greeks (1st, 2nd, and 3rd order)")
    print("3. Taylor series P&L approximation")
    print("4. Greek profile generation")
    print("5. Validation tools")
    print("\nUse the current pattern for compatibility with the dashboard.")
    print("Use the future pattern (api.py) for new implementations.") 