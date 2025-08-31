#!/usr/bin/env python3
"""
Simple Bond Future Options Calculator

Takes option parameters and outputs implied volatility and Greeks.
Uses the existing uikitxv2 bond future options package.
"""

import sys
import os

# Add the project root to Python path so we can import uikitxv2 modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from lib.trading.bond_future_options.analysis import solve_implied_volatility, calculate_all_greeks
from lib.trading.bond_future_options.pricing_engine import BondFutureOption


def calculate_option_vol_and_greeks(future_price, strike_price, time_to_expiry, 
                                   option_price, option_type='put',
                                   future_dv01=0.063, future_convexity=0.002404):
    """
    Calculate implied volatility and Greeks for a bond future option.
    
    Parameters:
    -----------
    future_price : float
        Current future price (e.g., 110.789)
    strike_price : float  
        Option strike price (e.g., 110.75)
    time_to_expiry : float
        Time to expiry in years (e.g., 0.0186 for ~7 days)
    option_price : float
        Market price of the option (e.g., 0.359375)
    option_type : str
        'call' or 'put' (default: 'put')
    future_dv01 : float
        Future DV01 (default: 0.063)
    future_convexity : float
        Future convexity (default: 0.002404)
        
    Returns:
    --------
    dict with 'implied_volatility', 'yield_volatility', and 'greeks'
    """
    
    # Create the bond future option model
    model = BondFutureOption(future_dv01, future_convexity)
    
    # Solve for implied volatility
    implied_vol, final_error = solve_implied_volatility(
        model, future_price, strike_price, time_to_expiry, 
        option_price, option_type
    )
    
    # Convert to yield volatility
    yield_vol = model.convert_price_to_yield_volatility(implied_vol)
    
    # Calculate all Greeks
    greeks = calculate_all_greeks(
        model, future_price, strike_price, time_to_expiry, 
        implied_vol, option_type
    )
    
    return {
        'implied_volatility': implied_vol,
        'yield_volatility': yield_vol,
        'greeks': greeks,
        'final_error': final_error
    }


def main():
    """Example usage"""
    
    # Example: 10-year Treasury note futures option
    result = calculate_option_vol_and_greeks(
        future_price=110.789062,
        strike_price=110.75,
        time_to_expiry=0.0186508,  # ~7 days
        option_price=0.359375,
        option_type='put'
    )
    
    print("=" * 50)
    print("Bond Future Option Analysis")
    print("=" * 50)
    
    print(f"Implied Volatility (Price): {result['implied_volatility']:.2f}")
    print(f"Implied Volatility (Yield): {result['yield_volatility']:.2f}")
    print(f"Final Error: {result['final_error']:.9f}")
    
    print("\nGreeks:")
    print("-" * 30)
    for greek_name, value in result['greeks'].items():
        print(f"{greek_name:15s}: {value:10.4f}")


if __name__ == "__main__":
    result = calculate_option_vol_and_greeks(future_price=111.71875,
        strike_price=110.25,
        time_to_expiry=0.0008349,  # ~7 days
        option_price=1.46875,
        option_type='call'
    )
    print(result['greeks']['delta_F'])
    print(result['greeks']['gamma_F'])
    print(result['greeks']['speed_F'])

    

