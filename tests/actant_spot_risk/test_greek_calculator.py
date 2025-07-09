"""Test Greek calculator with real spot risk CSV data."""

import pytest
import pandas as pd
from pathlib import Path
import numpy as np

from lib.trading.actant.spot_risk import (
    parse_spot_risk_csv,
    SpotRiskGreekCalculator
)


def test_greek_calculator_with_real_csv():
    """Test Greek calculations on real CSV data."""
    # Load real CSV file
    csv_path = Path("data/input/actant_spot_risk/bav_analysis_20250708_104022.csv")
    
    if not csv_path.exists():
        pytest.skip(f"Test CSV not found: {csv_path}")
    
    # Parse CSV
    df = parse_spot_risk_csv(csv_path)
    
    # Verify we have data
    assert len(df) > 0, "No data loaded from CSV"
    
    # Extract future price from the future row
    future_rows = df[df['instrument_type'] == 'future']
    assert len(future_rows) == 1, f"Expected 1 future, found {len(future_rows)}"
    
    future_price = future_rows.iloc[0]['midpoint_price']
    print(f"Future price: {future_price}")
    
    # Add future_price column for calculator
    df['future_price'] = future_price
    
    # Initialize calculator with default values
    calculator = SpotRiskGreekCalculator()
    
    # Calculate Greeks
    df_with_greeks, results = calculator.calculate_greeks(df)
    
    # Print summary
    print(f"\nTotal rows: {len(df)}")
    print(f"Options processed: {len(results)}")
    
    # Check for successful calculations
    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]
    
    print(f"Successful calculations: {len(successful)}")
    print(f"Failed calculations: {len(failed)}")
    
    # Print sample of successful results
    if successful:
        print("\nSample successful results:")
        for result in successful[:3]:
            print(f"\n{result.instrument_key}:")
            print(f"  Strike: {result.strike}")
            print(f"  Type: {result.option_type}")
            print(f"  Market price: {result.market_price:.4f}")
            print(f"  IV: {result.implied_volatility:.4f}")
            print(f"  Delta_y: {result.delta_y:.4f}")
            print(f"  Gamma_y: {result.gamma_y:.4f}")
            print(f"  Vega_y: {result.vega_y:.4f}")
    
    # Print any errors
    if failed:
        print("\nErrors encountered:")
        for result in failed[:5]:  # Show first 5 errors
            print(f"\n{result.instrument_key}: {result.error}")
            if result.error_details:
                print(f"  Details: {result.error_details}")
    
    # Verify DataFrame has Greek columns
    greek_columns = ['calc_vol', 'delta_y', 'gamma_y', 'vega_y', 'theta_F']
    for col in greek_columns:
        assert col in df_with_greeks.columns, f"Missing column: {col}"
    
    # Check that at least some Greeks were calculated
    assert df_with_greeks['calc_vol'].notna().sum() > 0, "No implied volatilities calculated"
    assert df_with_greeks['delta_y'].notna().sum() > 0, "No deltas calculated"
    
    return df_with_greeks, results


def test_single_option_calculation():
    """Test calculation for a single option."""
    calculator = SpotRiskGreekCalculator()
    
    # Create test data
    test_option = pd.Series({
        'instrument_key': 'XCME.ZN1.09JUL25.110:25.C',
        'strike': 110.25,
        'option_type': 'call',
        'midpoint_price': 0.0156,  # 1/64ths
        'vtexp': 0.004519,  # ~1.14 business days
        'future_price': 110.875
    })
    
    # Calculate single Greek
    result = calculator.calculate_single_greek(test_option)
    
    # Check result
    assert result.error is None, f"Calculation failed: {result.error}"
    assert result.implied_volatility is not None
    assert result.delta_y is not None
    
    print(f"\nSingle option test:")
    print(f"Strike: {result.strike}, Type: {result.option_type}")
    print(f"IV: {result.implied_volatility:.4f}")
    print(f"Delta_y: {result.delta_y:.4f}")
    print(f"Gamma_y: {result.gamma_y:.4f}")
    
    return result


def test_invalid_inputs():
    """Test error handling for invalid inputs."""
    calculator = SpotRiskGreekCalculator()
    
    # Test missing strike
    test_data = pd.Series({
        'instrument_key': 'TEST',
        'option_type': 'call',
        'midpoint_price': 0.1,
        'vtexp': 0.1,
        'future_price': 100
    })
    
    result = calculator.calculate_single_greek(test_data)
    assert result.error == "Missing strike price"
    
    # Test invalid option type
    test_data['strike'] = 100
    test_data['option_type'] = 'invalid'
    
    result = calculator.calculate_single_greek(test_data)
    assert result.error == "Invalid option type: invalid"
    
    # Test negative time to expiry
    test_data['option_type'] = 'call'
    test_data['vtexp'] = -0.1
    
    result = calculator.calculate_single_greek(test_data)
    assert "Invalid time to expiry" in result.error


if __name__ == "__main__":
    # Run tests
    print("Testing single option calculation...")
    test_single_option_calculation()
    
    print("\n" + "="*60 + "\n")
    
    print("Testing with real CSV data...")
    df_with_greeks, results = test_greek_calculator_with_real_csv()
    
    # Save sample output
    output_file = "tests/actant_spot_risk/greek_test_output.csv"
    df_with_greeks.head(20).to_csv(output_file, index=False)
    print(f"\nSample output saved to: {output_file}") 