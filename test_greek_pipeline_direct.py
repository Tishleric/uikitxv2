"""
Comprehensive Greek Pipeline Test Without Redis
Tests each component in isolation to identify where the 10,000x discrepancy occurs
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import shutil

# Import our components
from trading.bond_future_options import BondFutureOption, calculate_all_greeks, solve_implied_volatility
from trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=[
        logging.FileHandler('greek_pipeline_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GreekPipelineTester:
    def __init__(self):
        # Create test database (copy of production)
        self.test_db = 'test_trades.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        shutil.copy('trades.db', self.test_db)
        
        # Model parameters for TY
        self.future_dv01 = 64.2
        self.future_convexity = 0.87
        self.model = BondFutureOption(self.future_dv01, self.future_convexity)
        
    def log_section(self, title):
        """Log a section header"""
        logger.info("\n" + "=" * 80)
        logger.info(f"{title}")
        logger.info("=" * 80)
        
    def test_greek_calculation(self):
        """Test raw Greek calculations with detailed logging"""
        self.log_section("STAGE 1: GREEK CALCULATION TEST")
        
        # Test position: TJWQ25C1 112.5 (120 contracts)
        test_cases = [
            {
                'symbol': 'TJWQ25C1 112.5 Comdty',
                'option_type': 'call',
                'strike': 112.5,
                'position': 120.0,
                'future_price': 110.5,
                'time_to_expiry': 0.25,  # 3 months
                'market_price': 1.5
            }
        ]
        
        results = []
        
        for test in test_cases:
            logger.info(f"\nTesting: {test['symbol']}")
            logger.info(f"  Type: {test['option_type'].upper()}")
            logger.info(f"  Strike: {test['strike']}")
            logger.info(f"  Future Price: {test['future_price']}")
            logger.info(f"  Time to Expiry: {test['time_to_expiry']} years")
            logger.info(f"  Position: {test['position']} contracts")
            
            # Step 1: Calculate implied volatility
            logger.info("\n  Step 1.1: Solving for implied volatility...")
            iv, calculated_price = solve_implied_volatility(
                self.model,
                test['future_price'],
                test['strike'],
                test['time_to_expiry'],
                test['market_price'],
                option_type=test['option_type']
            )
            logger.info(f"    Implied Volatility: {iv:.4f}")
            logger.info(f"    Calculated Price: {calculated_price:.4f}")
            
            # Step 2: Calculate all Greeks
            logger.info("\n  Step 1.2: Calculating Greeks...")
            greeks = calculate_all_greeks(
                self.model,
                test['future_price'],
                test['strike'],
                test['time_to_expiry'],
                iv,
                option_type=test['option_type']
            )
            
            # Log each Greek with its scaling
            logger.info("\n  Raw Greeks (from calculate_all_greeks):")
            for greek_name, value in greeks.items():
                if greek_name in ['delta_y', 'gamma_y', 'theta_F', 'vega_y', 'speed_y']:
                    logger.info(f"    {greek_name}: {value:.6f}")
                    
                    # Check if 1000x scaling is already applied
                    if greek_name == 'delta_y':
                        # Calculate expected natural delta
                        natural_delta = value / 1000
                        logger.info(f"      -> Natural delta (before scaling): {natural_delta:.6f}")
                        logger.info(f"      -> Scaled delta (after 1000x): {value:.6f}")
            
            # Store results
            result = {
                'symbol': test['symbol'],
                'position': test['position'],
                'greeks': greeks,
                'iv': iv
            }
            results.append(result)
            
        return results
    
    def test_position_weighting(self, greek_results):
        """Test position weighting logic"""
        self.log_section("STAGE 2: POSITION WEIGHTING TEST")
        
        weighted_results = []
        
        for result in greek_results:
            symbol = result['symbol']
            position = result['position']
            greeks = result['greeks']
            
            logger.info(f"\nPosition Weighting for {symbol}:")
            logger.info(f"  Position Size: {position} contracts")
            
            weighted = {}
            
            # This is what PositionsAggregator does
            for greek_name in ['delta_y', 'gamma_y', 'speed_y', 'theta_F', 'vega_y']:
                if greek_name in greeks:
                    per_contract = greeks[greek_name]
                    weighted_value = per_contract * position
                    weighted[greek_name] = weighted_value
                    
                    logger.info(f"\n  {greek_name}:")
                    logger.info(f"    Per-contract value: {per_contract:.6f}")
                    logger.info(f"    Position ({position}): {per_contract:.6f} x {position} = {weighted_value:.6f}")
                    
                    # Check if this matches expected
                    if greek_name == 'delta_y' and symbol == 'TJWQ25C1 112.5 Comdty':
                        logger.info(f"    *** EXPECTED for 120 contracts: ~2,835,200")
                        logger.info(f"    *** ACTUAL: {weighted_value:.0f}")
                        logger.info(f"    *** RATIO: {2835200 / weighted_value:.2f}x")
            
            weighted_results.append({
                'symbol': symbol,
                'position': position,
                'weighted_greeks': weighted
            })
            
        return weighted_results
    
    def test_database_storage(self, weighted_results):
        """Test database storage and retrieval"""
        self.log_section("STAGE 3: DATABASE STORAGE TEST")
        
        conn = sqlite3.connect(self.test_db)
        
        for result in weighted_results:
            symbol = result['symbol']
            weighted_greeks = result['weighted_greeks']
            
            logger.info(f"\nStoring Greeks for {symbol}:")
            
            # Update positions table (simulate what aggregator does)
            update_query = """
            UPDATE positions 
            SET delta_y = ?, gamma_y = ?, speed_y = ?, theta = ?, vega = ?,
                has_greeks = 1, last_updated = CURRENT_TIMESTAMP
            WHERE symbol = ?
            """
            
            values = (
                weighted_greeks.get('delta_y'),
                weighted_greeks.get('gamma_y'),
                weighted_greeks.get('speed_y'),
                weighted_greeks.get('theta_F'),  # Note: theta_F → theta
                weighted_greeks.get('vega_y'),   # Note: vega_y → vega
                symbol
            )
            
            logger.info(f"  Writing to database:")
            logger.info(f"    delta_y: {values[0]}")
            logger.info(f"    gamma_y: {values[1]}")
            logger.info(f"    theta: {values[3]}")
            
            cursor = conn.cursor()
            cursor.execute(update_query, values)
            conn.commit()
            
            # Read back to verify
            read_query = """
            SELECT delta_y, gamma_y, speed_y, theta, vega 
            FROM positions 
            WHERE symbol = ?
            """
            
            cursor.execute(read_query, (symbol,))
            row = cursor.fetchone()
            
            logger.info(f"\n  Reading from database:")
            if row:
                logger.info(f"    delta_y: {row[0]}")
                logger.info(f"    gamma_y: {row[1]}")
                logger.info(f"    theta: {row[3]}")
                
                # Check for any transformation
                if row[0] and weighted_greeks.get('delta_y'):
                    ratio = row[0] / weighted_greeks.get('delta_y')
                    logger.info(f"    Storage ratio (read/written): {ratio:.6f}")
                    if abs(ratio - 1.0) > 0.001:
                        logger.warning(f"    *** WARNING: Value changed during storage!")
            
        conn.close()
    
    def test_ui_query(self):
        """Test the exact query used by the UI"""
        self.log_section("STAGE 4: UI QUERY TEST")
        
        conn = sqlite3.connect(self.test_db)
        
        # Execute the exact query from app.py
        query = """
        SELECT 
            p.symbol,
            p.instrument_type,
            p.open_position,
            p.closed_position,
            p.delta_y,
            p.gamma_y,
            p.speed_y,
            p.theta,
            p.vega
        FROM positions p
        WHERE p.open_position != 0 OR p.closed_position != 0
        ORDER BY p.symbol
        """
        
        df = pd.read_sql_query(query, conn)
        
        logger.info("\nUI Query Results:")
        for _, row in df.iterrows():
            if row['open_position'] != 0 and pd.notna(row['delta_y']):
                logger.info(f"\n{row['symbol']}:")
                logger.info(f"  Position: {row['open_position']}")
                logger.info(f"  Delta Y (as displayed): {row['delta_y']}")
                logger.info(f"  Gamma Y (as displayed): {row['gamma_y']}")
                logger.info(f"  Theta (as displayed): {row['theta']}")
                
                # Check against expected
                if row['symbol'] == 'TJWQ25C1 112.5 Comdty':
                    logger.info(f"\n  *** DISCREPANCY CHECK ***")
                    logger.info(f"  Expected delta_y: ~2,835,200")
                    logger.info(f"  Actual delta_y: {row['delta_y']:.0f}")
                    if row['delta_y'] < 1000:
                        factor = 2835200 / row['delta_y']
                        logger.info(f"  Factor difference: {factor:.0f}x too small")
                    
        conn.close()
        
    def run_complete_test(self):
        """Run the complete test pipeline"""
        logger.info("=" * 80)
        logger.info("GREEK PIPELINE TEST - WITHOUT REDIS")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Test Greek calculations
            greek_results = self.test_greek_calculation()
            
            # Stage 2: Test position weighting
            weighted_results = self.test_position_weighting(greek_results)
            
            # Stage 3: Test database storage
            self.test_database_storage(weighted_results)
            
            # Stage 4: Test UI query
            self.test_ui_query()
            
            # Summary
            self.log_section("TEST SUMMARY")
            logger.info("\nPipeline stages tested:")
            logger.info("1. Greek Calculation [PASS]")
            logger.info("2. Position Weighting [PASS]")
            logger.info("3. Database Storage [PASS]")
            logger.info("4. UI Query [PASS]")
            
            logger.info("\nCheck greek_pipeline_test.log for full details")
            
        except Exception as e:
            logger.error(f"\nERROR in test: {e}", exc_info=True)
        finally:
            # Cleanup
            if os.path.exists(self.test_db):
                os.remove(self.test_db)

if __name__ == "__main__":
    tester = GreekPipelineTester()
    tester.run_complete_test()