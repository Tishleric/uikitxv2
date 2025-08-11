#!/usr/bin/env python3
"""
Test real-world broker to Bloomberg translations.
Shows actual inputs/outputs from rosetta stone.
"""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_real_broker_trades():
    """Test with actual broker trade descriptions."""
    rs = RosettaStone()
    
    print("REAL BROKER TRADE TRANSLATION TEST")
    print("="*70)
    
    # These are actual broker descriptions from DASONLY files
    broker_trades = [
        # Futures
        ("SEP 25 CBT 10YR TNOTE", "Future"),
        ("SEP 25 CBT 30YR TBOND", "Future"),
        
        # Options - using actual formats from broker trades
        ("CALL AUG 25 CBT 10YR TNOTE WKLY WK1 112.25", "Option"),
        ("CALL AUG 25 CBT 10YR TNOTE WED WK1 112.25", "Option"),
        ("PUT AUG 25 CBT 10YR T NOTE W1 TUES OPT 110.50", "Option"),
        
        # Test cases that should work based on calendar
        ("CALL JUL 25 CBT 10YR TNOTE 111.00", "Option"),
        ("PUT AUG 25 CBT 10YR TNOTE WKLY WK1 111.00", "Option"),
    ]
    
    print("\n1. BROKER → BLOOMBERG TRANSLATIONS:")
    print("-" * 70)
    
    for broker_symbol, trade_type in broker_trades:
        print(f"\nInput: {broker_symbol}")
        print(f"Type:  {trade_type}")
        
        try:
            # Try exact match first
            result = rs.translate(broker_symbol, "broker", "bloomberg")
            if result:
                print(f"✓ Bloomberg: {result}")
            else:
                print(f"✗ No translation found")
                
                # Debug: Check if we have the base mapping
                if trade_type == "Option":
                    # Extract base without strike for debugging
                    parts = broker_symbol.split()
                    if parts[0] in ['CALL', 'PUT']:
                        base_without_strike = ' '.join(parts[:-1])
                        lookup_key = f"broker_{broker_symbol}_to_bloomberg"
                        print(f"  Debug: Looking for key: {lookup_key}")
                        
                        # Check if similar mapping exists
                        similar = [k for k in rs.lookups.keys() if base_without_strike in k and 'broker' in k]
                        if similar:
                            print(f"  Similar mappings found:")
                            for s in similar[:3]:
                                print(f"    {s}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Test reverse translations
    print("\n\n2. BLOOMBERG → BROKER TRANSLATIONS:")
    print("-" * 70)
    
    bloomberg_symbols = [
        "TYU5 Comdty",        # Sept futures
        "USU5 Comdty",        # 30-year futures
        "VBYN25C3 111.00 Comdty",  # Monday weekly option
        "TJPN25C4 111.00 Comdty",  # Tuesday weekly option
    ]
    
    for bb_symbol in bloomberg_symbols:
        print(f"\nInput: {bb_symbol}")
        try:
            result = rs.translate(bb_symbol, "bloomberg", "broker")
            if result:
                print(f"✓ Broker: {result}")
            else:
                print(f"✗ No translation found")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Show some actual mappings
    print("\n\n3. SAMPLE BROKER MAPPINGS IN ROSETTA STONE:")
    print("-" * 70)
    
    broker_keys = [k for k in rs.lookups.keys() if k.startswith('broker_') and 'to_bloomberg' in k]
    print(f"Total broker→bloomberg mappings: {len(broker_keys)}")
    print("\nFirst 10 mappings:")
    for key in sorted(broker_keys)[:10]:
        value = rs.lookups[key]
        print(f"  {key} = {value}")


if __name__ == "__main__":
    test_real_broker_trades()