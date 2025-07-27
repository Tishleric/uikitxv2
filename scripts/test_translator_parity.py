#!/usr/bin/env python3
"""
Test translator parity between RosettaStone and legacy translators.

This script verifies that RosettaStone produces identical outputs to existing translators
for all symbol formats and edge cases.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all translators
from lib.trading.market_prices.rosetta_stone import RosettaStone
from lib.trading.symbol_translator import SymbolTranslator
from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator


class TranslatorParityTester:
    """Test parity between different translator implementations."""
    
    def __init__(self):
        self.rosetta = RosettaStone()
        self.symbol_translator = SymbolTranslator()
        self.spot_risk_translator = SpotRiskSymbolTranslator()
        self.results = []
        
    def test_symbol_translator_parity(self):
        """Test SymbolTranslator vs RosettaStone for ActantTrades format."""
        print("\n" + "="*60)
        print("TESTING: SymbolTranslator vs RosettaStone")
        print("="*60)
        
        # Test cases from actual trade files
        test_cases = [
            # Format: (actant_symbol, expected_bloomberg)
            ("XCMEOCADPS20250721N0VY3/111", "VBYN25C3 111.000 Comdty"),
            ("XCMEOCADPS20250728N0VY4/111.75", "VBYN25C4 111.750 Comdty"),
            ("XCMEOCADPS20250729N0GY5/110.5", "TJPN25C5 110.500 Comdty"),
            ("XCMEOCADPS20250730N0WY5/111.25", "TYWN25C5 111.250 Comdty"),
            ("XCMEOCADPS20250731N0HY5/112", "TJWN25C5 112.000 Comdty"),
            ("XCMEOCADPS20250801Q0ZN1/111", "1MQ5C 111.000 Comdty"),
            ("XCMEOCADPS20250808Q0ZN2/112", "2MQ5C 112.000 Comdty"),
            ("XCMEOCADPS20250815Q0ZN3/110.75", "3MQ5C 110.750 Comdty"),
            ("XCMEOCADPS20250822U0OZN/97", None),  # Quarterly, should fail on SymbolTranslator
        ]
        
        for actant_symbol, expected in test_cases:
            print(f"\nTesting: {actant_symbol}")
            
            # Test SymbolTranslator
            try:
                st_result = self.symbol_translator.translate(actant_symbol)
                print(f"  SymbolTranslator: {st_result}")
            except Exception as e:
                st_result = f"ERROR: {str(e)}"
                print(f"  SymbolTranslator: {st_result}")
            
            # Test RosettaStone
            try:
                rs_result = self.rosetta.translate(actant_symbol, 'actanttrades', 'bloomberg')
                print(f"  RosettaStone:     {rs_result}")
            except Exception as e:
                rs_result = f"ERROR: {str(e)}"
                print(f"  RosettaStone:     {rs_result}")
            
            # Compare results
            if expected:
                print(f"  Expected:         {expected}")
            
            match = st_result == rs_result
            print(f"  Match: {'✓' if match else '✗'}")
            
            self.results.append({
                'test': 'SymbolTranslator',
                'input': actant_symbol,
                'st_output': st_result,
                'rs_output': rs_result,
                'match': match
            })
    
    def test_spot_risk_translator_parity(self):
        """Test SpotRiskSymbolTranslator vs RosettaStone for spot risk format."""
        print("\n" + "="*60)
        print("TESTING: SpotRiskSymbolTranslator vs RosettaStone")
        print("="*60)
        
        # Test cases from actual spot risk files
        test_cases = [
            # Options
            ("XCME.VY3.21JUL25.111.C", "VBYN25C3 111.000 Comdty"),
            ("XCME.VY3.21JUL25.111:75.P", "VBYN25P3 111.750 Comdty"),
            ("XCME.GY4.22JUL25.110:5.C", "TJPN25C4 110.500 Comdty"),
            ("XCME.WY4.23JUL25.111:25.C", "TYWN25C4 111.250 Comdty"),
            ("XCME.HY4.24JUL25.112.P", "TJWN25P4 112.000 Comdty"),
            ("XCME.ZN1.01AUG25.111.C", "1MQ5C 111.000 Comdty"),
            ("XCME.OZN.AUG25.111.C", "TYQ5C 111.000 Comdty"),
            # Futures
            ("XCME.ZN.SEP25", "TYU5 Comdty"),
            ("XCME.ZN.DEC25", "TYZ5 Comdty"),
        ]
        
        for spot_risk_symbol, expected in test_cases:
            print(f"\nTesting: {spot_risk_symbol}")
            
            # Test SpotRiskSymbolTranslator
            try:
                srt_result = self.spot_risk_translator.to_bloomberg(spot_risk_symbol)
                print(f"  SpotRiskTranslator: {srt_result}")
            except Exception as e:
                srt_result = f"ERROR: {str(e)}"
                print(f"  SpotRiskTranslator: {srt_result}")
            
            # Test RosettaStone
            try:
                rs_result = self.rosetta.translate(spot_risk_symbol, 'actantrisk', 'bloomberg')
                print(f"  RosettaStone:       {rs_result}")
            except Exception as e:
                rs_result = f"ERROR: {str(e)}"
                print(f"  RosettaStone:       {rs_result}")
            
            # Compare results
            print(f"  Expected:           {expected}")
            
            match = srt_result == rs_result
            print(f"  Match: {'✓' if match else '✗'}")
            
            self.results.append({
                'test': 'SpotRiskTranslator',
                'input': spot_risk_symbol,
                'srt_output': srt_result,
                'rs_output': rs_result,
                'match': match
            })
    
    def test_bidirectional_translations(self):
        """Test bidirectional translations to ensure reversibility."""
        print("\n" + "="*60)
        print("TESTING: Bidirectional Translation (Bloomberg ↔ CME ↔ ActantRisk)")
        print("="*60)
        
        test_cases = [
            ("VBYN25C3 111.000 Comdty", "VY3N5 C11100", "XCME.VY3.21JUL25.111.C"),
            ("1MQ5C 111.500 Comdty", "ZN1Q5 C11150", "XCME.ZN1.01AUG25.111:5.C"),
            ("TYQ5C 111.250 Comdty", "OZNQ5 C11125", "XCME.OZN.AUG25.111:25.C"),
        ]
        
        for bloomberg, cme, actant_risk in test_cases:
            print(f"\nTesting: {bloomberg}")
            
            # Bloomberg → CME
            cme_result = self.rosetta.translate(bloomberg, 'bloomberg', 'cme')
            print(f"  Bloomberg → CME: {cme_result} (expected: {cme})")
            
            # CME → ActantRisk
            actant_result = self.rosetta.translate(cme, 'cme', 'actantrisk')
            print(f"  CME → ActantRisk: {actant_result} (expected: {actant_risk})")
            
            # ActantRisk → Bloomberg (full circle)
            bloomberg_result = self.rosetta.translate(actant_risk, 'actantrisk', 'bloomberg')
            print(f"  ActantRisk → Bloomberg: {bloomberg_result} (expected: {bloomberg})")
            
            full_circle = bloomberg_result == bloomberg
            print(f"  Full circle: {'✓' if full_circle else '✗'}")
    
    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        print("\n" + "="*60)
        print("TESTING: Edge Cases")
        print("="*60)
        
        # Month boundaries
        print("\nMonth boundary cases:")
        month_boundary_cases = [
            ("XCMEOCADPS20250131Q0ZN5/111", "Friday option at month end"),
            ("XCMEOCADPS20250228Q0ZN4/110.5", "Friday option in February"),
            ("XCMEOCADPS20251229N0VY5/112", "Year-end Monday option"),
        ]
        
        for symbol, description in month_boundary_cases:
            print(f"\n  {description}: {symbol}")
            try:
                result = self.rosetta.translate(symbol, 'actanttrades', 'bloomberg')
                print(f"    Result: {result}")
            except Exception as e:
                print(f"    Error: {str(e)}")
    
    def generate_report(self):
        """Generate summary report of test results."""
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        
        # Count matches by test type
        test_types = {}
        for result in self.results:
            test_type = result['test']
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'matches': 0}
            test_types[test_type]['total'] += 1
            if result.get('match', False):
                test_types[test_type]['matches'] += 1
        
        # Print summary
        for test_type, stats in test_types.items():
            match_rate = (stats['matches'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"\n{test_type}:")
            print(f"  Total tests: {stats['total']}")
            print(f"  Matches: {stats['matches']}")
            print(f"  Match rate: {match_rate:.1f}%")
        
        # List all mismatches
        mismatches = [r for r in self.results if not r.get('match', False)]
        if mismatches:
            print("\n" + "-"*60)
            print("MISMATCHES FOUND:")
            for mm in mismatches:
                print(f"\n  Input: {mm['input']}")
                if 'st_output' in mm:
                    print(f"    SymbolTranslator: {mm['st_output']}")
                if 'srt_output' in mm:
                    print(f"    SpotRiskTranslator: {mm['srt_output']}")
                print(f"    RosettaStone: {mm['rs_output']}")
    
    def run_all_tests(self):
        """Run all parity tests."""
        try:
            self.test_symbol_translator_parity()
        except Exception as e:
            print(f"\nERROR in SymbolTranslator tests: {e}")
            traceback.print_exc()
        
        try:
            self.test_spot_risk_translator_parity()
        except Exception as e:
            print(f"\nERROR in SpotRiskTranslator tests: {e}")
            traceback.print_exc()
        
        try:
            self.test_bidirectional_translations()
        except Exception as e:
            print(f"\nERROR in bidirectional tests: {e}")
            traceback.print_exc()
        
        try:
            self.test_edge_cases()
        except Exception as e:
            print(f"\nERROR in edge case tests: {e}")
            traceback.print_exc()
        
        self.generate_report()


if __name__ == "__main__":
    import io
    import contextlib
    
    # Capture output to both console and file
    output = io.StringIO()
    
    with contextlib.redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding='utf-8', write_through=True)) as buffer:
        tester = TranslatorParityTester()
        
        # Also print to console
        import sys
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
                    f.flush()
            def flush(self):
                for f in self.files:
                    f.flush()
        
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, output)
        
        try:
            tester.run_all_tests()
        finally:
            sys.stdout = original_stdout
        
        # Save output to file
        with open('translator_parity_report.txt', 'w') as f:
            f.write(output.getvalue())
        print("\nReport saved to translator_parity_report.txt") 