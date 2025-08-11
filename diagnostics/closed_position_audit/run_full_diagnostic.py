"""
Master diagnostic script to investigate closed position double-counting
Runs all diagnostic checks and provides summary
"""
import os
import sys
from datetime import datetime

# Add the diagnostic directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"   {title}")
    print("="*80 + "\n")

def main():
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " CLOSED POSITION DOUBLE-COUNTING DIAGNOSTIC SUITE".center(78) + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    print(f"\nDiagnostic run started: {datetime.now()}")
    
    # Check if trades.db exists
    if not os.path.exists('trades.db'):
        print("\n❌ ERROR: trades.db not found in current directory!")
        print("Please run this script from the project root directory.")
        return
    
    # Run duplicate check
    print_header("STEP 1: CHECKING FOR DUPLICATE TRADES")
    try:
        from check_duplicate_trades import check_duplicate_trades
        check_duplicate_trades()
    except Exception as e:
        print(f"❌ Error running duplicate check: {e}")
    
    # Run position reconciliation
    print_header("STEP 2: RECONCILING POSITIONS")
    try:
        from position_reconciliation import reconcile_positions
        reconcile_positions()
    except Exception as e:
        print(f"❌ Error running position reconciliation: {e}")
    
    # Run timeline analysis
    print_header("STEP 3: TIMELINE ANALYSIS")
    try:
        from timeline_analysis import analyze_timeline
        analyze_timeline()
    except Exception as e:
        print(f"❌ Error running timeline analysis: {e}")
    
    # Summary and recommendations
    print_header("DIAGNOSTIC SUMMARY")
    print("Based on the analysis above, please check for:")
    print("1. Duplicate trades in realized tables (Step 1)")
    print("2. Discrepancies between daily_positions and actual trades (Step 2)")
    print("3. Unusual spikes in position counts around deployment time (Step 3)")
    print("\nThe close PnL implementation involved changes to:")
    print("- PositionsAggregator (dual calculation)")
    print("- Database schema (new columns)")
    print("- FRGMonitor display logic")
    print("\nIf duplicates started appearing after these changes, focus on:")
    print("- Whether PositionsAggregator is somehow triggering re-processing")
    print("- Whether any watchers restarted and re-read files")
    print("- Whether the dual PnL calculation is causing double aggregation")
    
    print(f"\nDiagnostic run completed: {datetime.now()}")
    print("\n" + "#"*80)

if __name__ == "__main__":
    main()