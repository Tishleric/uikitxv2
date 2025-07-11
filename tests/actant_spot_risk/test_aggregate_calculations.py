"""Test aggregate calculations for spot risk data."""

import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from lib.trading.actant.spot_risk import SpotRiskGreekCalculator


def create_test_data():
    """Create test DataFrame with futures and options data."""
    
    # Create sample data with multiple expiries
    data = [
        # Future
        {
            'key': 'ZN_MAR25_F', 
            'itype': 'F',
            'expiry_date': '2025-03-15',
            'strike': 'INVALID',
            'pos.position': 100,
            'midpoint_price': 110.875,
            'implied_vol': np.nan,
            'vtexp': 0.25,
        },
        # Options for MAR25
        {
            'key': 'ZN_MAR25_110C',
            'itype': 'C',
            'expiry_date': '2025-03-15', 
            'strike': 110.0,
            'pos.position': 50,
            'midpoint_price': 1.5,
            'implied_vol': 0.75,
            'vtexp': 0.25,
            'delta_F': 0.55,
            'delta_y': 0.54,
            'gamma_F': 0.002,
            'gamma_y': 0.0019,
            'vega_price': 0.015,
            'vega_y': 0.014,
            'theta_F': -0.05,
            'theta_y': -0.048,
        },
        {
            'key': 'ZN_MAR25_111P',
            'itype': 'P',
            'expiry_date': '2025-03-15',
            'strike': 111.0,
            'pos.position': -30,
            'midpoint_price': 1.2,
            'implied_vol': 0.73,
            'vtexp': 0.25,
            'delta_F': -0.45,
            'delta_y': -0.44,
            'gamma_F': 0.0018,
            'gamma_y': 0.0017,
            'vega_price': 0.013,
            'vega_y': 0.012,
            'theta_F': -0.04,
            'theta_y': -0.038,
        },
        # Option with zero position (should be excluded from aggregates)
        {
            'key': 'ZN_MAR25_109C',
            'itype': 'C',
            'expiry_date': '2025-03-15',
            'strike': 109.0,
            'pos.position': 0,  # Zero position
            'midpoint_price': 2.5,
            'implied_vol': 0.77,
            'vtexp': 0.25,
            'delta_F': 0.65,
            'delta_y': 0.64,
            'gamma_F': 0.0022,
            'gamma_y': 0.0021,
            'vega_price': 0.018,
            'vega_y': 0.017,
            'theta_F': -0.06,
            'theta_y': -0.058,
        },
        # Options for JUN25
        {
            'key': 'ZN_JUN25_112C',
            'itype': 'C',
            'expiry_date': '2025-06-15',
            'strike': 112.0,
            'pos.position': 20,
            'midpoint_price': 2.0,
            'implied_vol': 0.8,
            'vtexp': 0.5,
            'delta_F': 0.52,
            'delta_y': 0.51,
            'gamma_F': 0.0015,
            'gamma_y': 0.0014,
            'vega_price': 0.02,
            'vega_y': 0.019,
            'theta_F': -0.03,
            'theta_y': -0.028,
        }
    ]
    
    df = pd.DataFrame(data)
    
    # Add more Greek columns
    for col in ['volga_price', 'vanna_F_price', 'vanna_y_price', 'charm_F', 'charm_y',
                'speed_F', 'speed_y', 'color_F', 'color_y', 'ultima', 'zomma']:
        df[col] = np.random.uniform(0.0001, 0.01, len(df))
    
    # Set hardcoded futures Greeks
    futures_mask = df['itype'] == 'F'
    df.loc[futures_mask, 'delta_F'] = 63.0
    df.loc[futures_mask, 'gamma_F'] = 0.0042
    df.loc[futures_mask, 'delta_y'] = 63.0 * 9.34 / 1000.0  # DV01 conversion
    df.loc[futures_mask, 'gamma_y'] = 0.0042 * (9.34 / 1000.0) ** 2
    df.loc[futures_mask, 'vega_price'] = 0.0
    df.loc[futures_mask, 'vega_y'] = 0.0
    df.loc[futures_mask, 'theta_F'] = 0.0
    df.loc[futures_mask, 'theta_y'] = 0.0
    
    return df


def test_calculate_aggregates():
    """Test the calculate_aggregates method."""
    calculator = SpotRiskGreekCalculator()
    
    # Create test data
    df = create_test_data()
    
    # Calculate aggregates
    df_with_aggregates = calculator.calculate_aggregates(df)
    
    # Verify aggregate rows were added
    aggregate_rows = df_with_aggregates[df_with_aggregates['key'].str.startswith('NET_')]
    assert len(aggregate_rows) == 3, f"Expected 3 aggregate rows (NET_FUTURES, NET_OPTIONS_F, NET_OPTIONS_Y), got {len(aggregate_rows)}"
    
    # Check aggregate keys
    expected_keys = {'NET_FUTURES', 'NET_OPTIONS_F', 'NET_OPTIONS_Y'}
    actual_keys = set(aggregate_rows['key'].tolist())
    assert actual_keys == expected_keys, f"Unexpected aggregate keys: {actual_keys}"
    
    # Verify NET_FUTURES aggregates
    net_futures_df = aggregate_rows[aggregate_rows['key'] == 'NET_FUTURES']
    net_futures = net_futures_df.iloc[0]
    assert net_futures['pos.position'] == 100, "Futures position should be 100"
    assert net_futures['delta_F'] == 63.0, "Futures delta_F should be 63 (simple addition)"
    assert net_futures['gamma_F'] == 0.0042, "Futures gamma_F should be 0.0042 (simple addition)"
    
    # Verify NET_OPTIONS_F aggregates (simple addition of Greeks)
    net_options_f = aggregate_rows[aggregate_rows['key'] == 'NET_OPTIONS_F'].iloc[0]
    
    # Sum positions for options with non-zero positions (excluding ZN_MAR25_109C)
    expected_option_position = 50 + (-30) + 20  
    assert net_options_f['pos.position'] == expected_option_position, \
        f"Options position should be {expected_option_position}, got {net_options_f['pos.position']}"
    
    # Check delta aggregation (simple addition, not position-weighted)
    expected_delta_f = 0.55 + (-0.45) + 0.52  # Simple sum of deltas
    assert abs(net_options_f['delta_F'] - expected_delta_f) < 0.0001, \
        f"Options delta_F should be {expected_delta_f} (simple addition), got {net_options_f['delta_F']}"
    
    # Check gamma aggregation
    expected_gamma_f = 0.002 + 0.0018 + 0.0015  # Simple sum
    assert abs(net_options_f['gamma_F'] - expected_gamma_f) < 0.0001, \
        f"Options gamma_F should be {expected_gamma_f}, got {net_options_f['gamma_F']}"
    
    # Verify NET_OPTIONS_Y aggregates
    net_options_y = aggregate_rows[aggregate_rows['key'] == 'NET_OPTIONS_Y'].iloc[0]
    expected_delta_y = 0.54 + (-0.44) + 0.51  # Simple sum of Y-space deltas
    assert abs(net_options_y['delta_y'] - expected_delta_y) < 0.0001, \
        f"Options delta_y should be {expected_delta_y}, got {net_options_y['delta_y']}"
    
    # Verify that 'itype' is 'NET' for all aggregate rows
    assert (aggregate_rows['itype'] == 'NET').all(), "All aggregate rows should have itype='NET'"
    
    print("Aggregate calculations test passed!")
    print("\nAggregate rows:")
    print(aggregate_rows[['key', 'pos.position', 'delta_F', 'delta_y', 'gamma_F', 'vega_price']])
    
    return df_with_aggregates


def test_aggregates_with_no_positions():
    """Test aggregate calculations when there are no positions."""
    calculator = SpotRiskGreekCalculator()
    
    # Create data with zero positions
    df = create_test_data()
    df['pos.position'] = 0
    
    # Calculate aggregates
    df_with_aggregates = calculator.calculate_aggregates(df)
    
    # When all positions are zero, no aggregate rows should be created
    aggregate_rows = df_with_aggregates[df_with_aggregates['key'].str.startswith('NET_')]
    assert len(aggregate_rows) == 0, "Should not create aggregate rows when all positions are zero"
    
    print("Zero positions test passed!")


def test_greek_space_filtering():
    """Test that NET_OPTIONS rows are filtered based on Greek space."""
    from apps.dashboards.spot_risk.callbacks import apply_spot_risk_filters_with_greek_space
    
    # Create test data with aggregates
    calculator = SpotRiskGreekCalculator()
    df = create_test_data()
    df_with_aggregates = calculator.calculate_aggregates(df)
    
    # Convert to dict format for dashboard
    data_dict = df_with_aggregates.to_dict('records')
    
    # Test F-space filtering
    f_space_data = apply_spot_risk_filters_with_greek_space(
        data_dict, 'ALL', 'ALL', [100, 120], 'F'
    )
    
    # Check which NET rows are present
    f_space_net_keys = [row['key'] for row in f_space_data if row['key'].startswith('NET_')]
    assert 'NET_FUTURES' in f_space_net_keys, "NET_FUTURES should be present in F-space"
    assert 'NET_OPTIONS_F' in f_space_net_keys, "NET_OPTIONS_F should be present in F-space"
    assert 'NET_OPTIONS_Y' not in f_space_net_keys, "NET_OPTIONS_Y should NOT be present in F-space"
    
    # Test Y-space filtering
    y_space_data = apply_spot_risk_filters_with_greek_space(
        data_dict, 'ALL', 'ALL', [100, 120], 'y'
    )
    
    # Check which NET rows are present
    y_space_net_keys = [row['key'] for row in y_space_data if row['key'].startswith('NET_')]
    assert 'NET_FUTURES' in y_space_net_keys, "NET_FUTURES should be present in Y-space"
    assert 'NET_OPTIONS_Y' in y_space_net_keys, "NET_OPTIONS_Y should be present in Y-space"
    assert 'NET_OPTIONS_F' not in y_space_net_keys, "NET_OPTIONS_F should NOT be present in Y-space"
    
    print("Greek space filtering test passed!")


if __name__ == "__main__":
    print("Testing aggregate calculations...")
    test_calculate_aggregates()
    
    print("\n" + "="*60 + "\n")
    
    print("Testing aggregates with no positions...")
    test_aggregates_with_no_positions()
    
    print("\n" + "="*60 + "\n")
    
    print("Testing Greek space filtering...")
    test_greek_space_filtering() 