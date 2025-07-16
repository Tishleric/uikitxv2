"""Test script for TYU5 P&L integration

This script tests the integration between UIKitXv2 data stores
and the TYU5 P&L calculation engine.
"""

import sys
import logging
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_integration import TYU5Service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run TYU5 integration test."""
    
    print("\n" + "="*60)
    print("TYU5 P&L INTEGRATION TEST")
    print("="*60)
    
    # Initialize service
    service = TYU5Service()
    
    # Test connection
    print("\n1. Testing database connection...")
    if service.test_connection():
        print("✓ Connection successful")
    else:
        print("✗ Connection failed")
        return
        
    # Print summary of available data
    print("\n2. Data summary:")
    service.print_summary()
    
    # Run calculation for all dates
    print("\n3. Running P&L calculation for all dates...")
    output_file = service.calculate_pnl(
        trade_date=None,
        output_format="excel"
    )
    
    if output_file:
        print(f"✓ Calculation complete: {output_file}")
    else:
        print("✗ Calculation failed")
        return
        
    # Test specific date if available
    print("\n4. Testing date-specific calculation...")
    # Get a sample date from the data
    excel_data = service.adapter.prepare_excel_data()
    if not excel_data['Trades_Input'].empty:
        sample_date = excel_data['Trades_Input']['Date'].iloc[0]
        if hasattr(sample_date, 'date'):
            sample_date = sample_date.date()
        
        print(f"   Running calculation for {sample_date}...")
        date_output = service.calculate_pnl(
            trade_date=sample_date,
            output_format="excel"
        )
        
        if date_output:
            print(f"✓ Date-specific calculation complete: {date_output}")
        else:
            print("✗ Date-specific calculation failed")
    else:
        print("   No trades available for date-specific test")
        
    # Test CSV output
    print("\n5. Testing CSV output format...")
    csv_output = service.calculate_pnl(
        trade_date=None,
        output_format="csv"
    )
    
    if csv_output:
        print(f"✓ CSV output complete: {csv_output}")
    else:
        print("✗ CSV output failed")
        
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    

if __name__ == "__main__":
    main() 