"""
Unit tests for Spot Risk Greek Calculations.

This test suite validates Greek calculations with clear output for manual verification.
Tests use actual calculation functions to replicate live environment.
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import json
from tabulate import tabulate

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.greek_config import GreekConfiguration, DEFAULT_ENABLED_GREEKS
from lib.trading.bond_future_options.greek_calculator_api import GreekCalculatorAPI
from lib.trading.actant.spot_risk.calculator import GreekResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSpotRiskGreekCalculations(unittest.TestCase):
    """Test suite for Greek calculations with detailed output."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and configuration."""
        cls.test_dir = Path("tests/data/spot_risk_test")
        cls.csv_file = cls.test_dir / "bav_analysis_20250801_140005_chunk_01_of_16.csv"
        cls.vtexp_file = cls.test_dir / "vtexp_20250802_120234.csv"
        
        # Load VTEXP data
        vtexp_df = pd.read_csv(cls.vtexp_file)
        cls.vtexp_data = vtexp_df.set_index('symbol')['vtexp'].to_dict()
        
        # Create output directory for results
        cls.output_dir = Path("tests/output/greek_calculations")
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        
    def setUp(self):
        """Set up each test."""
        # Initialize Greek configuration with all Greeks enabled for testing
        all_greeks_enabled = {
            'delta_F': True,
            'delta_y': True,
            'theta_F': True,
            'gamma_F': True,
            'gamma_y': True,
            'speed_F': True,
            'speed_y': True,
            'vega_price': True,
            'vega_y': True,
            'volga_price': True,
            'vanna_F_price': True,
            'charm_F': True,
            'color_F': True,
            'ultima': True,
            'zomma': True
        }
        self.greek_config = GreekConfiguration(enabled_greeks=all_greeks_enabled)
        
        # Initialize calculator
        self.calculator = SpotRiskGreekCalculator(greek_config=self.greek_config)
        
    def test_1_greek_calculation_parameters(self):
        """Test 1: Verify parameters sent to Greek calculation API."""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: GREEK CALCULATION PARAMETER VERIFICATION")
        logger.info("="*80)
        
        # Parse test data
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        
        # Capture parameters sent to API
        captured_params = []
        
        # Mock the API analyze method to capture parameters
        original_analyze = self.calculator.api.analyze
        
        def capture_analyze(options_data, model=None, model_params=None, requested_greeks=None):
            # Capture the parameters
            for option in options_data:
                captured_params.append({
                    'option': option.copy(),
                    'model': model,
                    'model_params': model_params.copy() if model_params else None,
                    'requested_greeks': requested_greeks.copy() if requested_greeks else None
                })
            # Call original method
            return original_analyze(options_data, model, model_params, requested_greeks)
        
        self.calculator.api.analyze = capture_analyze
        
        # Calculate Greeks
        df_with_greeks, results = self.calculator.calculate_greeks(df)
        
        # Restore original method
        self.calculator.api.analyze = original_analyze
        
        # Display captured parameters
        logger.info("\nCAPTURED API PARAMETERS:")
        logger.info("-" * 60)
        
        param_table = []
        for i, params in enumerate(captured_params):
            option = params['option']
            param_table.append([
                i + 1,
                option.get('_instrument_key', 'N/A'),
                f"{option['F']:.6f}",
                f"{option['K']:.6f}",
                f"{option['T']:.6f}",
                f"{option['market_price']:.6f}",
                option['option_type']
            ])
        
        headers = ['#', 'Instrument', 'Future Price', 'Strike', 'Time to Exp', 'Market Price', 'Type']
        print("\n" + tabulate(param_table, headers=headers, tablefmt='grid'))
        
        # Display model parameters
        if captured_params:
            model_params = captured_params[0]['model_params']
            logger.info("\nMODEL PARAMETERS:")
            logger.info(f"  Model: {captured_params[0]['model']}")
            logger.info(f"  Future DV01: {model_params['future_dv01'] * 1000:.1f}")
            logger.info(f"  Future Convexity: {model_params['future_convexity']}")
            logger.info(f"  Yield Level: {model_params['yield_level']}")
            
            logger.info(f"\nRequested Greeks: {captured_params[0]['requested_greeks']}")
        
        # Save parameters to file
        param_file = self.output_dir / "api_parameters.json"
        with open(param_file, 'w') as f:
            json.dump(captured_params, f, indent=2, default=str)
        logger.info(f"\nParameters saved to: {param_file}")
        
    def test_2_greek_calculation_results(self):
        """Test 2: Calculate Greeks and display results for manual verification."""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: GREEK CALCULATION RESULTS")
        logger.info("="*80)
        
        # Parse test data
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        
        # Calculate Greeks
        df_with_greeks, results = self.calculator.calculate_greeks(df)
        
        # Extract option results only
        option_results = [r for r in results if r.instrument_key and 'XCME.WY' in r.instrument_key]
        
        # Create detailed results table
        results_data = []
        
        for result in option_results:
            if result.success:
                results_data.append({
                    'Symbol': result.instrument_key,
                    'Bloomberg': df[df['key'] == result.instrument_key]['bloomberg_symbol'].iloc[0] if not df[df['key'] == result.instrument_key].empty else 'N/A',
                    'Type': result.option_type.upper(),
                    'Strike': result.strike,
                    'Future Price': result.future_price,
                    'Market Price': result.market_price,
                    'Time to Exp': result.time_to_expiry,
                    'IV': result.implied_volatility,
                    'Delta_F': result.delta_F,
                    'Delta_y': result.delta_y,
                    'Gamma_F': result.gamma_F,
                    'Gamma_y': result.gamma_y,
                    'Theta_F': result.theta_F,
                    'Vega_y': result.vega_y,
                    'Speed_F': result.speed_F,
                    'Speed_y': result.speed_y
                })
        
        # Display results in clear format
        logger.info("\nGREEK CALCULATION RESULTS:")
        logger.info("=" * 150)
        
        for i, result in enumerate(results_data):
            print(f"\n{i+1}. {result['Symbol']} ({result['Bloomberg']})")
            print("-" * 60)
            
            # Input parameters
            print("INPUT PARAMETERS:")
            print(f"  Option Type:    {result['Type']}")
            print(f"  Strike (K):     {result['Strike']}")
            print(f"  Future (F):     {result['Future Price']:.6f}")
            print(f"  Market Price:   {result['Market Price']:.6f}")
            print(f"  Time to Exp:    {result['Time to Exp']:.6f} years")
            print(f"  Moneyness:      {result['Strike'] - result['Future Price']:.6f} ({((result['Strike']/result['Future Price'] - 1) * 100):.2f}%)")
            
            # Greeks
            print("\nCALCULATED GREEKS:")
            print(f"  Implied Vol:    {result['IV']:.6f}" if result['IV'] else "  Implied Vol:    N/A")
            print(f"  Delta (F):      {result['Delta_F']:.6f}" if result['Delta_F'] is not None else "  Delta (F):      N/A")
            print(f"  Delta (y):      {result['Delta_y']:.6f}" if result['Delta_y'] is not None else "  Delta (y):      N/A")
            print(f"  Gamma (F):      {result['Gamma_F']:.6f}" if result['Gamma_F'] is not None else "  Gamma (F):      N/A")
            print(f"  Gamma (y):      {result['Gamma_y']:.6f}" if result['Gamma_y'] is not None else "  Gamma (y):      N/A")
            print(f"  Theta (F):      {result['Theta_F']:.6f}" if result['Theta_F'] is not None else "  Theta (F):      N/A")
            print(f"  Vega (y):       {result['Vega_y']:.6f}" if result['Vega_y'] is not None else "  Vega (y):      N/A")
            print(f"  Speed (F):      {result['Speed_F']:.6f}" if result['Speed_F'] is not None else "  Speed (F):      N/A")
            print(f"  Speed (y):      {result['Speed_y']:.6f}" if result['Speed_y'] is not None else "  Speed (y):      N/A")
        
        # Save detailed results
        results_df = pd.DataFrame(results_data)
        results_file = self.output_dir / "greek_calculation_results.csv"
        results_df.to_csv(results_file, index=False)
        logger.info(f"\nDetailed results saved to: {results_file}")
        
        # Create summary table
        summary_data = []
        for r in results_data:
            summary_data.append([
                r['Bloomberg'],
                r['Type'],
                f"{r['Strike']}",
                f"{r['Market Price']:.4f}",
                f"{r['Delta_F']:.4f}" if r['Delta_F'] is not None else "N/A",
                f"{r['Gamma_F']:.4f}" if r['Gamma_F'] is not None else "N/A",
                f"{r['Theta_F']:.4f}" if r['Theta_F'] is not None else "N/A",
                f"{r['Vega_y']:.4f}" if r['Vega_y'] is not None else "N/A"
            ])
        
        headers = ['Symbol', 'Type', 'Strike', 'Price', 'Delta_F', 'Gamma_F', 'Theta_F', 'Vega_y']
        print("\n\nSUMMARY TABLE:")
        print(tabulate(summary_data, headers=headers, tablefmt='grid'))
        
    def test_3_greek_validation_checks(self):
        """Test 3: Validate Greek values are within reasonable ranges."""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: GREEK VALUE VALIDATION")
        logger.info("="*80)
        
        # Parse and calculate
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        df_with_greeks, results = self.calculator.calculate_greeks(df)
        
        validation_results = []
        
        for result in results:
            if result.success and result.option_type:
                validations = {
                    'Symbol': result.instrument_key,
                    'Type': result.option_type,
                    'Strike': result.strike,
                    'Validations': []
                }
                
                # Delta validation
                if result.delta_F is not None:
                    if result.option_type == 'call':
                        delta_valid = 0 <= result.delta_F <= 1
                        validations['Validations'].append(f"Delta ∈ [0,1]: {delta_valid} (actual: {result.delta_F:.4f})")
                    else:  # put
                        delta_valid = -1 <= result.delta_F <= 0
                        validations['Validations'].append(f"Delta ∈ [-1,0]: {delta_valid} (actual: {result.delta_F:.4f})")
                
                # Gamma validation (always positive)
                if result.gamma_F is not None:
                    gamma_valid = result.gamma_F >= 0
                    validations['Validations'].append(f"Gamma ≥ 0: {gamma_valid} (actual: {result.gamma_F:.6f})")
                
                # Theta validation (usually negative)
                if result.theta_F is not None:
                    theta_sign = "negative" if result.theta_F < 0 else "positive"
                    validations['Validations'].append(f"Theta sign: {theta_sign} (actual: {result.theta_F:.6f})")
                
                # Vega validation (always positive)
                if result.vega_y is not None:
                    vega_valid = result.vega_y >= 0
                    validations['Validations'].append(f"Vega ≥ 0: {vega_valid} (actual: {result.vega_y:.6f})")
                
                validation_results.append(validations)
        
        # Display validation results
        logger.info("\nGREEK VALIDATION RESULTS:")
        for val in validation_results:
            print(f"\n{val['Symbol']} ({val['Type'].upper()} @ {val['Strike']})")
            for check in val['Validations']:
                status = "✓" if "True" in check else "✗"
                print(f"  {status} {check}")
        
    def test_4_moneyness_analysis(self):
        """Test 4: Analyze Greeks by moneyness."""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: MONEYNESS ANALYSIS")
        logger.info("="*80)
        
        # Parse and calculate
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        df_with_greeks, results = self.calculator.calculate_greeks(df)
        
        # Get future price
        future_price = df[df['itype'].str.upper() == 'F']['midpoint_price'].iloc[0]
        
        moneyness_data = []
        
        for result in results:
            if result.success and result.option_type:
                moneyness = result.strike - future_price
                moneyness_pct = (result.strike / future_price - 1) * 100
                
                # Determine ITM/OTM status
                if result.option_type == 'call':
                    status = "ITM" if moneyness < 0 else "OTM" if moneyness > 0 else "ATM"
                else:
                    status = "ITM" if moneyness > 0 else "OTM" if moneyness < 0 else "ATM"
                
                moneyness_data.append({
                    'Symbol': result.instrument_key,
                    'Type': result.option_type.upper(),
                    'Strike': result.strike,
                    'Moneyness': moneyness,
                    'Moneyness %': moneyness_pct,
                    'Status': status,
                    'Delta': result.delta_F,
                    'Gamma': result.gamma_F,
                    'Theta': result.theta_F,
                    'Vega': result.vega_y
                })
        
        # Sort by moneyness
        moneyness_data.sort(key=lambda x: x['Moneyness'])
        
        # Display moneyness analysis
        logger.info(f"\nMONEYNESS ANALYSIS (Future Price: {future_price:.6f})")
        logger.info("-" * 100)
        
        table_data = []
        for m in moneyness_data:
            table_data.append([
                m['Type'],
                f"{m['Strike']}",
                f"{m['Moneyness']:.4f}",
                f"{m['Moneyness %']:.2f}%",
                m['Status'],
                f"{m['Delta']:.4f}" if m['Delta'] is not None else "N/A",
                f"{m['Gamma']:.6f}" if m['Gamma'] is not None else "N/A"
            ])
        
        headers = ['Type', 'Strike', 'Moneyness', 'Money%', 'Status', 'Delta', 'Gamma']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
    def test_5_greek_config_performance(self):
        """Test 5: Compare performance with different Greek configurations."""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: GREEK CONFIGURATION PERFORMANCE")
        logger.info("="*80)
        
        # Parse test data
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        
        import time
        
        # Test 1: Minimal Greeks
        config_minimal = GreekConfiguration()  # Default minimal set
        calc_minimal = SpotRiskGreekCalculator(greek_config=config_minimal)
        
        start_time = time.time()
        df_minimal, results_minimal = calc_minimal.calculate_greeks(df.copy())
        time_minimal = time.time() - start_time
        
        # Test 2: All Greeks
        all_greeks = {greek: True for greek in DEFAULT_ENABLED_GREEKS.keys()}
        config_all = GreekConfiguration(enabled_greeks=all_greeks)
        calc_all = SpotRiskGreekCalculator(greek_config=config_all)
        
        start_time = time.time()
        df_all, results_all = calc_all.calculate_greeks(df.copy())
        time_all = time.time() - start_time
        
        # Display comparison
        logger.info("\nPERFORMANCE COMPARISON:")
        logger.info(f"  Minimal Greeks ({len(config_minimal.get_enabled_greeks())} enabled): {time_minimal:.3f} seconds")
        logger.info(f"  All Greeks ({len(config_all.get_enabled_greeks())} enabled): {time_all:.3f} seconds")
        logger.info(f"  Speed improvement: {((time_all - time_minimal) / time_all * 100):.1f}% faster")
        
        logger.info(f"\nMinimal Greeks: {config_minimal.get_enabled_greeks()}")
        logger.info(f"All Greeks: {config_all.get_enabled_greeks()}")
        
        # Compare results
        logger.info("\nRESULT COMPARISON (Sample Option):")
        if results_minimal and results_all:
            sample_min = next((r for r in results_minimal if r.option_type == 'call'), None)
            sample_all = next((r for r in results_all if r.option_type == 'call'), None)
            
            if sample_min and sample_all:
                logger.info(f"\nOption: {sample_min.instrument_key}")
                logger.info("Greeks available in minimal config:")
                for greek in ['delta_F', 'gamma_F', 'theta_F', 'vega_y']:
                    value = getattr(sample_min, greek, None)
                    logger.info(f"  {greek}: {value:.6f}" if value is not None else f"  {greek}: N/A")
                
                logger.info("\nAdditional Greeks in full config:")
                for greek in ['volga_price', 'vanna_F_price', 'charm_F', 'speed_F']:
                    value = getattr(sample_all, greek, None)
                    logger.info(f"  {greek}: {value:.6f}" if value is not None else f"  {greek}: N/A")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)