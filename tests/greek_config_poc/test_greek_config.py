"""
Test Suite for Greek Configuration
Validates that the configuration works as intended.
"""

import os
import sys
import pandas as pd
import numpy as np
import sqlite3
import json
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from greek_config import GreekConfiguration, REQUIRED_FOR_POSITIONS
from mock_calculator import MockGreekCalculator


def create_test_dataframe(num_options=10):
    """Create a test DataFrame with mock spot risk data."""
    data = []
    
    # Add a future
    data.append({
        'instrument_key': 'ZNH5',
        'instrument_type': 'FUTURE',
        'strike': np.nan,
        'position': 100,
        'midpoint_price': 110.5
    })
    
    # Add options
    for i in range(num_options):
        option_type = 'CALL' if i % 2 == 0 else 'PUT'
        data.append({
            'instrument_key': f'ZNH5_{110 + i}_{option_type[0]}',
            'instrument_type': option_type,
            'strike': 110 + i,
            'position': 10 * (i + 1),
            'midpoint_price': 0.5 + i * 0.1
        })
    
    return pd.DataFrame(data)


def test_default_configuration():
    """Test 1: Default configuration enables required Greeks."""
    print("\n" + "="*50)
    print("TEST 1: Default Configuration")
    print("="*50)
    
    config = GreekConfiguration()
    enabled = config.get_enabled_greeks()
    
    print(config.summary())
    
    # Check that default Greeks are enabled
    expected_defaults = {'delta_F', 'delta_y', 'gamma_F', 'gamma_y', 'speed_F', 'speed_y', 'theta_F'}
    assert expected_defaults.issubset(enabled), f"Missing default Greeks: {expected_defaults - enabled}"
    
    print("✓ Default Greeks are enabled")
    
    # Check that expensive Greeks are disabled by default
    expensive_greeks = {'ultima', 'zomma', 'volga_price'}
    assert not any(config.is_enabled(g) for g in expensive_greeks), "Expensive Greeks should be disabled by default"
    
    print("✓ Expensive Greeks are disabled by default")


def test_minimal_configuration():
    """Test 2: Minimal configuration with only required Greeks."""
    print("\n" + "="*50)
    print("TEST 2: Minimal Configuration")
    print("="*50)
    
    # Set environment variable for minimal Greeks
    os.environ['SPOT_RISK_GREEKS_ENABLED'] = 'delta_F,delta_y,gamma_F,gamma_y,speed_F,theta_F,vega_y'
    
    config = GreekConfiguration()
    enabled = config.get_enabled_greeks()
    
    print(config.summary())
    
    # Check that only minimal Greeks are enabled
    assert len(enabled) <= 8, f"Too many Greeks enabled: {enabled}"
    
    # Check that required position Greeks are included
    for greek in REQUIRED_FOR_POSITIONS:
        if greek == 'speed_y':
            assert 'speed_F' in enabled, "speed_F must be enabled for speed_y"
        else:
            assert config.is_enabled(greek), f"Required Greek {greek} is not enabled"
    
    print("✓ Minimal configuration includes all required Greeks")
    
    # Clean up
    del os.environ['SPOT_RISK_GREEKS_ENABLED']


def test_greek_calculation_with_config():
    """Test 3: Greek calculation respects configuration."""
    print("\n" + "="*50)
    print("TEST 3: Greek Calculation with Configuration")
    print("="*50)
    
    # Create test data
    df = create_test_dataframe(num_options=5)
    
    # Test with full Greeks
    print("\n--- Full Greek Calculation ---")
    full_config = GreekConfiguration({greek: True for greek in GreekConfiguration().enabled_greeks})
    calc_full = MockGreekCalculator(full_config)
    df_full, results_full = calc_full.calculate_greeks(df.copy())
    
    # Test with minimal Greeks
    print("\n--- Minimal Greek Calculation ---")
    minimal_config = GreekConfiguration({
        'delta_F': True, 'delta_y': True,
        'gamma_F': True, 'gamma_y': True,
        'speed_F': True, 'theta_F': True,
        'vega_y': True,  # Required for positions
        # All others False
        'vega_price': False, 'volga_price': False,
        'vanna_F_price': False, 'charm_F': False,
        'color_F': False, 'ultima': False, 'zomma': False
    })
    calc_minimal = MockGreekCalculator(minimal_config)
    df_minimal, results_minimal = calc_minimal.calculate_greeks(df.copy())
    
    # Verify disabled Greeks are NaN
    options_mask = df_minimal['instrument_type'].isin(['CALL', 'PUT'])
    disabled_greeks = minimal_config.get_disabled_greeks()
    
    for greek in disabled_greeks:
        if greek in df_minimal.columns and greek != 'speed_y':  # speed_y is derived
            assert df_minimal.loc[options_mask, greek].isna().all(), f"{greek} should be NaN when disabled"
    
    print("✓ Disabled Greeks are correctly set to NaN")
    
    # Verify enabled Greeks have values
    enabled_greeks = minimal_config.get_enabled_greeks()
    for greek in enabled_greeks:
        if greek in df_minimal.columns:
            has_values = df_minimal.loc[options_mask, greek].notna().any()
            assert has_values, f"{greek} should have values when enabled"
    
    print("✓ Enabled Greeks have calculated values")
    
    return df_full, df_minimal


def test_aggregation_with_missing_greeks():
    """Test 4: Aggregation handles missing Greeks gracefully."""
    print("\n" + "="*50)
    print("TEST 4: Aggregation with Missing Greeks")
    print("="*50)
    
    # Create test data with minimal Greeks
    df = create_test_dataframe(num_options=5)
    
    minimal_config = GreekConfiguration({
        'delta_F': True, 'delta_y': True,
        'gamma_F': True, 'gamma_y': True,
        'speed_F': True, 'theta_F': True,
        'vega_y': True
    })
    
    calc = MockGreekCalculator(minimal_config)
    df_calc, _ = calc.calculate_greeks(df)
    
    # Test aggregation
    df_agg = calc.calculate_aggregates(df_calc)
    
    # Check that aggregate row exists
    agg_rows = df_agg[df_agg['instrument_key'] == 'NET_OPTIONS_F']
    assert len(agg_rows) == 1, "Should have one aggregate row"
    
    agg_row = agg_rows.iloc[0]
    
    # Check enabled Greeks are aggregated
    assert not pd.isna(agg_row['delta_F']), "delta_F should be aggregated"
    assert not pd.isna(agg_row['gamma_F']), "gamma_F should be aggregated"
    
    # Check disabled Greeks are NaN
    assert pd.isna(agg_row['ultima']), "ultima should be NaN when disabled"
    assert pd.isna(agg_row['zomma']), "zomma should be NaN when disabled"
    
    print("✓ Aggregation correctly handles missing Greeks")


def test_database_compatibility():
    """Test 5: Database operations handle NULL Greeks."""
    print("\n" + "="*50)
    print("TEST 5: Database Compatibility")
    print("="*50)
    
    # Create test database
    db_path = "test_greeks.db"
    conn = sqlite3.connect(db_path)
    
    # Create simplified spot_risk_calculated table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS spot_risk_calculated (
        id INTEGER PRIMARY KEY,
        instrument_key TEXT,
        delta_F REAL,
        delta_y REAL,
        gamma_F REAL,
        gamma_y REAL,
        ultima REAL,
        zomma REAL
    )
    """)
    
    # Test data with some NULL Greeks
    test_data = [
        ('OPT1', 0.5, 31.5, 0.02, 1.26, None, None),  # Missing ultima, zomma
        ('OPT2', 0.3, 18.9, 0.01, 0.63, 0.001, 0.002),  # All Greeks present
        ('OPT3', 0.7, 44.1, 0.03, 1.89, None, None),  # Missing ultima, zomma
    ]
    
    # Insert with NULL values
    conn.executemany(
        "INSERT INTO spot_risk_calculated (instrument_key, delta_F, delta_y, gamma_F, gamma_y, ultima, zomma) VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_data
    )
    conn.commit()
    
    # Test aggregation query with NULL handling
    result = conn.execute("""
    SELECT 
        'AGGREGATE' as instrument_key,
        SUM(delta_F) as total_delta_F,
        SUM(delta_y) as total_delta_y,
        SUM(gamma_F) as total_gamma_F,
        SUM(gamma_y) as total_gamma_y,
        SUM(ultima) as total_ultima,
        SUM(zomma) as total_zomma,
        COUNT(*) as row_count,
        COUNT(ultima) as ultima_count,
        COUNT(zomma) as zomma_count
    FROM spot_risk_calculated
    """).fetchone()
    
    print(f"Aggregation results:")
    print(f"- Total delta_F: {result[1]:.2f}")
    print(f"- Total delta_y: {result[2]:.2f}")  
    print(f"- Total ultima: {result[5]}")  # Should handle NULLs
    print(f"- Rows with ultima: {result[8]}/{result[7]}")
    
    assert result[1] == 1.5, "delta_F sum incorrect"
    assert result[5] == 0.001, "ultima sum should skip NULLs"
    assert result[8] == 1, "Only 1 row has ultima value"
    
    print("✓ Database aggregation handles NULL Greeks correctly")
    
    conn.close()
    os.remove(db_path)


def test_performance_comparison():
    """Test 6: Performance comparison between full and minimal Greeks."""
    print("\n" + "="*50)
    print("TEST 6: Performance Comparison")
    print("="*50)
    
    # Create larger test dataset
    df = create_test_dataframe(num_options=20)
    
    # Full Greeks calculation
    import time
    full_config = GreekConfiguration({greek: True for greek in GreekConfiguration().enabled_greeks})
    calc_full = MockGreekCalculator(full_config)
    
    start = time.time()
    df_full, _ = calc_full.calculate_greeks(df.copy())
    full_time = time.time() - start
    
    # Minimal Greeks calculation  
    minimal_config = GreekConfiguration({
        'delta_F': True, 'delta_y': True,
        'gamma_F': True, 'gamma_y': True,
        'speed_F': True, 'theta_F': True,
        'vega_y': True
    })
    calc_minimal = MockGreekCalculator(minimal_config)
    
    start = time.time()
    df_minimal, _ = calc_minimal.calculate_greeks(df.copy())
    minimal_time = time.time() - start
    
    print(f"\nPerformance Results:")
    print(f"- Full Greeks ({len(full_config.get_enabled_greeks())} enabled): {full_time:.3f}s")
    print(f"- Minimal Greeks ({len(minimal_config.get_enabled_greeks())} enabled): {minimal_time:.3f}s")
    print(f"- Speed improvement: {(1 - minimal_time/full_time)*100:.1f}%")
    
    assert minimal_time < full_time, "Minimal Greeks should be faster"
    print("✓ Minimal Greek calculation is faster")


def save_test_results(df_full, df_minimal):
    """Save test results for inspection."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save DataFrames
    df_full.to_csv(output_dir / "greeks_full.csv", index=False)
    df_minimal.to_csv(output_dir / "greeks_minimal.csv", index=False)
    
    # Save comparison
    comparison = {
        'full_greeks': {
            'count': len([c for c in df_full.columns if c.endswith(('_F', '_y', 'price', 'ultima', 'zomma'))]),
            'columns': sorted([c for c in df_full.columns if not df_full[c].isna().all()])
        },
        'minimal_greeks': {
            'count': len([c for c in df_minimal.columns if not df_minimal[c].isna().all() and c.endswith(('_F', '_y', 'price', 'ultima', 'zomma'))]),
            'columns': sorted([c for c in df_minimal.columns if not df_minimal[c].isna().all()])
        }
    }
    
    with open(output_dir / "comparison.json", 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\nTest results saved to: {output_dir}")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("GREEK CONFIGURATION TEST SUITE")
    print("="*70)
    
    try:
        # Run tests
        test_default_configuration()
        test_minimal_configuration()
        df_full, df_minimal = test_greek_calculation_with_config()
        test_aggregation_with_missing_greeks()
        test_database_compatibility()
        test_performance_comparison()
        
        # Save results
        save_test_results(df_full, df_minimal)
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✓")
        print("="*70)
        print("\nThe Greek configuration system works as intended:")
        print("1. ✓ Configuration correctly enables/disables Greeks")
        print("2. ✓ Required Greeks for positions are always enabled")
        print("3. ✓ Disabled Greeks are set to NaN (not calculated)")
        print("4. ✓ Aggregation handles missing Greeks gracefully")
        print("5. ✓ Database operations support NULL Greeks")
        print("6. ✓ Performance improves with fewer Greeks")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()