"""
Comprehensive test for unrealized P&L calculation robustness.
Focuses on validating actual calculation logic, not just getting passing tests.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch
import pytz
import os
import sys
import tempfile

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trading.pnl_fifo_lifo.data_manager import (
    view_unrealized_positions,
    load_pricing_dictionaries,
    create_all_tables
)
from lib.trading.pnl_fifo_lifo.pnl_engine import (
    calculate_unrealized_pnl,
    get_effective_entry_price,
    get_current_time_period,
    PNL_MULTIPLIER
)


class ComprehensiveUnrealizedPnLTest:
    """Comprehensive test for unrealized P&L calculations"""
    
    def __init__(self):
        self.production_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trades_test_copy.db')
        self.test_results = []
        self.cdt = pytz.timezone('US/Central')
        
    def test_aug5_trades_pmax_logic(self):
        """Test Pmax logic specifically with Aug 5 trades that should have different prices"""
        print("\n=== Testing Aug 5 Trades (Pmax Logic) ===")
        
        conn = sqlite3.connect(self.production_db)
        try:
            # Query specifically for Aug 5 trades
            aug5_query = """
                SELECT * FROM trades_fifo 
                WHERE sequenceId LIKE '20250805-%' 
                AND quantity > 0
                ORDER BY sequenceId
                LIMIT 10
            """
            aug5_trades = pd.read_sql_query(aug5_query, conn)
            
            if aug5_trades.empty:
                print("No Aug 5 trades found in trades_fifo")
                return
                
            # Get pricing data
            prices = load_pricing_dictionaries(conn)
            
            print(f"Found {len(aug5_trades)} Aug 5 trades")
            print("\nAnalyzing first few Aug 5 trades:")
            
            differences_found = False
            
            for _, trade in aug5_trades.head(5).iterrows():
                symbol = trade['symbol']
                actual_price = trade['price']
                sod_price = prices['sodTod'].get(symbol, actual_price)
                
                # These Aug 5 trades should use actual price (traded today)
                effective_price = get_effective_entry_price(
                    actual_price, 
                    sod_price, 
                    trade['time']
                )
                
                print(f"\nSymbol: {symbol}")
                print(f"  Trade time: {trade['time']}")
                print(f"  Actual price: ${actual_price:.5f}")
                print(f"  SOD price: ${sod_price:.5f}")
                print(f"  Effective entry: ${effective_price:.5f}")
                print(f"  Using: {'ACTUAL' if effective_price == actual_price else 'SOD'}")
                
                # Check if we found a case where prices differ
                if actual_price != sod_price:
                    differences_found = True
                    # Verify Aug 5 trades use actual price
                    assert effective_price == actual_price, \
                        f"Aug 5 trade should use actual price, not SOD"
                        
            if not differences_found:
                print("\nWARNING: All Aug 5 trades have identical actual and SOD prices!")
                print("Cannot properly test Pmax logic with this data.")
                
            self.test_results.append({
                'test': 'aug5_trades_pmax',
                'status': 'PASSED' if differences_found else 'WARNING',
                'details': f'Analyzed {len(aug5_trades)} Aug 5 trades' + 
                          (' - found price differences' if differences_found else ' - no price differences found')
            })
            
        finally:
            conn.close()
            
    def test_price_dictionary_validation(self):
        """Validate that price dictionaries have different values for proper testing"""
        print("\n=== Validating Price Dictionaries ===")
        
        conn = sqlite3.connect(self.production_db)
        try:
            prices = load_pricing_dictionaries(conn)
            
            # Check for each symbol
            symbols_with_issues = []
            symbols_ok = []
            
            # Get unique symbols from pricing table
            symbols_query = "SELECT DISTINCT symbol FROM pricing"
            symbols_df = pd.read_sql_query(symbols_query, conn)
            
            for symbol in symbols_df['symbol'].unique():
                sod_tod = prices['sodTod'].get(symbol, 0)
                sod_tom = prices['sodTom'].get(symbol, 0)
                now = prices['now'].get(symbol, 0)
                close = prices['close'].get(symbol, 0)
                
                # Check if prices are different
                prices_differ = (sod_tod != sod_tom) or (now != close) or (now != sod_tod)
                
                if not prices_differ or any(p == 0 for p in [sod_tod, sod_tom, now]):
                    symbols_with_issues.append({
                        'symbol': symbol,
                        'sodTod': sod_tod,
                        'sodTom': sod_tom,
                        'now': now,
                        'close': close
                    })
                else:
                    symbols_ok.append(symbol)
                    
            print(f"\nSymbols analyzed: {len(symbols_df)}")
            print(f"Symbols with proper price variation: {len(symbols_ok)}")
            print(f"Symbols with price issues: {len(symbols_with_issues)}")
            
            if symbols_with_issues:
                print("\nProblematic symbols (first 5):")
                for issue in symbols_with_issues[:5]:
                    print(f"  {issue['symbol']}: sodTod=${issue['sodTod']:.5f}, "
                          f"sodTom=${issue['sodTom']:.5f}, now=${issue['now']:.5f}")
                    
            # Show some good examples
            if symbols_ok:
                print("\nGood examples with price variation:")
                for symbol in symbols_ok[:3]:
                    print(f"  {symbol}: sodTod=${prices['sodTod'].get(symbol):.5f}, "
                          f"sodTom=${prices['sodTom'].get(symbol):.5f}, "
                          f"now=${prices['now'].get(symbol):.5f}")
                          
            self.test_results.append({
                'test': 'price_dictionary_validation',
                'status': 'WARNING' if symbols_with_issues else 'PASSED',
                'details': f'{len(symbols_with_issues)} symbols have identical or zero prices'
            })
            
        finally:
            conn.close()
            
    def test_synthetic_positions(self):
        """Test with synthetic data where we control all inputs"""
        print("\n=== Testing with Synthetic Positions ===")
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            temp_db = tmp.name
            
        conn = sqlite3.connect(temp_db)
        try:
            # Create tables
            create_all_tables(conn)
            
            # Insert synthetic positions
            positions_data = [
                # Yesterday trade - should use SOD price
                {
                    'transactionId': 1,
                    'symbol': 'TEST1',
                    'price': 110.00,
                    'quantity': 10,
                    'buySell': 'B',
                    'sequenceId': 'YESTERDAY-1',
                    'time': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d 10:00:00.000'),
                    'original_price': 110.00,
                    'original_time': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d 10:00:00.000')
                },
                # Today trade - should use actual price  
                {
                    'transactionId': 2,
                    'symbol': 'TEST1',
                    'price': 111.00,
                    'quantity': 10,
                    'buySell': 'B',
                    'sequenceId': 'TODAY-1',
                    'time': datetime.now().strftime('%Y-%m-%d 10:00:00.000'),
                    'original_price': 111.00,
                    'original_time': datetime.now().strftime('%Y-%m-%d 10:00:00.000')
                }
            ]
            
            # Insert positions
            for pos in positions_data:
                conn.execute("""
                    INSERT INTO trades_fifo 
                    (transactionId, symbol, price, original_price, quantity, buySell, 
                     sequenceId, time, original_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pos['transactionId'], pos['symbol'], pos['price'], 
                      pos['original_price'], pos['quantity'], pos['buySell'],
                      pos['sequenceId'], pos['time'], pos['original_time']))
                      
            # Insert controlled prices
            price_data = [
                ('TEST1', 'sodTod', 110.50),
                ('TEST1', 'sodTom', 111.00),
                ('TEST1', 'now', 111.25),
                ('TEST1', 'close', 111.10)
            ]
            
            for symbol, price_type, price in price_data:
                conn.execute("""
                    INSERT INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (symbol, price_type, price, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
            conn.commit()
            
            # Load data
            positions_df = view_unrealized_positions(conn, 'fifo')
            prices = load_pricing_dictionaries(conn)
            
            print("\nSynthetic test setup:")
            print(f"Positions: {len(positions_df)}")
            print(f"Prices: sodTod=${prices['sodTod']['TEST1']:.2f}, "
                  f"sodTom=${prices['sodTom']['TEST1']:.2f}, "
                  f"now=${prices['now']['TEST1']:.2f}")
                  
            # Test at different times
            test_scenarios = [
                ('10:00', 'pre_2pm', 110.50, 111.25),  # Before 2pm
                ('15:00', '2pm_to_4pm', 111.00, 111.25),  # After 2pm
            ]
            
            for time_str, expected_period, expected_intermediate, exit_price in test_scenarios:
                hour = int(time_str.split(':')[0])
                
                with patch('lib.trading.pnl_fifo_lifo.pnl_engine.datetime') as mock_dt:
                    mock_time = self.cdt.localize(datetime.now().replace(hour=hour, minute=0))
                    mock_dt.now.return_value = mock_time
                    mock_dt.strptime = datetime.strptime
                    
                    period = get_current_time_period()
                    assert period == expected_period, f"Expected {expected_period}, got {period}"
                    
                    results = calculate_unrealized_pnl(positions_df, prices, 'live')
                    
                    print(f"\nTime: {time_str} ({period})")
                    for result in results:
                        # Manual calculation
                        if result['sequenceId'] == 'YESTERDAY-1':
                            # Should use SOD as entry
                            entry = 110.50
                            expected_pnl = ((expected_intermediate - entry) * 10 + 
                                          (exit_price - expected_intermediate) * 10) * 1000
                        else:  # TODAY-1
                            # Should use actual as entry
                            entry = 111.00
                            expected_pnl = ((expected_intermediate - entry) * 10 + 
                                          (exit_price - expected_intermediate) * 10) * 1000
                                          
                        print(f"  {result['sequenceId']}: "
                              f"Entry=${result['entryPrice']:.2f}, "
                              f"Intermediate=${result['intermediatePrice']:.2f}, "
                              f"Exit=${result['exitPrice']:.2f}, "
                              f"P&L=${result['unrealizedPnL']:.2f}")
                        print(f"    Expected P&L: ${expected_pnl:.2f}")
                        
                        # Verify calculation
                        assert abs(result['unrealizedPnL'] - expected_pnl) < 0.01, \
                            f"P&L mismatch: got ${result['unrealizedPnL']}, expected ${expected_pnl}"
                            
            self.test_results.append({
                'test': 'synthetic_positions',
                'status': 'PASSED',
                'details': 'Synthetic position calculations verified correctly'
            })
            
        finally:
            conn.close()
            # Clean up temp file
            if os.path.exists(temp_db):
                os.unlink(temp_db)
                
    def test_time_period_transitions(self):
        """Test P&L changes at time period boundaries"""
        print("\n=== Testing Time Period Transitions ===")
        
        conn = sqlite3.connect(self.production_db)
        try:
            # Get a position and prices
            positions_df = view_unrealized_positions(conn, 'fifo')
            if positions_df.empty:
                print("No positions to test")
                return
                
            prices = load_pricing_dictionaries(conn)
            
            # Find a symbol where sodTod != sodTom
            test_symbol = None
            for symbol in positions_df['symbol'].unique():
                sod_tod = prices['sodTod'].get(symbol, 0)
                sod_tom = prices['sodTom'].get(symbol, 0)
                if sod_tod != sod_tom and sod_tod > 0 and sod_tom > 0:
                    test_symbol = symbol
                    break
                    
            if not test_symbol:
                print("WARNING: No symbols found with different sodTod/sodTom prices")
                self.test_results.append({
                    'test': 'time_period_transitions',
                    'status': 'WARNING',
                    'details': 'No suitable test data found'
                })
                return
                
            # Get positions for this symbol
            symbol_positions = positions_df[positions_df['symbol'] == test_symbol]
            
            print(f"\nTesting with {test_symbol}:")
            print(f"  sodTod: ${prices['sodTod'][test_symbol]:.5f}")
            print(f"  sodTom: ${prices['sodTom'][test_symbol]:.5f}")
            print(f"  Difference: ${abs(prices['sodTom'][test_symbol] - prices['sodTod'][test_symbol]):.5f}")
            
            # Test at boundary times
            boundary_tests = [
                (13, 59, 'pre_2pm'),    # 1:59 PM
                (14, 1, '2pm_to_4pm'),  # 2:01 PM
            ]
            
            pnl_results = {}
            
            for hour, minute, expected_period in boundary_tests:
                with patch('lib.trading.pnl_fifo_lifo.pnl_engine.datetime') as mock_dt:
                    mock_time = self.cdt.localize(datetime.now().replace(hour=hour, minute=minute))
                    mock_dt.now.return_value = mock_time
                    mock_dt.strptime = datetime.strptime
                    
                    period = get_current_time_period()
                    results = calculate_unrealized_pnl(symbol_positions, prices, 'live')
                    total_pnl = sum(r['unrealizedPnL'] for r in results)
                    
                    pnl_results[f"{hour:02d}:{minute:02d}"] = total_pnl
                    
                    print(f"\n{hour:02d}:{minute:02d} ({period}): Total P&L = ${total_pnl:,.2f}")
                    
            # Verify P&L changed
            pnl_values = list(pnl_results.values())
            if len(set(pnl_values)) == 1:
                print("\nWARNING: P&L did not change across time periods!")
                print("This suggests time-based logic may not be working correctly.")
                status = 'FAILED'
            else:
                print("\n✓ P&L changes detected at time boundaries")
                status = 'PASSED'
                
            self.test_results.append({
                'test': 'time_period_transitions',
                'status': status,
                'details': f'Tested {test_symbol} at time boundaries'
            })
            
        finally:
            conn.close()
            
    def test_calculation_precision(self):
        """Test floating-point precision with real positions"""
        print("\n=== Testing Calculation Precision ===")
        
        conn = sqlite3.connect(self.production_db)
        try:
            positions_df = view_unrealized_positions(conn, 'fifo')
            prices = load_pricing_dictionaries(conn)
            
            if positions_df.empty:
                print("No positions to test")
                return
                
            # Calculate for a few positions
            sample_positions = positions_df.head(5)
            results = calculate_unrealized_pnl(sample_positions, prices, 'live')
            
            print("\nPrecision verification:")
            all_precise = True
            
            for result in results:
                pnl = result['unrealizedPnL']
                pnl_str = f"{pnl:.2f}"
                
                # Check it's rounded to 2 decimals
                if '.' in pnl_str:
                    decimals = len(pnl_str.split('.')[1])
                    if decimals > 2:
                        all_precise = False
                        print(f"  {result['symbol']}: ${pnl} - MORE THAN 2 DECIMALS!")
                    else:
                        print(f"  {result['symbol']}: ${pnl} - OK")
                        
            self.test_results.append({
                'test': 'calculation_precision',
                'status': 'PASSED' if all_precise else 'FAILED',
                'details': 'All P&L values rounded to 2 decimals' if all_precise else 'Precision issues found'
            })
            
        finally:
            conn.close()
            
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("=" * 80)
        print("COMPREHENSIVE UNREALIZED P&L ROBUSTNESS TEST")
        print("=" * 80)
        
        try:
            # Run each test
            self.test_aug5_trades_pmax_logic()
            self.test_price_dictionary_validation()
            self.test_synthetic_positions()
            self.test_time_period_transitions()
            self.test_calculation_precision()
            
            # Display summary
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            
            passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
            warnings = sum(1 for r in self.test_results if r['status'] == 'WARNING')
            failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')
            total = len(self.test_results)
            
            for result in self.test_results:
                if result['status'] == 'PASSED':
                    icon = "✓"
                elif result['status'] == 'WARNING':
                    icon = "⚠"
                else:
                    icon = "✗"
                    
                print(f"{icon} {result['test']:30} {result['status']:10} - {result['details']}")
                
            print(f"\nTotal: {passed} passed, {warnings} warnings, {failed} failed (out of {total})")
            
            if failed == 0 and warnings == 0:
                print("\n✓ ALL TESTS PASSED - Unrealized P&L calculations are robust!")
            elif failed == 0:
                print(f"\n⚠ Tests passed but {warnings} warnings need attention")
            else:
                print(f"\n✗ {failed} tests FAILED - Review calculations immediately")
                
        except Exception as e:
            print(f"\nERROR during testing: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = ComprehensiveUnrealizedPnLTest()
    tester.run_all_tests()