#!/usr/bin/env python3
"""Debug script to see what broker lookups are being created."""

import sys
sys.path.insert(0, '.')

from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    rs = RosettaStone()
    
    # Find all broker-related lookups
    broker_lookups = [(k, v) for k, v in rs.lookups.items() if 'broker' in k]
    
    print(f"Total broker lookups: {len(broker_lookups)}")
    print("\nSample broker lookups:")
    
    # Group by type
    broker_to_bloomberg = [(k, v) for k, v in broker_lookups if k.startswith('broker_') and 'to_bloomberg' in k]
    bloomberg_to_broker = [(k, v) for k, v in broker_lookups if k.startswith('bloomberg_') and 'to_broker' in k]
    broker_to_cme = [(k, v) for k, v in broker_lookups if k.startswith('broker_') and 'to_cme' in k]
    cme_to_broker = [(k, v) for k, v in broker_lookups if k.startswith('cme_') and 'to_broker' in k]
    
    print(f"\nBroker→Bloomberg: {len(broker_to_bloomberg)} mappings")
    for k, v in broker_to_bloomberg[:5]:
        print(f"  {k} = {v}")
    
    print(f"\nBloomberg→Broker: {len(bloomberg_to_broker)} mappings")
    for k, v in bloomberg_to_broker[:5]:
        print(f"  {k} = {v}")
        
    # Check for specific symbols
    print("\nLooking for specific mappings:")
    test_keys = [
        "broker_SEP 25 CBT 10YR TNOTE_to_bloomberg",
        "broker_CALL JUL 25 CBT 10YR TNOTE 111.00_to_bloomberg",
        "bloomberg_TYU5 Comdty_to_broker",
        "bloomberg_TYN5C111 Comdty_to_broker"
    ]
    
    for key in test_keys:
        if key in rs.lookups:
            print(f"  ✓ {key} = {rs.lookups[key]}")
        else:
            print(f"  ✗ {key} NOT FOUND")

if __name__ == "__main__":
    main()