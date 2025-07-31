"""
Example: Using the multi-symbol test simulation

This example shows how to rebuild the database with multiple symbols
that have different closing prices on the same day.
"""

from datetime import datetime
from test_simulation import run_comprehensive_daily_breakdown

# Example: Define close prices for multiple symbols
# Structure: {date: {symbol: price}}
multi_symbol_close_prices = {
    datetime(2025, 7, 21).date(): {
        'XCMEFFDPSX20250919U0ZN': 111.1875,  # 10-year futures
        'XCMEOCADPS20250919Q0TY4': 2.25       # Your options symbol
    },
    datetime(2025, 7, 22).date(): {
        'XCMEFFDPSX20250919U0ZN': 111.40625,
        'XCMEOCADPS20250919Q0TY4': 2.30
    },
    datetime(2025, 7, 23).date(): {
        'XCMEFFDPSX20250919U0ZN': 111.015625,
        'XCMEOCADPS20250919Q0TY4': 2.15
    },
    datetime(2025, 7, 24).date(): {
        'XCMEFFDPSX20250919U0ZN': 110.828125,
        'XCMEOCADPS20250919Q0TY4': 2.05
    },
    datetime(2025, 7, 25).date(): {
        'XCMEFFDPSX20250919U0ZN': 110.984375,
        'XCMEOCADPS20250919Q0TY4': 2.10
    }
}

def main():
    """
    Run the simulation with multi-symbol support
    """
    print("Running multi-symbol P&L simulation...")
    print("=" * 60)
    
    # Run the comprehensive daily breakdown with multiple symbols
    run_comprehensive_daily_breakdown(close_prices=multi_symbol_close_prices)
    
    print("\nMulti-symbol simulation complete!")
    print("The database has been rebuilt with separate P&L calculations for each symbol.")

if __name__ == '__main__':
    main()