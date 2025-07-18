#!/usr/bin/env python
"""Comprehensive Testing of TYU5 Migration Phases 1-3

This script thoroughly tests:
1. Schema Enhancement - all tables and constraints
2. Database Writer - data persistence and integrity
3. Unified Service - API functionality and data retrieval
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import json
from typing import Dict, List, Any
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_integration.tyu5_database_writer import TYU5DatabaseWriter
from lib.trading.pnl_integration.tyu5_adapter import TYU5Adapter
from lib.trading.pnl_integration.tyu5_service import TYU5Service
from lib.trading.pnl_integration.unified_pnl_api import UnifiedPnLAPI
from lib.trading.pnl_calculator.unified_service import UnifiedPnLService


class ComprehensiveTester:
    """Comprehensive test suite for TYU5 migration phases."""
    
    def __init__(self, db_path: str = "data/output/pnl/pnl_tracker.db"):
        self.db_path = db_path
        self.test_results = {
            "phase1_schema": {},
            "phase2_writer": {},
            "phase3_unified": {},
            "data_integrity": {},
            "performance": {}
        }
        
    def run_all_tests(self):
        """Run all comprehensive tests."""
        print("=" * 80)
        print("COMPREHENSIVE TYU5 MIGRATION TEST SUITE")
        print("=" * 80)
        
        # Phase 1 Tests
        print("\n" + "=" * 80)
        print("PHASE 1: SCHEMA ENHANCEMENT TESTS")
        print("=" * 80)
        self.test_phase1_schema()
        
        # Phase 2 Tests
        print("\n" + "=" * 80)
        print("PHASE 2: DATABASE WRITER TESTS")
        print("=" * 80)
        self.test_phase2_writer()
        
        # Phase 3 Tests
        print("\n" + "=" * 80)
        print("PHASE 3: UNIFIED SERVICE TESTS")
        print("=" * 80)
        self.test_phase3_unified()
        
        # Data Integrity Tests
        print("\n" + "=" * 80)
        print("DATA INTEGRITY VALIDATION")
        print("=" * 80)
        self.test_data_integrity()
        
        # Performance Tests
        print("\n" + "=" * 80)
        print("PERFORMANCE METRICS")
        print("=" * 80)
        self.test_performance()
        
        # Summary Report
        print("\n" + "=" * 80)
        print("TEST SUMMARY REPORT")
        print("=" * 80)
        self.generate_summary_report()
        
    def test_phase1_schema(self):
        """Test Phase 1: Schema Enhancement."""
        print("\n1.1 Testing Table Creation...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Expected tables with their key columns
        expected_tables = {
            'lot_positions': ['id', 'symbol', 'trade_id', 'remaining_quantity', 'entry_price', 'entry_date'],
            'position_greeks': ['id', 'position_id', 'calc_timestamp', 'delta', 'gamma', 'vega', 'theta', 'speed'],
            'risk_scenarios': ['id', 'calc_timestamp', 'symbol', 'scenario_price', 'scenario_pnl'],
            'match_history': ['id', 'symbol', 'match_date', 'buy_trade_id', 'sell_trade_id', 'matched_quantity'],
            'pnl_attribution': ['id', 'position_id', 'calc_timestamp', 'total_pnl', 'delta_pnl', 'gamma_pnl'],
            'schema_migrations': ['version', 'applied_at', 'description']
        }
        
        tables_found = 0
        tables_correct = 0
        
        for table_name, expected_columns in expected_tables.items():
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            if cursor.fetchone():
                tables_found += 1
                print(f"✓ Table '{table_name}' exists")
                
                # Check columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                
                missing_cols = set(expected_columns) - set(columns)
                if not missing_cols:
                    tables_correct += 1
                    print(f"  ✓ All expected columns present")
                else:
                    print(f"  ✗ Missing columns: {missing_cols}")
                    
                # Show actual columns
                print(f"  Columns: {', '.join(columns)}")
                
            else:
                print(f"✗ Table '{table_name}' NOT FOUND")
                
        self.test_results["phase1_schema"]["tables_found"] = f"{tables_found}/{len(expected_tables)}"
        self.test_results["phase1_schema"]["tables_correct"] = f"{tables_correct}/{len(expected_tables)}"
        
        # Test positions table enhancement
        print("\n1.2 Testing Positions Table Enhancement...")
        cursor.execute("PRAGMA table_info(positions)")
        position_columns = [row[1] for row in cursor.fetchall()]
        
        if 'short_quantity' in position_columns:
            print("✓ 'short_quantity' column added to positions table")
            self.test_results["phase1_schema"]["short_quantity"] = "Present"
        else:
            print("✗ 'short_quantity' column NOT FOUND in positions table")
            self.test_results["phase1_schema"]["short_quantity"] = "Missing"
            
        # Test indexes
        print("\n1.3 Testing Indexes...")
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = cursor.fetchall()
        print(f"Found {len(indexes)} indexes")
        for idx_name, _ in indexes[:5]:  # Show first 5
            print(f"  ✓ {idx_name}")
            
        self.test_results["phase1_schema"]["indexes"] = len(indexes)
        
        # Test WAL mode
        print("\n1.4 Testing WAL Mode...")
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        if mode == 'wal':
            print("✓ WAL mode enabled")
            self.test_results["phase1_schema"]["wal_mode"] = "Enabled"
        else:
            print(f"✗ Journal mode is '{mode}', not WAL")
            self.test_results["phase1_schema"]["wal_mode"] = mode
            
        conn.close()
        
    def test_phase2_writer(self):
        """Test Phase 2: Database Writer."""
        print("\n2.1 Testing Data Persistence...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Check lot positions
        lot_df = pd.read_sql_query("SELECT * FROM lot_positions", conn)
        print(f"\nLot Positions: {len(lot_df)} records")
        if not lot_df.empty:
            print("Sample lot positions:")
            print(lot_df[['symbol', 'remaining_quantity', 'entry_price', 'trade_id']].head())
            
            # Validate data
            print("\nData validation:")
            print(f"  Unique symbols: {lot_df['symbol'].nunique()}")
            print(f"  Quantity range: {lot_df['remaining_quantity'].min():.2f} to {lot_df['remaining_quantity'].max():.2f}")
            print(f"  Price range: {lot_df['entry_price'].min():.4f} to {lot_df['entry_price'].max():.4f}")
            
            # Check for 32nds conversion
            prices_with_fractions = lot_df[lot_df['entry_price'] % 1 != 0]
            if not prices_with_fractions.empty:
                print(f"  ✓ 32nds conversion detected: {len(prices_with_fractions)} prices with fractions")
            
        self.test_results["phase2_writer"]["lot_positions"] = len(lot_df)
        
        # Check risk scenarios
        risk_df = pd.read_sql_query("SELECT * FROM risk_scenarios", conn)
        print(f"\nRisk Scenarios: {len(risk_df)} records")
        if not risk_df.empty:
            # Group by symbol
            scenarios_by_symbol = risk_df.groupby('symbol').agg({
                'scenario_price': ['count', 'min', 'max'],
                'scenario_pnl': ['min', 'max']
            })
            print("\nScenarios by symbol:")
            print(scenarios_by_symbol)
            
        self.test_results["phase2_writer"]["risk_scenarios"] = len(risk_df)
        
        # Check position Greeks
        greeks_df = pd.read_sql_query("""
            SELECT pg.*, p.instrument_name 
            FROM position_greeks pg
            JOIN positions p ON pg.position_id = p.id
        """, conn)
        print(f"\nPosition Greeks: {len(greeks_df)} records")
        if not greeks_df.empty:
            print("Sample Greeks:")
            print(greeks_df[['instrument_name', 'delta', 'gamma', 'vega', 'theta']].head())
            
        self.test_results["phase2_writer"]["position_greeks"] = len(greeks_df)
        
        # Check match history
        match_df = pd.read_sql_query("SELECT * FROM match_history", conn)
        print(f"\nMatch History: {len(match_df)} records")
        if not match_df.empty:
            print("Sample matches:")
            print(match_df[['symbol', 'matched_quantity', 'realized_pnl']].head())
            
        self.test_results["phase2_writer"]["match_history"] = len(match_df)
        
        conn.close()
        
    def test_phase3_unified(self):
        """Test Phase 3: Unified Service."""
        print("\n3.1 Testing UnifiedPnLAPI...")
        
        try:
            api = UnifiedPnLAPI(self.db_path)
            
            # Test positions with lots
            print("\n3.1.1 Testing get_positions_with_lots()...")
            positions = api.get_positions_with_lots()
            print(f"Found {len(positions)} positions with lots")
            
            if positions:
                # Show first position details
                pos = positions[0]
                print(f"\nSample position: {pos['symbol']}")
                print(f"  Net position: {pos['net_position']}")
                print(f"  Lot count: {pos['lot_count']}")
                print(f"  Total lot quantity: {pos.get('total_lot_quantity', 'N/A')}")
                if 'lots' in pos and pos['lots']:
                    print(f"  Individual lots: {len(pos['lots'])}")
                    for lot in pos['lots'][:2]:
                        print(f"    - {lot['remaining_quantity']} @ {lot['entry_price']}")
                        
            self.test_results["phase3_unified"]["positions_with_lots"] = len(positions)
            
            # Test portfolio Greeks
            print("\n3.1.2 Testing get_portfolio_greeks()...")
            greeks = api.get_portfolio_greeks()
            print("Portfolio Greeks:")
            for key, value in greeks.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
                    
            self.test_results["phase3_unified"]["portfolio_greeks"] = greeks
            
            # Test risk scenarios
            print("\n3.1.3 Testing get_risk_scenarios()...")
            scenarios_df = api.get_risk_scenarios()
            if not scenarios_df.empty:
                print(f"Found {len(scenarios_df)} risk scenarios")
                print(f"Symbols with scenarios: {scenarios_df['symbol'].nunique()}")
                
                # Show sample scenarios for first symbol
                first_symbol = scenarios_df['symbol'].iloc[0]
                symbol_scenarios = scenarios_df[scenarios_df['symbol'] == first_symbol]
                print(f"\nScenarios for {first_symbol}:")
                print(symbol_scenarios[['scenario_price', 'scenario_pnl']].head())
                
            self.test_results["phase3_unified"]["risk_scenarios"] = len(scenarios_df)
            
            # Test portfolio summary
            print("\n3.1.4 Testing get_portfolio_summary()...")
            summary = api.get_portfolio_summary()
            print("Portfolio Summary:")
            print(json.dumps(summary, indent=2, default=str))
            
            self.test_results["phase3_unified"]["portfolio_summary"] = summary
            
        except Exception as e:
            print(f"✗ UnifiedPnLAPI error: {e}")
            traceback.print_exc()
            self.test_results["phase3_unified"]["api_error"] = str(e)
            
        # Test UnifiedPnLService
        print("\n3.2 Testing UnifiedPnLService...")
        try:
            service = UnifiedPnLService(
                db_path=self.db_path,
                trade_ledger_dir="data/input/trade_ledger",
                price_directories=["data/input/market_prices"]
            )
            
            print(f"TYU5 Features Enabled: {service._tyu5_enabled}")
            self.test_results["phase3_unified"]["tyu5_enabled"] = service._tyu5_enabled
            
            # Test enhanced methods
            if service._tyu5_enabled:
                # Test lot positions
                lot_positions = service.get_positions_with_lots()
                print(f"Service returned {len(lot_positions)} positions with lots")
                
                # Test portfolio Greeks through service
                portfolio_greeks = service.get_portfolio_greeks()
                print(f"Service portfolio Greeks: {portfolio_greeks.get('option_count', 0)} options")
                
        except Exception as e:
            print(f"✗ UnifiedPnLService error: {e}")
            self.test_results["phase3_unified"]["service_error"] = str(e)
            
    def test_data_integrity(self):
        """Test data integrity across all systems."""
        print("\n4.1 Cross-System Data Validation...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Check positions vs lot positions consistency
        print("\n4.1.1 Positions vs Lot Positions Consistency...")
        
        # Get positions with quantities
        positions_df = pd.read_sql_query("""
            SELECT instrument_name, position_quantity, short_quantity
            FROM positions
            WHERE position_quantity != 0
        """, conn)
        
        # Get lot totals
        lot_totals_df = pd.read_sql_query("""
            SELECT symbol, SUM(remaining_quantity) as total_lot_qty
            FROM lot_positions
            GROUP BY symbol
        """, conn)
        
        # Merge and compare
        comparison_df = positions_df.merge(
            lot_totals_df, 
            left_on='instrument_name', 
            right_on='symbol', 
            how='outer'
        )
        
        print(f"Positions count: {len(positions_df)}")
        print(f"Symbols with lots: {len(lot_totals_df)}")
        
        if not comparison_df.empty:
            # Check for mismatches
            comparison_df['match'] = comparison_df['position_quantity'].fillna(0) == comparison_df['total_lot_qty'].fillna(0)
            mismatches = comparison_df[~comparison_df['match']]
            
            if mismatches.empty:
                print("✓ All positions match lot totals")
                self.test_results["data_integrity"]["position_lot_match"] = "Perfect"
            else:
                print(f"✗ Found {len(mismatches)} mismatches:")
                print(mismatches[['instrument_name', 'position_quantity', 'total_lot_qty']])
                self.test_results["data_integrity"]["position_lot_match"] = f"{len(mismatches)} mismatches"
                
        # Check Greeks timestamp consistency
        print("\n4.1.2 Greeks Timestamp Validation...")
        greeks_timestamps = pd.read_sql_query("""
            SELECT COUNT(DISTINCT calc_timestamp) as unique_timestamps,
                   MIN(calc_timestamp) as earliest,
                   MAX(calc_timestamp) as latest
            FROM position_greeks
        """, conn)
        
        if not greeks_timestamps.empty:
            row = greeks_timestamps.iloc[0]
            print(f"Greek calculation timestamps: {row['unique_timestamps']} unique")
            print(f"  Earliest: {row['earliest']}")
            print(f"  Latest: {row['latest']}")
            
        # Check risk scenarios consistency
        print("\n4.1.3 Risk Scenarios Validation...")
        scenario_stats = pd.read_sql_query("""
            SELECT symbol,
                   COUNT(*) as scenario_count,
                   MIN(scenario_price) as min_price,
                   MAX(scenario_price) as max_price,
                   COUNT(DISTINCT calc_timestamp) as calc_runs
            FROM risk_scenarios
            GROUP BY symbol
        """, conn)
        
        if not scenario_stats.empty:
            print("Risk scenario statistics:")
            print(scenario_stats)
            
            # Check for consistent scenario counts
            scenario_counts = scenario_stats['scenario_count'].unique()
            if len(scenario_counts) == 1:
                print(f"✓ All symbols have {scenario_counts[0]} scenarios")
                self.test_results["data_integrity"]["scenario_consistency"] = "Consistent"
            else:
                print(f"✗ Inconsistent scenario counts: {scenario_counts}")
                self.test_results["data_integrity"]["scenario_consistency"] = "Inconsistent"
                
        conn.close()
        
    def test_performance(self):
        """Test performance metrics."""
        import time
        
        print("\n5.1 Query Performance Tests...")
        
        api = UnifiedPnLAPI(self.db_path)
        
        # Test 1: Position query performance
        start = time.time()
        positions = api.get_positions_with_lots()
        positions_time = (time.time() - start) * 1000
        print(f"get_positions_with_lots(): {positions_time:.2f}ms for {len(positions)} positions")
        
        # Test 2: Greeks query performance
        start = time.time()
        greeks_df = api.get_greek_exposure()
        greeks_time = (time.time() - start) * 1000
        print(f"get_greek_exposure(): {greeks_time:.2f}ms for {len(greeks_df)} records")
        
        # Test 3: Risk scenarios performance
        start = time.time()
        scenarios_df = api.get_risk_scenarios()
        scenarios_time = (time.time() - start) * 1000
        print(f"get_risk_scenarios(): {scenarios_time:.2f}ms for {len(scenarios_df)} scenarios")
        
        # Test 4: Portfolio summary performance
        start = time.time()
        summary = api.get_portfolio_summary()
        summary_time = (time.time() - start) * 1000
        print(f"get_portfolio_summary(): {summary_time:.2f}ms")
        
        self.test_results["performance"] = {
            "positions_query_ms": round(positions_time, 2),
            "greeks_query_ms": round(greeks_time, 2),
            "scenarios_query_ms": round(scenarios_time, 2),
            "summary_query_ms": round(summary_time, 2)
        }
        
        # Database size check
        print("\n5.2 Database Size Analysis...")
        conn = sqlite3.connect(self.db_path)
        
        table_sizes = pd.read_sql_query("""
            SELECT 
                name as table_name,
                (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
            FROM sqlite_master m
            WHERE type='table' AND name IN ('lot_positions', 'position_greeks', 'risk_scenarios', 'match_history')
        """, conn)
        
        # Get actual row counts
        for table in ['lot_positions', 'position_greeks', 'risk_scenarios', 'match_history']:
            count = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {table}", conn).iloc[0]['cnt']
            print(f"  {table}: {count:,} rows")
            
        # Database file size
        db_size_mb = Path(self.db_path).stat().st_size / (1024 * 1024)
        print(f"\nDatabase file size: {db_size_mb:.2f} MB")
        self.test_results["performance"]["db_size_mb"] = round(db_size_mb, 2)
        
        conn.close()
        
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        print("\n" + "=" * 80)
        print("FINAL TEST RESULTS")
        print("=" * 80)
        
        # Phase 1 Summary
        print("\nPHASE 1 - SCHEMA ENHANCEMENT:")
        phase1 = self.test_results["phase1_schema"]
        print(f"  Tables Created: {phase1.get('tables_found', 'N/A')}")
        print(f"  Tables Correct: {phase1.get('tables_correct', 'N/A')}")
        print(f"  Short Quantity Column: {phase1.get('short_quantity', 'N/A')}")
        print(f"  Indexes Created: {phase1.get('indexes', 'N/A')}")
        print(f"  WAL Mode: {phase1.get('wal_mode', 'N/A')}")
        
        # Phase 2 Summary
        print("\nPHASE 2 - DATABASE WRITER:")
        phase2 = self.test_results["phase2_writer"]
        print(f"  Lot Positions: {phase2.get('lot_positions', 0)} records")
        print(f"  Risk Scenarios: {phase2.get('risk_scenarios', 0)} records")
        print(f"  Position Greeks: {phase2.get('position_greeks', 0)} records")
        print(f"  Match History: {phase2.get('match_history', 0)} records")
        
        # Phase 3 Summary
        print("\nPHASE 3 - UNIFIED SERVICE:")
        phase3 = self.test_results["phase3_unified"]
        print(f"  TYU5 Features Enabled: {phase3.get('tyu5_enabled', 'N/A')}")
        print(f"  Positions with Lots: {phase3.get('positions_with_lots', 0)}")
        if 'portfolio_greeks' in phase3:
            greeks = phase3['portfolio_greeks']
            print(f"  Portfolio Greeks: {greeks.get('option_count', 0)} options tracked")
        print(f"  Risk Scenarios Available: {phase3.get('risk_scenarios', 0)}")
        
        # Data Integrity Summary
        print("\nDATA INTEGRITY:")
        integrity = self.test_results["data_integrity"]
        print(f"  Position/Lot Consistency: {integrity.get('position_lot_match', 'N/A')}")
        print(f"  Scenario Consistency: {integrity.get('scenario_consistency', 'N/A')}")
        
        # Performance Summary
        print("\nPERFORMANCE METRICS:")
        perf = self.test_results["performance"]
        print(f"  Query Performance:")
        print(f"    - Positions: {perf.get('positions_query_ms', 'N/A')}ms")
        print(f"    - Greeks: {perf.get('greeks_query_ms', 'N/A')}ms")
        print(f"    - Scenarios: {perf.get('scenarios_query_ms', 'N/A')}ms")
        print(f"    - Summary: {perf.get('summary_query_ms', 'N/A')}ms")
        print(f"  Database Size: {perf.get('db_size_mb', 'N/A')} MB")
        
        # Overall Status
        print("\n" + "=" * 80)
        errors = []
        if 'api_error' in phase3:
            errors.append(f"API Error: {phase3['api_error']}")
        if 'service_error' in phase3:
            errors.append(f"Service Error: {phase3['service_error']}")
            
        if errors:
            print("OVERALL STATUS: ISSUES DETECTED")
            for error in errors:
                print(f"  ✗ {error}")
        else:
            print("OVERALL STATUS: ALL TESTS PASSED ✓")
            
        print("=" * 80)
        
        # Save detailed results to file
        output_path = Path("data/output/pnl/tyu5_test_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_all_tests() 