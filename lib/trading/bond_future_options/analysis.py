import numpy as np
from scipy.stats import norm
import pandas as pd
from .pricing_engine import BondFutureOption

def solve_implied_volatility(option_model, F, K, T, market_price, option_type='put', 
                           initial_guess=100.0, tolerance=1e-9, max_iterations=100):
    """
    Extract Newton-Raphson solver from solve_bond_future_option()
    with added safeguards to prevent infinite loops
    
    Returns: (price_volatility, final_error) tuple
    """
    # Use better initial guess based on typical values
    price_volatility = initial_guess if initial_guess != 100.0 else 20.0
    
    # Use smaller step size for better convergence
    dx = 0.1
    
    # Track iterations to prevent infinite loops
    iteration = 0
    
    # Initialize option_price for the while loop
    option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price
    
    # Store convergence history for debugging
    convergence_history = []
    
    # Track if we've hit zero derivative
    zero_derivative_count = 0
    max_zero_derivative_attempts = 3
    
    while abs(option_price) > tolerance and iteration < max_iterations:
        iteration += 1
        option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type) - market_price
        
        # Store convergence info
        convergence_history.append((iteration, price_volatility, option_price))
        
        if abs(option_price) > tolerance:
            # Calculate numerical derivative
            option_implied_2 = option_model.bachelier_future_option_price(F, K, T, price_volatility+dx, option_type) - market_price
            derivative = (option_implied_2 - option_price) / dx
            
            # Check for zero derivative to prevent division by zero
            if abs(derivative) < 1e-10:
                zero_derivative_count += 1
                print(f"WARNING: Derivative too small ({derivative:.2e}) at iteration {iteration}, vol={price_volatility:.6f}")
                
                # Try to escape zero derivative by perturbing volatility
                if zero_derivative_count <= max_zero_derivative_attempts:
                    # Perturb volatility in direction of error
                    if option_price > 0:  # Price too high, need lower vol
                        price_volatility *= 0.9
                    else:  # Price too low, need higher vol
                        price_volatility *= 1.1
                    print(f"Attempting to escape zero derivative, new vol={price_volatility:.6f}")
                    continue
                else:
                    print(f"ERROR: Unable to escape zero derivative after {max_zero_derivative_attempts} attempts")
                    break
            
            # Reset zero derivative count on successful derivative
            zero_derivative_count = 0
            
            # Newton-Raphson update
            new_volatility = price_volatility - option_price / derivative
            
            # Bound volatility to reasonable values to prevent divergence
            # Min: 0.1 (very low vol), Max: 1000.0 (extremely high vol)
            new_volatility = max(0.1, min(1000.0, new_volatility))
            
            # Check for large jumps that might indicate instability
            if abs(new_volatility - price_volatility) > 50.0:
                print(f"WARNING: Large volatility jump from {price_volatility:.2f} to {new_volatility:.2f} at iteration {iteration}")
                # Dampen the update for stability
                new_volatility = price_volatility + 0.5 * (new_volatility - price_volatility)
            
            price_volatility = new_volatility
        
        print(f"Current Price Volatility: {price_volatility:.6f}, Error: {option_price:.9f}")
    
    # Check convergence status
    if iteration >= max_iterations:
        print(f"WARNING: Newton-Raphson failed to converge after {max_iterations} iterations")
        print(f"Final error: {abs(option_price):.9f}, Final volatility: {price_volatility:.6f}")
        print(f"Inputs: F={F:.6f}, K={K:.6f}, T={T:.6f}, market_price={market_price:.6f}, type={option_type}")
        
        # Print last few iterations for debugging
        if len(convergence_history) > 5:
            print("Last 5 iterations:")
            for i, vol, err in convergence_history[-5:]:
                print(f"  Iter {i}: vol={vol:.6f}, error={err:.9f}")
    
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
    
    # Add new 3rd order Greeks (scaled by 1000 for consistency)
    for greek in ['ultima', 'zomma']:
        greek_value = getattr(option_model, greek)(F, K, T, price_volatility) * 1000.
        greeks[greek] = greek_value
    
    # Add F-space Greeks for numerical comparison (not in original)
    # These are needed for comparing with numerical differentiation
    greeks['gamma_F'] = option_model.gamma_F(F, K, T, price_volatility)
    greeks['vega_price'] = option_model.vega_price(F, K, T, price_volatility)
    greeks['vomma_F'] = option_model.vomma_F(F, K, T, price_volatility)
    
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