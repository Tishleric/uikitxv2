"""
Test script for CSV parser module.
"""

from pathlib import Path
import pandas as pd

from csv_parser import ActantCSVParser, ActantFileMonitor, ActantDataFile, load_latest_data
from pnl_calculations import PnLCalculator


def test_csv_parser():
    """Test CSV parsing functionality."""
    print("Testing CSV Parser Module\n" + "="*50)
    
    # Test 1: Parse sample CSV file
    print("\n1. Testing direct CSV parsing:")
    parser = ActantCSVParser()
    csv_file = Path("GE_XCME.ZN_20250610_103938.csv")
    
    try:
        df = parser.parse_file(csv_file)
        print(f"✓ Successfully loaded CSV: {df.shape}")
        
        # Get expirations
        expirations = parser.get_expirations(df)
        print(f"✓ Found {len(expirations)} valid expirations:")
        for exp in expirations[:5]:  # Show first 5
            print(f"  - {exp}")
        if len(expirations) > 5:
            print(f"  ... and {len(expirations) - 5} more")
            
        # Extract shocks
        shocks = parser.extract_shock_values(df)
        print(f"✓ Shock values (bp): {shocks[:5]} ... {shocks[-5:]}")
        
    except Exception as e:
        print(f"✗ Error parsing CSV: {e}")
        return
    
    # Test 2: Parse to OptionGreeks
    print("\n2. Testing OptionGreeks conversion:")
    try:
        # Use first valid expiration
        test_exp = expirations[0]
        greeks = parser.parse_to_greeks(df, test_exp)
        print(f"✓ Successfully created OptionGreeks for {test_exp}")
        print(f"  - Underlying: ${greeks.underlying_price:.3f}")
        print(f"  - Strike: ${greeks.strike:.3f}")
        print(f"  - Forward: ${greeks.forward:.3f}")
        print(f"  - Time to expiry: {greeks.time_to_expiry:.3f} years")
        print(f"  - ATM Call price: ${greeks.call_prices[greeks.atm_index]:.2f}")
        print(f"  - ATM Put price: ${greeks.put_prices[greeks.atm_index]:.2f}")
        
    except Exception as e:
        print(f"✗ Error creating OptionGreeks: {e}")
        return
    
    # Test 3: Calculate PnLs
    print("\n3. Testing PnL calculations:")
    try:
        pnl_df = PnLCalculator.calculate_all_pnls(greeks, 'call')
        print("✓ Call option PnL summary:")
        print(f"  - Actant PnL range: [{pnl_df['actant_pnl'].min():.2f}, {pnl_df['actant_pnl'].max():.2f}]")
        print(f"  - TS0 diff range: [{pnl_df['ts0_diff'].min():.2f}, {pnl_df['ts0_diff'].max():.2f}]")
        print(f"  - TS-0.25 diff range: [{pnl_df['ts_neighbor_diff'].min():.2f}, {pnl_df['ts_neighbor_diff'].max():.2f}]")
        
        # Show sample around ATM
        atm_idx = greeks.atm_index
        sample_indices = range(max(0, atm_idx-2), min(len(pnl_df), atm_idx+3))
        print("\n  Sample data around ATM:")
        print(pnl_df.iloc[list(sample_indices)][['shock_bp', 'actant_pnl', 'ts0_diff', 'ts_neighbor_diff']].to_string())
        
    except Exception as e:
        print(f"✗ Error calculating PnLs: {e}")
        return
    
    # Test 4: File monitoring
    print("\n4. Testing file monitoring:")
    try:
        monitor = ActantFileMonitor(Path("."))
        latest = monitor.get_latest_file()
        
        if latest:
            print(f"✓ Found latest file: {latest.filepath.name}")
            print(f"  - Symbol: {latest.symbol}")
            print(f"  - Timestamp: {latest.timestamp}")
        else:
            print("✗ No Actant CSV files found")
            
    except Exception as e:
        print(f"✗ Error in file monitoring: {e}")
    
    # Test 5: Convenience function
    print("\n5. Testing convenience loader:")
    try:
        df, all_greeks = load_latest_data(Path("."), expiration="XCME.ZN")
        print(f"✓ Loaded data with {len(all_greeks)} expiration(s)")
        
    except Exception as e:
        print(f"✗ Error in convenience loader: {e}")
    
    print("\n" + "="*50)
    print("Testing complete!")


if __name__ == "__main__":
    test_csv_parser() 