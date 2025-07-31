"""
Diagnostic script to compare symbol translations from different source formats.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    """Run the translation comparison."""
    
    trade_symbol = 'XCMEOCADPS20250801Q0ZN1/111.75'
    risk_symbol = 'XCME.ZN1.01AUG25.111:75.C'
    
    translator = RosettaStone()
    
    print("="*50)
    print("Symbol Translation Verification")
    print("="*50)
    
    # Translate from ActantTrades format
    trade_to_bloomberg = translator.translate(trade_symbol, 'actanttrades', 'bloomberg')
    print(f"\nTrade Ledger Symbol ('actanttrades'):")
    print(f"  Input:  {trade_symbol}")
    print(f"  Output: {trade_to_bloomberg}")
    
    # Translate from ActantRisk format
    risk_to_bloomberg = translator.translate(risk_symbol, 'actantrisk', 'bloomberg')
    print(f"\nSpot Risk Symbol ('actantrisk'):")
    print(f"  Input:  {risk_symbol}")
    print(f"  Output: {risk_to_bloomberg}")
    
    print("\n" + "="*50)
    
    if trade_to_bloomberg == risk_to_bloomberg:
        print("\nConclusion: SUCCESS - The symbols translate identically.")
    else:
        print("\nConclusion: FAILURE - The symbols translate to different Bloomberg formats.")
        print("This is the root cause of the merge issue.")

if __name__ == '__main__':
    main()
