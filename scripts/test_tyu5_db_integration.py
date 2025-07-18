#!/usr/bin/env python
"""Test TYU5 Database Integration

This script tests the full integration of TYU5 calculations with database persistence.
It runs a TYU5 calculation and verifies the results are properly stored in the database.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_integration import TYU5Service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def verify_database_persistence(db_path: str = "data/output/pnl/pnl_tracker.db"):
    """Verify that TYU5 results were persisted to database."""
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("VERIFYING TYU5 DATABASE PERSISTENCE")
        print("="*60)
        
        # Check lot positions
        cursor.execute("SELECT COUNT(*) FROM lot_positions")
        lot_count = cursor.fetchone()[0]
        print(f"\nLot Positions: {lot_count} records")
        
        if lot_count > 0:
            cursor.execute("""
                SELECT symbol, trade_id, remaining_quantity, entry_price 
                FROM lot_positions 
                LIMIT 5
            """)
            print("\nSample Lot Positions:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: Trade {row[1]}, Qty={row[2]}, Price={row[3]}")
                
        # Check position Greeks
        cursor.execute("SELECT COUNT(*) FROM position_greeks")
        greek_count = cursor.fetchone()[0]
        print(f"\nPosition Greeks: {greek_count} records")
        
        if greek_count > 0:
            cursor.execute("""
                SELECT pg.calc_timestamp, p.instrument_name, pg.delta, pg.gamma, pg.vega, pg.theta
                FROM position_greeks pg
                JOIN positions p ON pg.position_id = p.id
                LIMIT 5
            """)
            print("\nSample Greeks:")
            for row in cursor.fetchall():
                print(f"  {row[1]}: Δ={row[2]:.4f}, Γ={row[3]:.4f}, ν={row[4]:.4f}, Θ={row[5]:.4f}")
                
        # Check risk scenarios
        cursor.execute("SELECT COUNT(*) FROM risk_scenarios")
        risk_count = cursor.fetchone()[0]
        print(f"\nRisk Scenarios: {risk_count} records")
        
        if risk_count > 0:
            cursor.execute("""
                SELECT symbol, COUNT(*) as scenarios, MIN(scenario_price) as min_price, 
                       MAX(scenario_price) as max_price
                FROM risk_scenarios
                GROUP BY symbol
                LIMIT 5
            """)
            print("\nRisk Scenario Summary:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} scenarios, Price range: {row[2]:.2f} - {row[3]:.2f}")
                
        # Check match history
        cursor.execute("SELECT COUNT(*) FROM match_history")
        match_count = cursor.fetchone()[0]
        print(f"\nMatch History: {match_count} records")
        
        if match_count > 0:
            cursor.execute("""
                SELECT symbol, matched_quantity, buy_price, sell_price, realized_pnl
                FROM match_history
                LIMIT 5
            """)
            print("\nSample Matches:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: Qty={row[1]}, Buy={row[2]}, Sell={row[3]}, P&L={row[4]}")
                
        # Check positions with short quantities
        cursor.execute("""
            SELECT instrument_name, position_quantity, short_quantity 
            FROM positions 
            WHERE short_quantity > 0
        """)
        shorts = cursor.fetchall()
        print(f"\nPositions with Shorts: {len(shorts)} records")
        for row in shorts:
            print(f"  {row[0]}: Net={row[1]}, Short={row[2]}")
            
        print("\n" + "="*60)
        
        return {
            'lot_positions': lot_count,
            'position_greeks': greek_count,
            'risk_scenarios': risk_count,
            'match_history': match_count,
            'short_positions': len(shorts)
        }


def main():
    """Main function to test TYU5 database integration."""
    try:
        # Create TYU5 service with database writer enabled
        logger.info("Initializing TYU5 service with database persistence...")
        service = TYU5Service(
            enable_attribution=True,  # Enable Greek attribution
            enable_db_writer=True     # Enable database persistence
        )
        
        # Run the analysis
        logger.info("Running TYU5 P&L analysis...")
        output_file = service.calculate_pnl(
            trade_date=None,  # Process all dates
            output_format="excel"
        )
        
        if output_file:
            logger.info(f"✅ Analysis complete! Excel file: {output_file}")
            
            # Verify database persistence
            results = verify_database_persistence()
            
            # Summary
            print("\nINTEGRATION TEST SUMMARY:")
            print(f"  Excel Output: {output_file}")
            print(f"  Database Records Written:")
            for table, count in results.items():
                status = "✅" if count > 0 else "❌"
                print(f"    {status} {table}: {count}")
                
            # Overall success
            if all(count > 0 for count in results.values()):
                print("\n✅ ALL TESTS PASSED - TYU5 database integration successful!")
            else:
                print("\n⚠️  Some tables have no data - check TYU5 output structure")
                
        else:
            logger.error("TYU5 analysis failed - no output file generated")
            
    except Exception as e:
        logger.error(f"Error in TYU5 database integration test: {e}")
        raise


if __name__ == "__main__":
    main() 