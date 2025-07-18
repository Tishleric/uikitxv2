#!/usr/bin/env python3
"""
Test script for FULLPNL full rebuild functionality.

Tests that the FULLPNLBuilder can perform a complete rebuild
of the master P&L table from all data sources.
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.fullpnl import FULLPNLBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def display_table_contents(builder):
    """Display a sample of the FULLPNL table contents."""
    cursor = builder.pnl_db.execute("""
        SELECT 
            symbol,
            ROUND(bid, 6) as bid,
            ROUND(ask, 6) as ask,
            ROUND(price, 6) as price,
            ROUND(px_last, 6) as px_last,
            ROUND(px_settle, 6) as px_settle,
            open_position,
            closed_position,
            ROUND(delta_f, 2) as delta_f,
            ROUND(vtexp, 6) as vtexp
        FROM FULLPNL
        ORDER BY symbol
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    
    # Print header
    print("\nFULLPNL Table Sample (first 10 rows):")
    print("=" * 120)
    
    # Column widths
    widths = {
        'symbol': 25,
        'bid': 10,
        'ask': 10,
        'price': 10,
        'px_last': 10,
        'px_settle': 10,
        'open_position': 12,
        'closed_position': 14,
        'delta_f': 8,
        'vtexp': 10
    }
    
    # Print column headers
    header = ""
    for col in columns:
        width = widths.get(col, 10)
        header += f"{col:<{width}} "
    print(header)
    print("-" * 120)
    
    # Print data
    for row in results:
        line = ""
        for i, col in enumerate(columns):
            value = row[i]
            width = widths.get(col, 10)
            
            if value is None:
                line += f"{'NULL':<{width}} "
            elif col in ['open_position', 'closed_position']:
                line += f"{int(value):<{width}} "
            else:
                line += f"{value:<{width}} "
        print(line)


def test_full_rebuild():
    """Test full rebuild of FULLPNL table."""
    print("\n" + "=" * 80)
    print("FULLPNL Full Rebuild Test")
    print("=" * 80)
    print(f"Start time: {datetime.now()}")
    
    # Initialize builder
    print("\n1. Initializing FULLPNLBuilder...")
    builder = FULLPNLBuilder()
    
    # Get initial state if table exists
    if builder.pnl_db.fullpnl_exists():
        print("\n2. Getting initial table state...")
        initial_summary = builder.get_table_summary()
        print(f"   Initial symbols: {initial_summary.get('total_symbols', 0)}")
    else:
        print("\n2. FULLPNL table does not exist yet")
        initial_summary = None
    
    # Perform full rebuild
    print("\n3. Performing full rebuild...")
    start_time = datetime.now()
    results = builder.build_or_update(full_rebuild=True)
    end_time = datetime.now()
    
    print(f"\n   Rebuild completed in {(end_time - start_time).total_seconds():.2f} seconds")
    
    # Display results
    print("\n4. Rebuild Results:")
    print("   " + "-" * 40)
    for key, value in results.items():
        print(f"   {key:20}: {value}")
    
    # Get final summary
    print("\n5. Final Table Summary:")
    final_summary = builder.get_table_summary()
    print("   " + "-" * 40)
    
    total = final_summary.get('total_symbols', 0)
    print(f"   Total symbols: {total}")
    
    # Coverage statistics
    coverage_fields = [
        'bid', 'ask', 'price', 'px_last', 'px_settle',
        'open_position', 'closed_position', 'delta_f', 'vtexp'
    ]
    
    for field in coverage_fields:
        count = final_summary.get(f'with_{field}', 0)
        coverage = final_summary.get(f'{field}_coverage', 0)
        print(f"   {field:15}: {count:3d} symbols ({coverage}%)")
    
    # Display sample data
    display_table_contents(builder)
    
    # Test incremental update
    print("\n\n6. Testing incremental update (no full rebuild)...")
    start_time = datetime.now()
    update_results = builder.build_or_update(full_rebuild=False)
    end_time = datetime.now()
    
    print(f"   Update completed in {(end_time - start_time).total_seconds():.2f} seconds")
    print(f"   New symbols added: {update_results.get('new_symbols', 0)}")
    
    # Close connections
    builder.close()
    print("\n7. Database connections closed")
    
    # Final status
    print("\n" + "=" * 80)
    if total > 0:
        print("✅ FULLPNL rebuild test completed successfully!")
    else:
        print("❌ FULLPNL rebuild test failed - no symbols loaded")
    print("=" * 80)
    
    return total > 0


def main():
    """Main entry point."""
    try:
        success = test_full_rebuild()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Error during rebuild test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 