"""
Extract and display all derived parameters from spot risk test data.
This script shows the exact parameters that would be sent to Greek calculations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.market_prices.rosetta_stone import RosettaStone
import json

def extract_parameters():
    """Extract and display all parameters from test CSV."""
    
    # Paths
    csv_file = Path("tests/data/spot_risk_test/bav_analysis_20250801_140005_chunk_01_of_16.csv")
    vtexp_file = Path("tests/data/spot_risk_test/vtexp_20250802_120234.csv")
    
    # Load VTEXP data
    vtexp_df = pd.read_csv(vtexp_file)
    vtexp_data = vtexp_df.set_index('symbol')['vtexp'].to_dict()
    
    print("=" * 80)
    print("SPOT RISK PARAMETER EXTRACTION REPORT")
    print("=" * 80)
    
    # Parse CSV with all processing
    df = parse_spot_risk_csv(csv_file, calculate_time_to_expiry=True, vtexp_data=vtexp_data)
    
    # Extract future price
    future_rows = df[df['itype'].str.upper() == 'F']
    future_price = None
    
    print("\n1. FUTURE IDENTIFICATION")
    print("-" * 40)
    
    if len(future_rows) > 0:
        future = future_rows.iloc[0]
        future_price = future['midpoint_price']
        
        print(f"Actant Symbol:     {future['key']}")
        print(f"Bloomberg Symbol:  {future['bloomberg_symbol']}")
        print(f"Bid Price:         {future['bid']}")
        print(f"Ask Price:         {future['ask']}")
        print(f"Midpoint Price:    {future_price}")
        print(f"Price Source:      {future['price_source']}")
        if 'adjtheor' in future:
            print(f"Adj Theor Price:   {future['adjtheor']}")
    
    # Extract options
    options_df = df[df['itype'].str.upper().isin(['C', 'P'])]
    
    print(f"\n2. OPTIONS SUMMARY")
    print("-" * 40)
    print(f"Total Options:     {len(options_df)}")
    print(f"Call Options:      {len(options_df[options_df['itype'].str.upper() == 'C'])}")
    print(f"Put Options:       {len(options_df[options_df['itype'].str.upper() == 'P'])}")
    
    print("\n3. DETAILED OPTION PARAMETERS")
    print("-" * 40)
    
    # Process each option
    greek_inputs = []
    
    for idx, option in options_df.iterrows():
        option_type = 'call' if option['itype'].upper() == 'C' else 'put'
        
        params = {
            'actant_symbol': option['key'],
            'bloomberg_symbol': option['bloomberg_symbol'],
            'option_type': option_type,
            'strike': option['strike'],
            'market_price': option['midpoint_price'],
            'price_source': option['price_source'],
            'future_price': future_price,
            'time_to_expiry': option.get('vtexp'),
            'expiry_date': option.get('expiry_date'),
            'bid': option.get('bid'),
            'ask': option.get('ask'),
            'adjtheor': option.get('adjtheor')
        }
        
        greek_inputs.append(params)
        
        print(f"\nOption #{idx + 1}:")
        print(f"  Actant Symbol:    {params['actant_symbol']}")
        print(f"  Bloomberg Symbol: {params['bloomberg_symbol']}")
        print(f"  Type:             {params['option_type'].upper()}")
        print(f"  Strike:           {params['strike']}")
        print(f"  Market Price:     {params['market_price']:.6f}")
        print(f"  Price Source:     {params['price_source']}")
        print(f"  Bid/Ask:          {params['bid']:.6f} / {params['ask']:.6f}")
        if pd.notna(params['adjtheor']):
            print(f"  Adj Theor:        {params['adjtheor']:.6f}")
        print(f"  Future Price:     {params['future_price']:.6f}")
        print(f"  Time to Expiry:   {params['time_to_expiry']:.6f} years")
        print(f"  Expiry Date:      {params['expiry_date']}")
    
    print("\n4. GREEK API INPUT PARAMETERS")
    print("-" * 40)
    print("Parameters that would be sent to bond_future_options API:")
    
    # Show what would be sent to API
    for i, params in enumerate(greek_inputs):
        print(f"\nAPI Call #{i + 1}:")
        print(f"  F (Future Price):     {params['future_price']:.6f}")
        print(f"  K (Strike):           {params['strike']:.6f}")
        print(f"  T (Time to Expiry):   {params['time_to_expiry']:.6f}")
        print(f"  market_price:         {params['market_price']:.6f}")
        print(f"  option_type:          '{params['option_type']}'")
        
    # Additional calculations
    print("\n5. MONEYNESS ANALYSIS")
    print("-" * 40)
    
    for params in greek_inputs:
        moneyness = params['strike'] - params['future_price']
        moneyness_pct = (params['strike'] / params['future_price'] - 1) * 100
        
        if params['option_type'] == 'call':
            if moneyness < 0:
                status = "ITM (In-the-money)"
            elif moneyness > 0:
                status = "OTM (Out-of-the-money)"
            else:
                status = "ATM (At-the-money)"
        else:  # put
            if moneyness > 0:
                status = "ITM (In-the-money)"
            elif moneyness < 0:
                status = "OTM (Out-of-the-money)"
            else:
                status = "ATM (At-the-money)"
                
        print(f"\n{params['bloomberg_symbol']}:")
        print(f"  Strike - Future:  {moneyness:.6f}")
        print(f"  Moneyness %:      {moneyness_pct:.2f}%")
        print(f"  Status:           {status}")
    
    # Model parameters
    print("\n6. MODEL PARAMETERS (DEFAULTS)")
    print("-" * 40)
    print(f"  Model:            'bachelier_v1'")
    print(f"  Future DV01:      64.2 (for ZN)")
    print(f"  Future Convexity: 0.0042")
    print(f"  Yield Level:      0.05")
    
    # Save to JSON for reference
    output_file = Path("tests/data/spot_risk_test/extracted_parameters.json")
    with open(output_file, 'w') as f:
        json.dump({
            'future': {
                'actant_symbol': future_rows.iloc[0]['key'] if len(future_rows) > 0 else None,
                'bloomberg_symbol': future_rows.iloc[0]['bloomberg_symbol'] if len(future_rows) > 0 else None,
                'price': float(future_price) if future_price else None
            },
            'options': [{
                'actant_symbol': p['actant_symbol'],
                'bloomberg_symbol': p['bloomberg_symbol'],
                'option_type': p['option_type'],
                'strike': float(p['strike']),
                'market_price': float(p['market_price']),
                'future_price': float(p['future_price']),
                'time_to_expiry': float(p['time_to_expiry'])
            } for p in greek_inputs]
        }, f, indent=2)
    
    print(f"\n7. OUTPUT SAVED")
    print("-" * 40)
    print(f"Parameters saved to: {output_file}")
    
    return df, greek_inputs

if __name__ == "__main__":
    extract_parameters()