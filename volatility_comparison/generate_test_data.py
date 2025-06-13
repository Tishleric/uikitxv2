"""
Generate test data for volatility comparison tool
Use this when you don't have access to Actant or Pricing Monkey
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_actant_test_data():
    """Generate sample Actant data CSV"""
    print("Generating test Actant data...")
    
    # Sample strikes around 110
    strikes = [110.0, 110.25, 110.5, 110.75, 111.0, 111.25, 111.5]
    
    # Different expiries
    expiries = [10, 20, 30, 45, 60]  # Days to expiry
    
    data = []
    for expiry in expiries:
        for strike in strikes:
            # Generate reasonable test volatilities
            # ATM vol around 0.08, with smile
            moneyness = abs(strike - 110.5) / 110.5
            base_vol = 0.08 + moneyness * 0.02  # Simple vol smile
            
            data.append({
                'strike': strike,
                'future_price': 110.5,
                'vol': base_vol,
                'time_to_expiry': expiry,
                'dv01': 0.063,
                'scenario': '0',  # ATM scenario
                'expiry': f"T+{expiry}d"
            })
    
    df = pd.DataFrame(data)
    df.to_csv('actant_data.csv', index=False)
    print(f"Generated {len(df)} Actant test records in actant_data.csv")
    return df


def generate_pm_test_data():
    """Generate sample Pricing Monkey data CSV"""
    print("\nGenerating test Pricing Monkey data...")
    
    # Format dates
    base_date = datetime.now()
    
    # Sample data matching Actant strikes
    strikes = [110.0, 110.25, 110.5, 110.75, 111.0, 111.25, 111.5]
    expiry_days = [10, 20, 30, 45, 60]
    
    data = []
    for days in expiry_days:
        expiry_date = (base_date + timedelta(days=days)).strftime('%m/%d/%y')
        
        for i, strike in enumerate(strikes):
            # Generate bid/ask spread
            moneyness = abs(strike - 110.5) / 110.5
            
            # Price in 64ths (higher for ATM)
            if moneyness < 0.01:  # ATM
                mid_price = 25 + np.random.normal(0, 2)
            else:
                mid_price = max(5, 25 - moneyness * 500) + np.random.normal(0, 1)
            
            spread = 1 + moneyness * 2  # Wider spread for OTM
            bid = mid_price - spread/2
            ask = mid_price + spread/2
            
            # Implied vol in bp (basis points)
            # Similar to Actant but in bp
            base_vol_bp = 800 + moneyness * 200 + np.random.normal(0, 20)
            
            data.append({
                'trade_description': f'ZN {expiry_date} C{strike:.2f}',
                'biz_days': days,
                'expiry_date': expiry_date,
                'strike': strike,
                'underlying': '110-16',  # Treasury format
                'underlying_decimal': 110.5,  # Converted
                'implied_vol_daily_bp': base_vol_bp,
                'price': (bid + ask) / 2,
                'bid': bid,
                'ask': ask,
                'mid_price_64ths': (bid + ask) / 2
            })
    
    df = pd.DataFrame(data)
    df.to_csv('pm_data.csv', index=False)
    print(f"Generated {len(df)} Pricing Monkey test records in pm_data.csv")
    return df


def main():
    """Generate all test data"""
    print("="*60)
    print("VOLATILITY COMPARISON TOOL - TEST DATA GENERATOR")
    print("="*60)
    print("\nThis will generate sample data files for testing:")
    print("- actant_data.csv")
    print("- pm_data.csv")
    print()
    
    # Check if files already exist
    if os.path.exists('actant_data.csv') or os.path.exists('pm_data.csv'):
        response = input("Data files already exist. Overwrite? (Y/N): ")
        if response.upper() != 'Y':
            print("Cancelled.")
            return
    
    # Generate data
    actant_df = generate_actant_test_data()
    pm_df = generate_pm_test_data()
    
    print("\n" + "="*60)
    print("TEST DATA GENERATION COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print(f"- actant_data.csv: {len(actant_df)} records")
    print(f"- pm_data.csv: {len(pm_df)} records")
    print("\nYou can now run:")
    print("  python volatility_calculator.py")
    print("\nTo test the volatility comparison without needing Actant/PM access.")
    

if __name__ == "__main__":
    main() 