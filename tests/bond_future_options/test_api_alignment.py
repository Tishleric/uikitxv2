"""
Test to verify that api.py and analysis.py produce identical results.
This ensures the API layer is correctly aligned with the implementation used in app.py.
"""

import pytest
import numpy as np
from lib.trading.bond_future_options.api import (
    calculate_implied_volatility, 
    calculate_greeks,
    quick_analysis,
    process_option_batch
)
from lib.trading.bond_future_options.analysis import (
    analyze_bond_future_option_greeks,
    solve_implied_volatility,
    calculate_all_greeks
)
from lib.trading.bond_future_options.pricing_engine import BondFutureOption
from lib.monitoring.decorators import monitor


# Test data matching app.py defaults
TEST_CASES = [
    # Near ATM option
    {
        'F': 110.7890625,  # 110 + 25.25/32
        'K': 110.75,       # 110 + 24/32
        'T': 0.018650794,  # 4.7/252
        'market_price': 0.359375,  # 23/64
        'option_type': 'put',
        'future_dv01': 0.063,
        'future_convexity': 0.002404,
        'yield_level': 0.05
    },
    # Deep OTM option
    {
        'F': 110.75,
        'K': 112.0,
        'T': 0.05,
        'market_price': 0.0625,  # 4/64
        'option_type': 'put',
        'future_dv01': 0.063,
        'future_convexity': 0.002404,
        'yield_level': 0.05
    },
    # Near expiry option
    {
        'F': 110.75,
        'K': 110.5,
        'T': 0.004,  # ~1 day
        'market_price': 0.1875,  # 12/64
        'option_type': 'put',
        'future_dv01': 0.063,
        'future_convexity': 0.002404,
        'yield_level': 0.05
    }
]


@monitor()
def test_implied_volatility_alignment():
    """Test that API and analysis functions produce identical implied volatilities"""
    for i, test_case in enumerate(TEST_CASES):
        print(f"\nTest case {i+1}: {test_case['option_type']} option, F={test_case['F']:.4f}, K={test_case['K']:.4f}")
        
        # Calculate using API
        try:
            api_vol = calculate_implied_volatility(
                F=test_case['F'],
                K=test_case['K'],
                T=test_case['T'],
                market_price=test_case['market_price'],
                option_type=test_case['option_type'],
                future_dv01=test_case['future_dv01'],
                future_convexity=test_case['future_convexity'],
                yield_level=test_case['yield_level'],
                suppress_output=True
            )
            api_success = True
            api_error = None
        except Exception as e:
            api_vol = None
            api_success = False
            api_error = str(e)
        
        # Calculate using analysis function directly
        try:
            option_model = BondFutureOption(
                test_case['future_dv01'], 
                test_case['future_convexity'], 
                test_case['yield_level']
            )
            
            # Get moneyness-based initial guess
            moneyness = (test_case['F'] - test_case['K']) / test_case['F'] if test_case['option_type'] == 'call' else (test_case['K'] - test_case['F']) / test_case['F']
            initial_guess = 20.0 if abs(moneyness) < 0.02 else 50.0
            
            analysis_vol, final_error = solve_implied_volatility(
                option_model=option_model,
                F=test_case['F'],
                K=test_case['K'],
                T=test_case['T'],
                market_price=test_case['market_price'],
                option_type=test_case['option_type'],
                initial_guess=initial_guess,
                tolerance=1e-6,
                max_iterations=100
            )
            analysis_success = abs(final_error) <= 1e-6
            analysis_error = None if analysis_success else f"Failed to converge: error={abs(final_error):.9f}"
        except Exception as e:
            analysis_vol = None
            analysis_success = False
            analysis_error = str(e)
        
        # Compare results
        api_vol_str = f"{api_vol:.6f}" if api_vol is not None else "None"
        analysis_vol_str = f"{analysis_vol:.6f}" if analysis_vol is not None else "None"
        print(f"API:      vol={api_vol_str}, success={api_success}, error={api_error}")
        print(f"Analysis: vol={analysis_vol_str}, success={analysis_success}, error={analysis_error}")
        
        if api_success and analysis_success:
            diff = abs(api_vol - analysis_vol)
            assert diff < 1e-6, f"Volatility mismatch: API={api_vol:.6f}, Analysis={analysis_vol:.6f}, diff={diff:.9f}"
            print(f"✓ Volatilities match within tolerance (diff={diff:.9f})")
        else:
            assert api_success == analysis_success, f"Success status mismatch: API={api_success}, Analysis={analysis_success}"
            print(f"✓ Both methods failed consistently")


@monitor()
def test_greeks_alignment():
    """Test that API and analysis functions produce identical Greeks"""
    # Use a known good case
    test_case = TEST_CASES[0]
    
    # First get implied volatility
    api_vol = calculate_implied_volatility(
        F=test_case['F'],
        K=test_case['K'],
        T=test_case['T'],
        market_price=test_case['market_price'],
        option_type=test_case['option_type'],
        future_dv01=test_case['future_dv01'],
        future_convexity=test_case['future_convexity'],
        yield_level=test_case['yield_level'],
        suppress_output=True
    )
    
    # Calculate Greeks using API
    api_greeks = calculate_greeks(
        F=test_case['F'],
        K=test_case['K'],
        T=test_case['T'],
        volatility=api_vol,
        option_type=test_case['option_type'],
        future_dv01=test_case['future_dv01'],
        future_convexity=test_case['future_convexity'],
        yield_level=test_case['yield_level'],
        return_scaled=True
    )
    
    # Calculate Greeks using analysis function
    option_model = BondFutureOption(
        test_case['future_dv01'], 
        test_case['future_convexity'], 
        test_case['yield_level']
    )
    analysis_greeks = calculate_all_greeks(
        option_model=option_model,
        F=test_case['F'],
        K=test_case['K'],
        T=test_case['T'],
        price_volatility=api_vol,
        option_type=test_case['option_type']
    )
    
    # Compare all Greeks
    print("\nGreek comparison:")
    for greek_name in ['delta_F', 'delta_y', 'gamma_y', 'vega_y', 'theta_F', 
                      'volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 
                      'color_F', 'ultima', 'zomma']:
        if greek_name in api_greeks and greek_name in analysis_greeks:
            api_value = api_greeks[greek_name]
            analysis_value = analysis_greeks[greek_name]
            diff = abs(api_value - analysis_value)
            
            # Use relative tolerance for large values, absolute for small
            if abs(analysis_value) > 1.0:
                tolerance = abs(analysis_value) * 1e-6
            else:
                tolerance = 1e-6
                
            assert diff < tolerance, f"{greek_name} mismatch: API={api_value:.6f}, Analysis={analysis_value:.6f}, diff={diff:.9f}"
            print(f"✓ {greek_name}: API={api_value:.6f}, Analysis={analysis_value:.6f}, diff={diff:.9f}")


@monitor()
def test_edge_cases():
    """Test edge cases with safeguards"""
    
    # Test 1: Deep OTM option below minimum price
    print("\nTest 1: Deep OTM option below minimum price")
    with pytest.raises(ValueError, match="below minimum safeguard"):
        calculate_implied_volatility(
            F=110.0,
            K=120.0,
            T=0.01,
            market_price=0.01,  # Below 1/64
            option_type='put'
        )
    
    # Test 2: Arbitrage violation
    print("\nTest 2: Arbitrage violation")
    with pytest.raises(ValueError, match="Arbitrage violation"):
        calculate_implied_volatility(
            F=100.0,
            K=110.0,
            T=0.1,
            market_price=5.0,  # Way below intrinsic value of 10
            option_type='put'
        )
    
    # Test 3: Option that fails to converge (extreme case)
    print("\nTest 3: Convergence failure handling")
    try:
        vol = calculate_implied_volatility(
            F=110.0,
            K=110.0,
            T=0.001,  # Very near expiry
            market_price=10.0,  # Unrealistic price
            option_type='put',
            suppress_output=True
        )
        print(f"Unexpected success: vol={vol}")
    except ValueError as e:
        assert "Failed to converge" in str(e) or "outside reasonable bounds" in str(e)
        print(f"✓ Correctly raised error: {e}")


@monitor()
def test_batch_processing():
    """Test batch processing functionality"""
    options = [
        {'F': 110.75, 'K': 110.5, 'T': 0.05, 'market_price': 0.359375},
        {'F': 110.75, 'K': 111.0, 'T': 0.05, 'market_price': 0.453125},
        {'F': 110.75, 'K': 120.0, 'T': 0.05, 'market_price': 0.01},  # Will fail
    ]
    
    results = process_option_batch(options, suppress_output=True)
    
    print("\nBatch processing results:")
    for i, result in enumerate(results):
        print(f"Option {i+1}: K={result['K']}, success={result['success']}")
        if result['success']:
            print(f"  Vol={result['volatility']:.2f}, Delta={result['greeks']['delta_y']:.2f}")
        else:
            print(f"  Error: {result['error_message']}")
    
    # Verify at least some succeeded
    successes = sum(1 for r in results if r['success'])
    assert successes >= 2, f"Expected at least 2 successes, got {successes}"
    
    # Verify failure has error message
    failures = [r for r in results if not r['success']]
    assert all('error_message' in f and f['error_message'] for f in failures)


if __name__ == "__main__":
    print("Testing API alignment with analysis functions...")
    
    test_implied_volatility_alignment()
    test_greeks_alignment()
    test_edge_cases()
    test_batch_processing()
    
    print("\n✓ All API alignment tests passed!") 