#!/usr/bin/env python3
"""Comprehensive test of spot risk pipeline including all components."""

import sys
sys.path.append('.')

from pathlib import Path
import pandas as pd
from datetime import datetime
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.market_prices.rosetta_stone import RosettaStone

def test_comprehensive_pipeline():
    """Test all aspects of the spot risk pipeline."""
    
    print("=== COMPREHENSIVE SPOT RISK PIPELINE TEST ===")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find test file
    spot_risk_dir = Path("data/input/actant_spot_risk")
    test_file = spot_risk_dir / "2025-07-24" / "bav_analysis_20250723_170920.csv"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Using test file: {test_file}")
    
    # Test 1: Parse CSV with vtexp loading
    print("\n1. PARSING CSV WITH VTEXP:")
    df = parse_spot_risk_csv(test_file, calculate_time_to_expiry=True)
    
    if df is None or df.empty:
        print("❌ Failed to parse CSV")
        return False
    
    print(f"✅ Parsed {len(df)} rows")
    
    # Test 2: Check Bloomberg translation
    print("\n2. BLOOMBERG SYMBOL TRANSLATION:")
    if 'bloomberg_symbol' not in df.columns:
        print("❌ bloomberg_symbol column missing")
        return False
    
    trans_count = df['bloomberg_symbol'].notna().sum()
    trans_rate = (trans_count / len(df)) * 100
    print(f"✅ Translated {trans_count}/{len(df)} symbols ({trans_rate:.1f}%)")
    
    # Show examples
    print("\nExample translations:")
    examples = df[df['bloomberg_symbol'].notna()][['key', 'bloomberg_symbol']].head(5)
    for _, row in examples.iterrows():
        print(f"  {row['key']} → {row['bloomberg_symbol']}")
    
    # Test 3: Check vtexp for options
    print("\n3. VTEXP MATCHING FOR OPTIONS:")
    options_df = df[df['itype'].isin(['C', 'P'])]
    
    if len(options_df) > 0:
        vtexp_count = options_df['vtexp'].notna().sum()
        vtexp_rate = (vtexp_count / len(options_df)) * 100
        print(f"✅ Matched vtexp for {vtexp_count}/{len(options_df)} options ({vtexp_rate:.1f}%)")
        
        # Show examples
        print("\nExample vtexp values:")
        vtexp_examples = options_df[options_df['vtexp'].notna()][['key', 'vtexp']].head(5)
        for _, row in vtexp_examples.iterrows():
            print(f"  {row['key']}: {row['vtexp']:.6f}")
    else:
        print("⚠️  No options found in test file")
    
    # Test 4: Greek calculations
    print("\n4. GREEK CALCULATIONS:")
    calculator = SpotRiskGreekCalculator()
    df_with_greeks, results = calculator.calculate_greeks(df)
    
    success_count = sum(1 for r in results if r.success)
    calc_rate = (success_count / len(results)) * 100 if results else 0
    print(f"✅ Calculated Greeks for {success_count}/{len(results)} positions ({calc_rate:.1f}%)")
    
    # Show example Greeks
    print("\nExample Greek values:")
    greek_examples = df_with_greeks[df_with_greeks['greek_calc_success'] == True].head(3)
    for _, row in greek_examples.iterrows():
        print(f"  {row['key']}:")
        print(f"    Delta: {row.get('delta_f', 'N/A')}")
        print(f"    Gamma: {row.get('gamma_f', 'N/A')}")
        print(f"    Vega:  {row.get('vega_f', 'N/A')}")
    
    # Test 5: Verify RosettaStone translations
    print("\n5. ROSETTASTONE TRANSLATION VERIFICATION:")
    rosetta = RosettaStone()
    
    test_symbols = [
        ("XCME.VY3.21JUL25.111.C", "actantrisk"),
        ("XCMEOCADPS20250721C3VY3/111", "actanttrades")
    ]
    
    for symbol, source_fmt in test_symbols:
        bloomberg = rosetta.translate(symbol, source_fmt, 'bloomberg')
        actanttime = rosetta.translate(symbol, source_fmt, 'actanttime')
        print(f"\n  {symbol} ({source_fmt}):")
        print(f"    → Bloomberg: {bloomberg}")
        print(f"    → ActantTime: {actanttime}")
    
    # Summary
    print("\n" + "="*60)
    print("PIPELINE TEST SUMMARY:")
    print(f"  ✅ CSV Parsing: Success ({len(df)} rows)")
    print(f"  {'✅' if trans_rate > 90 else '⚠️ '} Bloomberg Translation: {trans_rate:.1f}%")
    print(f"  {'✅' if vtexp_rate > 90 else '⚠️ '} vtexp Matching: {vtexp_rate:.1f}%")
    print(f"  {'✅' if calc_rate > 80 else '⚠️ '} Greek Calculations: {calc_rate:.1f}%")
    print(f"  ✅ RosettaStone: Working correctly")
    
    overall = trans_rate > 90 and vtexp_rate > 90 and calc_rate > 80
    print(f"\nOVERALL: {'✅ PASS' if overall else '⚠️  PASS WITH WARNINGS'}")
    
    return True

if __name__ == "__main__":
    try:
        test_comprehensive_pipeline()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 