"""Test integration of SpotRiskGreekCalculator with GreekCalculatorAPI."""

import pytest
import pandas as pd
import numpy as np
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
import logging

logging.basicConfig(level=logging.INFO)


def test_spot_risk_greek_calculator_with_api():
    """Test that SpotRiskGreekCalculator works with the new API."""
    
    # Create sample data with futures and options
    data = {
        'Product': ['XCME.ZN.SEP25', 'XCME.ZN.SEP25C112', 'XCME.ZN.SEP25P110'],
        'Instrument Type': ['FUTURE', 'CALL', 'PUT'],
        'Strike': [np.nan, 112.0, 110.0],
        'Price': [110.7734375, 0.5, 0.75],
        'vtexp': [0.25, 0.25, 0.25],  # 3 months to expiry
        'itype': ['F', 'C', 'P']
    }
    df = pd.DataFrame(data)
    
    # Initialize calculator
    calculator = SpotRiskGreekCalculator()
    
    # Calculate Greeks
    result_df, greek_results = calculator.calculate_greeks(df)
    
    # Verify columns were added
    expected_columns = [
        'calc_vol', 'implied_vol', 'delta_F', 'delta_y', 'gamma_F', 'gamma_y',
        'vega_price', 'vega_y', 'theta_F', 'volga_price', 'vanna_F_price',
        'charm_F', 'speed_F', 'color_F', 'ultima', 'zomma',
        'greek_calc_success', 'greek_calc_error', 'model_version'
    ]
    for col in expected_columns:
        assert col in result_df.columns, f"Column {col} not found in result"
    
    # Verify futures have NaN Greeks
    future_row = result_df[result_df['Instrument Type'] == 'FUTURE'].iloc[0]
    assert pd.isna(future_row['delta_F'])
    assert pd.isna(future_row['gamma_y'])
    
    # Verify options have calculated Greeks
    call_row = result_df[result_df['Instrument Type'] == 'CALL'].iloc[0]
    put_row = result_df[result_df['Instrument Type'] == 'PUT'].iloc[0]
    
    # Check that Greeks were calculated
    assert not pd.isna(call_row['implied_vol'])
    assert not pd.isna(call_row['delta_F'])
    assert not pd.isna(put_row['implied_vol'])
    assert not pd.isna(put_row['delta_F'])
    
    # Verify success flags
    assert call_row['greek_calc_success'] == True
    assert put_row['greek_calc_success'] == True
    
    # Verify model version
    print(f"Call model version: {call_row['model_version']}")
    print(f"Put model version: {put_row['model_version']}")
    # For now, just check that model_version is set
    assert call_row['model_version'] != ''
    assert put_row['model_version'] != ''

    # Basic sanity checks on Greeks
    assert 0 < call_row['delta_F'] < 1, "Call delta should be between 0 and 1"
    assert -1 < put_row['delta_F'] < 0, "Put delta should be between -1 and 0"
    
    print(f"Call IV: {call_row['implied_vol']:.4f}, Delta: {call_row['delta_F']:.4f}")
    print(f"Put IV: {put_row['implied_vol']:.4f}, Delta: {put_row['delta_F']:.4f}")
    
    # Verify we got 2 GreekResult objects (one for each option)
    assert len(greek_results) == 2
    assert all(result.success for result in greek_results)


def test_spot_risk_with_different_column_names():
    """Test with different column naming conventions."""
    
    # Create data with lowercase column names
    data = {
        'instrument_key': ['ZN_FUT', 'ZN_CALL_112', 'ZN_PUT_110'],
        'itype': ['F', 'C', 'P'],
        'strike': [np.nan, 112.0, 110.0],
        'midpoint_price': [110.7734375, 0.5, 0.75],
        'vtexp': [0.25, 0.25, 0.25]
    }
    df = pd.DataFrame(data)
    
    # Initialize calculator
    calculator = SpotRiskGreekCalculator()
    
    # Calculate Greeks
    result_df, greek_results = calculator.calculate_greeks(df)
    
    # Verify calculations worked
    assert len(greek_results) == 2
    assert all(result.success for result in greek_results)
    
    # Check Greeks were added
    call_row = result_df[result_df['itype'] == 'C'].iloc[0]
    assert not pd.isna(call_row['implied_vol'])
    assert not pd.isna(call_row['delta_F'])


def test_spot_risk_error_handling():
    """Test that missing future price raises ValueError with descriptive message."""
    
    # Create data with only options (no future) - this should never happen in real data
    data = {
        'Product': ['XCME.ZN.SEP25C112', 'XCME.ZN.SEP25P110'],
        'Instrument Type': ['CALL', 'PUT'],
        'Strike': [112.0, 110.0],
        'Price': [0.5, 0.75],
        'vtexp': [0.25, 0.25]
    }
    df = pd.DataFrame(data)
    
    # Initialize calculator
    calculator = SpotRiskGreekCalculator()
    
    # Should raise ValueError with descriptive message
    with pytest.raises(ValueError) as exc_info:
        calculator.calculate_greeks(df)
    
    # Check that error message is descriptive
    error_msg = str(exc_info.value)
    assert "No valid future price found" in error_msg
    assert "Searched:" in error_msg
    assert "'Instrument Type' == 'FUTURE'" in error_msg


if __name__ == "__main__":
    print("\n=== Test 1: Greek Calculator with API ===")
    test_spot_risk_greek_calculator_with_api()
    print("✓ Test 1 passed: Successfully calculated Greeks for options with future price")
    
    print("\n=== Test 2: Different Column Names ===")
    test_spot_risk_with_different_column_names()
    print("✓ Test 2 passed: Successfully handled different column naming conventions")
    
    print("\n=== Test 3: Error Handling (Missing Future) ===")
    test_spot_risk_error_handling()
    print("✓ Test 3 passed: Correctly raised ValueError for missing future price")
    
    print("\n✅ All tests passed! No false-passing tests with ERROR logs.") 