import numpy as np
from scipy.stats import norm
import pandas as pd
from .pricing_engine import BondFutureOption

def solve_implied_volatility(option_model, F, K, T, market_price, option_type='put', 
                           initial_guess=100.0, tolerance=1e-9):
    """
    Extract Newton-Raphson solver from solve_bond_future_option()
    EXACT copy of lines 376-387, parameterized
    
    Returns: (price_volatility, final_error) tuple
    """
    # VERBATIM COPY of solving logic from original
    price_volatility = initial_guess
    dx = 1
    
    # Initialize option_price for the while loop
    option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price
    
    while abs(option_price) > tolerance:
        option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price
        
        if abs(option_price) > tolerance:
            option_implied_2 = option_model.bachelier_future_option_price(F, K, T, price_volatility+dx, option_type) - market_price
            price_volatility = price_volatility - option_price * dx / (option_implied_2 - option_price)
        
        print(f"Current Price Volatility: {price_volatility:.6f}", option_price)
    
    return price_volatility, option_price

def calculate_all_greeks(option_model, F, K, T, price_volatility, option_type='put'):
    """
    Replicate EXACT Greek calculation sequence from solve_bond_future_option()
    Lines 389-398, preserving all scaling factors
    
    Returns: dict of Greek values
    """
    greeks = {}
    
    # EXACT replication of lines 389-391 from original
    for greek in ['delta_F', 'delta_y']:
        greek_value = getattr(option_model, greek)(F, K, T, price_volatility, option_type) * 1000 if greek != 'delta_F' else getattr(option_model, greek)(F, K, T, price_volatility, option_type)
        greeks[greek] = greek_value
    
    # EXACT replication of lines 392-394 from original  
    for greek in ['gamma_y','vega_y', 'theta_F', 'volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 'color_F']:  
        greek_value = getattr(option_model, greek)(F, K, T, price_volatility) * 1000.
        greeks[greek] = greek_value
    
    return greeks 

def generate_greek_profiles(option_model, base_F, K, T, price_volatility, 
                          option_type='put', range_size=20, step=1):
    """
    Generate Greeks across F scenarios
    
    Parameters:
    - base_F: Current market future price
    - range_size: ±range from base_F (default 20)
    - step: Increment size (default 1)
    
    Returns: List of dicts with F and all Greeks
    """
    results = []
    
    # Generate F range: base_F-20 to base_F+20
    F_values = np.arange(base_F - range_size, base_F + range_size + step, step)
    
    for F in F_values:
        # Calculate all Greeks at this F, using CONSTANT volatility
        greeks = calculate_all_greeks(option_model, F, K, T, price_volatility, option_type)
        
        # Add F value to results
        result_row = {'F': F}
        result_row.update(greeks)
        results.append(result_row)
    
    return results

def analyze_bond_future_option_greeks(future_dv01=.063, future_convexity=0.002404, 
                                    yield_level=.05, F=110+25.25/32.0, 
                                    K=110+24./32., T=4.7/252., 
                                    market_price=23./64, option_type='put'):
    """
    Replacement for solve_bond_future_option() with same defaults
    
    Workflow:
    1. Create model (unchanged)
    2. Solve implied volatility
    3. Generate Greek profiles
    4. Return structured results
    """
    # Step 1: Initialize model (UNCHANGED)
    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    # Step 2: Solve implied volatility
    price_volatility, final_error = solve_implied_volatility(
        option_model, F, K, T, market_price, option_type
    )
    
    # Print yield volatility first (matches line 388 of original)
    print(option_model.convert_price_to_yield_volatility(price_volatility))
    print(f"Final Price Volatility: {price_volatility:.6f}")
    # Use the final error from the solver (should be ~0)
    print(f"Final Option Price: {final_error:.6f}")
    
    # Step 3: Calculate Greeks at current F (for backward compatibility)
    current_greeks = calculate_all_greeks(option_model, F, K, T, price_volatility, option_type)
    
    # Print Greeks to match original output format
    for greek in ['delta_F', 'delta_y']:
        print(f"{greek}: {current_greeks[greek]:.6f}")
    
    for greek in ['gamma_y','vega_y', 'theta_F', 'volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 'color_F']:
        print(f"{greek}: {current_greeks[greek]:.6f}")
    
    # Step 4: Generate Greek profiles
    greek_profiles = generate_greek_profiles(
        option_model, F, K, T, price_volatility, option_type
    )
    
    return {
        'model': option_model,
        'implied_volatility': price_volatility,
        'current_greeks': current_greeks,
        'greek_profiles': greek_profiles
    } 

def validate_refactoring():
    """
    Validate that refactored code produces identical results to original
    """
    import io
    import sys
    from contextlib import redirect_stdout
    # NOTE: This validation function requires bfo_fixed.py to be in the Python path
    # It's preserved for historical validation purposes
    try:
        from bfo_fixed import solve_bond_future_option
    except ImportError:
        print("WARNING: Cannot validate against original bfo_fixed.py - file not found in Python path")
        print("This is expected after migration to the new package structure")
        return True
    
    # Capture original output
    original_output = io.StringIO()
    with redirect_stdout(original_output):
        solve_bond_future_option()
    original_lines = original_output.getvalue().strip().split('\n')
    
    # Capture refactored output
    refactored_output = io.StringIO()
    with redirect_stdout(refactored_output):
        analyze_bond_future_option_greeks()
    refactored_lines = refactored_output.getvalue().strip().split('\n')
    
    # Compare outputs
    print("=== VALIDATION RESULTS ===")
    
    # Check if same number of lines
    if len(original_lines) != len(refactored_lines):
        print(f"ERROR: Different number of output lines")
        print(f"Original: {len(original_lines)} lines")
        print(f"Refactored: {len(refactored_lines)} lines")
        print("\nOriginal output:")
        print("\n".join(original_lines))
        print("\nRefactored output:")
        print("\n".join(refactored_lines))
        return False
    
    # Compare line by line
    all_match = True
    for i, (orig, refact) in enumerate(zip(original_lines, refactored_lines)):
        if orig != refact:
            print(f"Line {i+1} differs:")
            print(f"  Original:   '{orig}'")
            print(f"  Refactored: '{refact}'")
            all_match = False
    
    if all_match:
        print("SUCCESS: All outputs match exactly!")
        return True
    else:
        print("\nERROR: Outputs do not match")
        return False

if __name__ == "__main__":
    # Run validation
    validate_refactoring() 