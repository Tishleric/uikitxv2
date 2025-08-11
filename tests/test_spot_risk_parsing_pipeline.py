"""
Unit tests for Spot Risk CSV parsing pipeline.

This test suite validates the CSV parsing and parameter extraction phase
of the spot risk pipeline, from file detection through to Greek calculation inputs.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import tempfile
import shutil
import time
import multiprocessing
import threading

# Import the modules we're testing
from lib.trading.actant.spot_risk.parser import (
    parse_spot_risk_csv, 
    extract_datetime_from_filename, 
    parse_expiry_from_key
)
from lib.trading.actant.spot_risk.file_watcher import (
    SpotRiskFileHandler,
    _wait_for_file_stabilization,
    calculation_worker
)
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator
from lib.trading.market_prices.rosetta_stone import RosettaStone


# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSpotRiskParsingPipeline(unittest.TestCase):
    """Test suite for spot risk CSV parsing pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data directory and files."""
        cls.test_dir = Path("tests/data/spot_risk_test")
        cls.csv_file = cls.test_dir / "bav_analysis_20250801_140005_chunk_01_of_16.csv"
        cls.vtexp_file = cls.test_dir / "vtexp_20250802_120234.csv"
        
        # Ensure test files exist
        if not cls.csv_file.exists():
            raise FileNotFoundError(f"Test CSV file not found: {cls.csv_file}")
        if not cls.vtexp_file.exists():
            raise FileNotFoundError(f"Test VTEXP file not found: {cls.vtexp_file}")
            
        # Load VTEXP data for tests
        vtexp_df = pd.read_csv(cls.vtexp_file)
        cls.vtexp_data = vtexp_df.set_index('symbol')['vtexp'].to_dict()
        
        logger.info(f"Test data directory: {cls.test_dir}")
        logger.info(f"Test CSV file: {cls.csv_file}")
        logger.info(f"Test VTEXP file: {cls.vtexp_file}")
        
    def setUp(self):
        """Set up each test."""
        self.symbol_translator = RosettaStone()
        
    def test_1_file_detection_and_pattern_matching(self):
        """Test 1: File Detection - Validate filename pattern matching and batch identification."""
        logger.info("\n=== TEST 1: File Detection and Pattern Matching ===")
        
        # Create mock components
        task_queue = Mock()
        total_files_per_batch = {}
        vtexp_cache = {'data': self.vtexp_data, 'filepath': str(self.vtexp_file)}
        watcher_ref = Mock()
        watcher_ref.positions_lock = threading.Lock()
        watcher_ref.positions_cache = {'TYU5': True, 'USU5': True}  # Mock positions
        
        # Create file handler
        handler = SpotRiskFileHandler(
            task_queue=task_queue,
            total_files_per_batch=total_files_per_batch,
            vtexp_cache=vtexp_cache,
            watcher_ref=watcher_ref
        )
        
        # Test filename pattern matching
        test_cases = [
            ("bav_analysis_20250801_140005_chunk_01_of_16.csv", True, "20250801_140005", "01", "16"),
            ("bav_analysis_20250801_140005_chunk_10_of_16.csv", True, "20250801_140005", "10", "16"),
            ("bav_analysis_20250801_140005.csv", False, None, None, None),  # Old format
            ("random_file.csv", False, None, None, None),
        ]
        
        for filename, should_match, expected_batch, expected_chunk, expected_total in test_cases:
            match = handler.filename_pattern.match(filename)
            
            if should_match:
                self.assertIsNotNone(match, f"Failed to match valid filename: {filename}")
                batch_id, chunk_num, total_chunks = match.groups()
                self.assertEqual(batch_id, expected_batch)
                self.assertEqual(chunk_num, expected_chunk)
                self.assertEqual(total_chunks, expected_total)
                logger.info(f"✓ Matched: {filename} -> batch={batch_id}, chunk={chunk_num}/{total_chunks}")
            else:
                self.assertIsNone(match, f"Incorrectly matched invalid filename: {filename}")
                logger.info(f"✓ Rejected: {filename}")
                
        # Test file event handling
        event = Mock()
        event.is_directory = False
        event.src_path = str(self.csv_file)
        
        # Process the event
        handler.on_created(event)
        
        # Verify task was queued
        task_queue.put.assert_called_once()
        call_args = task_queue.put.call_args[0][0]
        
        self.assertEqual(call_args[0], "20250801_140005")  # batch_id
        self.assertEqual(call_args[1], str(self.csv_file))  # filepath
        self.assertEqual(call_args[2], self.vtexp_data)  # vtexp_data
        self.assertEqual(call_args[3], {'TYU5': True, 'USU5': True})  # positions_snapshot
        
        logger.info(f"✓ File event processed and queued successfully")
        
    def test_2_csv_parsing_and_column_mapping(self):
        """Test 2: CSV Parsing - Validate data loading and column mapping."""
        logger.info("\n=== TEST 2: CSV Parsing and Column Mapping ===")
        
        # Parse the CSV file
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=False)
        
        # Validate basic properties
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "DataFrame should not be empty")
        
        # Log DataFrame info
        logger.info(f"Parsed {len(df)} rows from CSV")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Check required columns exist (lowercase)
        required_columns = ['key', 'bid', 'ask', 'strike', 'itype']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")
            
        # Check added columns
        self.assertIn('midpoint_price', df.columns, "Missing calculated midpoint_price column")
        self.assertIn('expiry_date', df.columns, "Missing parsed expiry_date column")
        
        # Validate data types
        numeric_columns = ['bid', 'ask', 'strike', 'midpoint_price']
        for col in numeric_columns:
            if col in df.columns:
                self.assertTrue(
                    pd.api.types.is_numeric_dtype(df[col]),
                    f"Column {col} should be numeric"
                )
                
        # Log sample data
        logger.info("\nSample parsed data:")
        for idx, row in df.head(5).iterrows():
            logger.info(f"  Row {idx}: key={row['key']}, itype={row['itype']}, "
                       f"strike={row.get('strike', 'N/A')}, midpoint={row['midpoint_price']:.4f}")
                       
        # Test price calculation logic
        adjtheor_count = df['price_source'].value_counts().get('adjtheor', 0)
        calculated_count = df['price_source'].value_counts().get('calculated', 0)
        
        logger.info(f"\nPrice sources: adjtheor={adjtheor_count}, calculated={calculated_count}")
        self.assertGreater(adjtheor_count + calculated_count, 0, "Should have valid prices")
        
    def test_3_symbol_translation_and_identification(self):
        """Test 3: Symbol Translation - Test Actant to Bloomberg symbol translation."""
        logger.info("\n=== TEST 3: Symbol Translation and Identification ===")
        
        # Parse CSV with Bloomberg translation
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=False)
        
        # Check Bloomberg symbols were added
        self.assertIn('bloomberg_symbol', df.columns, "Missing bloomberg_symbol column")
        
        # Test specific translations
        translation_tests = []
        
        for idx, row in df.iterrows():
            actant_key = row['key']
            bloomberg_symbol = row['bloomberg_symbol']
            itype = row['itype']
            
            # Log translation
            translation_tests.append({
                'actant': actant_key,
                'bloomberg': bloomberg_symbol,
                'itype': itype,
                'is_future': itype.upper() == 'F',
                'is_option': itype.upper() in ['C', 'P']
            })
            
        # Log all translations
        logger.info("\nSymbol translations:")
        for test in translation_tests[:10]:  # First 10
            status = "✓" if test['bloomberg'] else "✗"
            logger.info(f"  {status} {test['actant']} -> {test['bloomberg']} (type={test['itype']})")
            
        # Validate futures
        futures = [t for t in translation_tests if t['is_future']]
        self.assertGreater(len(futures), 0, "Should have at least one future")
        
        for future in futures:
            self.assertIsNotNone(future['bloomberg'], f"Future should translate: {future['actant']}")
            logger.info(f"✓ Future identified: {future['actant']} -> {future['bloomberg']}")
            
        # Validate options
        options = [t for t in translation_tests if t['is_option']]
        self.assertGreater(len(options), 0, "Should have at least one option")
        
        # Group options by type
        calls = [o for o in options if o['itype'].upper() == 'C']
        puts = [o for o in options if o['itype'].upper() == 'P']
        
        logger.info(f"\nInstrument breakdown: {len(futures)} futures, {len(calls)} calls, {len(puts)} puts")
        
    def test_4_future_price_extraction(self):
        """Test 4: Future Price Extraction - Identify future rows and extract prices."""
        logger.info("\n=== TEST 4: Future Price Extraction ===")
        
        df = parse_spot_risk_csv(self.csv_file, calculate_time_to_expiry=False)
        
        # Create calculator instance
        calculator = SpotRiskGreekCalculator()
        
        # Test future price extraction logic (from calculate_greeks method)
        future_price = None
        
        # Find future rows
        future_mask = df['itype'].str.upper() == 'F'
        future_rows = df[future_mask]
        
        logger.info(f"Found {len(future_rows)} future rows")
        
        self.assertGreater(len(future_rows), 0, "Should find at least one future")
        
        # Extract future price
        if len(future_rows) > 0:
            future_row = future_rows.iloc[0]
            future_price = future_row['midpoint_price']
            
            logger.info(f"\nFuture details:")
            logger.info(f"  Key: {future_row['key']}")
            logger.info(f"  Bloomberg: {future_row.get('bloomberg_symbol', 'N/A')}")
            logger.info(f"  Bid: {future_row['bid']}")
            logger.info(f"  Ask: {future_row['ask']}")
            logger.info(f"  Midpoint: {future_price}")
            logger.info(f"  Price Source: {future_row.get('price_source', 'N/A')}")
            
        self.assertIsNotNone(future_price, "Should extract future price")
        self.assertGreater(future_price, 0, "Future price should be positive")
        
        # Test that options can be mapped to this future
        option_mask = df['itype'].str.upper().isin(['C', 'P'])
        options_df = df[option_mask]
        
        logger.info(f"\n{len(options_df)} options will use future price: {future_price}")
        
        # Log sample option-to-future mapping
        for idx, option in options_df.head(3).iterrows():
            logger.info(f"  Option {option['key']} (strike={option['strike']}) -> Future price={future_price}")
            
    def test_5_vtexp_mapping(self):
        """Test 5: VTEXP Mapping - Test time-to-expiry mapping for options."""
        logger.info("\n=== TEST 5: VTEXP Mapping ===")
        
        # Parse CSV with time to expiry calculation
        df = parse_spot_risk_csv(
            self.csv_file, 
            calculate_time_to_expiry=True,
            vtexp_data=self.vtexp_data
        )
        
        # Check vtexp column was added
        self.assertIn('vtexp', df.columns, "Missing vtexp column")
        
        # Analyze VTEXP mappings
        vtexp_analysis = []
        
        for idx, row in df.iterrows():
            if row['itype'].upper() in ['C', 'P']:  # Options only
                vtexp_analysis.append({
                    'key': row['key'],
                    'expiry_date': row.get('expiry_date'),
                    'vtexp': row.get('vtexp'),
                    'has_vtexp': pd.notna(row.get('vtexp'))
                })
                
        # Log VTEXP mapping results
        logger.info("\nVTEXP mapping results:")
        
        mapped_count = sum(1 for a in vtexp_analysis if a['has_vtexp'])
        total_count = len(vtexp_analysis)
        
        logger.info(f"Successfully mapped: {mapped_count}/{total_count} options")
        
        # Show sample mappings
        for analysis in vtexp_analysis[:5]:
            status = "✓" if analysis['has_vtexp'] else "✗"
            vtexp_str = f"{analysis['vtexp']:.6f}" if analysis['has_vtexp'] else "N/A"
            logger.info(f"  {status} {analysis['key']} (expiry={analysis['expiry_date']}) -> vtexp={vtexp_str}")
            
        # Validate VTEXP values
        vtexp_values = [a['vtexp'] for a in vtexp_analysis if a['has_vtexp']]
        
        if vtexp_values:
            self.assertTrue(all(v > 0 for v in vtexp_values), "All VTEXP values should be positive")
            logger.info(f"\nVTEXP range: {min(vtexp_values):.6f} to {max(vtexp_values):.6f}")
            
    def test_6_parameter_assembly_for_greeks(self):
        """Test 6: Parameter Assembly - Validate all parameters needed for Greek calculations."""
        logger.info("\n=== TEST 6: Parameter Assembly for Greek Calculations ===")
        
        # Parse CSV with all processing
        df = parse_spot_risk_csv(
            self.csv_file,
            calculate_time_to_expiry=True,
            vtexp_data=self.vtexp_data
        )
        
        # Extract future price
        future_rows = df[df['itype'].str.upper() == 'F']
        future_price = future_rows.iloc[0]['midpoint_price'] if len(future_rows) > 0 else None
        
        self.assertIsNotNone(future_price, "Need future price for Greek calculations")
        
        # Get options
        options_df = df[df['itype'].str.upper().isin(['C', 'P'])]
        
        logger.info(f"\nPreparing {len(options_df)} options for Greek calculation")
        logger.info(f"Using future price: {future_price}")
        
        # Validate each option has required parameters
        missing_params = []
        valid_options = []
        
        for idx, option in options_df.iterrows():
            params = {
                'instrument_key': option['key'],
                'bloomberg_symbol': option.get('bloomberg_symbol'),
                'option_type': 'call' if option['itype'].upper() == 'C' else 'put',
                'strike': option.get('strike'),
                'market_price': option.get('midpoint_price'),
                'time_to_expiry': option.get('vtexp'),
                'future_price': future_price
            }
            
            # Check for missing values
            missing = [k for k, v in params.items() if pd.isna(v) or v is None]
            
            if missing:
                missing_params.append((option['key'], missing))
            else:
                valid_options.append(params)
                
        # Log parameter assembly results
        logger.info(f"\nParameter assembly results:")
        logger.info(f"  Valid options: {len(valid_options)}")
        logger.info(f"  Missing parameters: {len(missing_params)}")
        
        # Show sample valid parameters
        if valid_options:
            logger.info("\nSample option parameters for Greek calculation:")
            for params in valid_options[:3]:
                logger.info(f"\n  {params['instrument_key']}:")
                logger.info(f"    Bloomberg: {params['bloomberg_symbol']}")
                logger.info(f"    Type: {params['option_type']}")
                logger.info(f"    Strike: {params['strike']}")
                logger.info(f"    Market Price: {params['market_price']:.4f}")
                logger.info(f"    Future Price: {params['future_price']:.4f}")
                logger.info(f"    Time to Expiry: {params['time_to_expiry']:.6f} years")
                
        # Show any missing parameters
        if missing_params:
            logger.warning("\nOptions with missing parameters:")
            for key, missing in missing_params[:5]:
                logger.warning(f"  {key}: missing {missing}")
                
        # Validate we have enough valid options
        self.assertGreater(len(valid_options), 0, "Should have at least some valid options")
        
        # Calculate the percentage of successful parameter assembly
        success_rate = len(valid_options) / len(options_df) * 100
        logger.info(f"\nParameter assembly success rate: {success_rate:.1f}%")
        
    def test_7_end_to_end_worker_simulation(self):
        """Test 7: End-to-End Worker Simulation - Simulate the complete worker process."""
        logger.info("\n=== TEST 7: End-to-End Worker Process Simulation ===")
        
        # Create queues
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        
        # Prepare task data
        batch_id = "20250801_140005"
        filepath_str = str(self.csv_file)
        positions_snapshot = {'TYU5', 'USU5', 'TYH5C 116', 'TYH5P 114'}  # Mock positions
        
        # Put task in queue
        task_queue.put((batch_id, filepath_str, self.vtexp_data, positions_snapshot))
        
        # Mock the calculation worker's key steps
        logger.info(f"\nSimulating worker process for batch {batch_id}")
        
        # 1. File stabilization check
        file_stable = _wait_for_file_stabilization(Path(filepath_str), timeout=1)
        self.assertTrue(file_stable, "File should be stable")
        logger.info("✓ File stabilization check passed")
        
        # 2. Parse CSV
        df = parse_spot_risk_csv(filepath_str, calculate_time_to_expiry=True, vtexp_data=self.vtexp_data)
        logger.info(f"✓ Parsed {len(df)} rows from CSV")
        
        # 3. Symbol translation for filtering
        df['bloomberg_symbol'] = df['key'].apply(
            lambda x: self.symbol_translator.translate(x, 'actantrisk', 'bloomberg') if x else None
        )
        
        # 4. Position filtering
        original_count = len(df)
        is_future = df['itype'].str.upper() == 'F'
        has_position = df['bloomberg_symbol'].isin(positions_snapshot)
        df_filtered = df[is_future | has_position]
        
        logger.info(f"✓ Filtered {original_count} -> {len(df_filtered)} rows (kept futures + positions)")
        
        # 5. Verify we have data for Greek calculations
        future_rows = df_filtered[df_filtered['itype'].str.upper() == 'F']
        option_rows = df_filtered[df_filtered['itype'].str.upper().isin(['C', 'P'])]
        
        self.assertGreater(len(future_rows), 0, "Should have at least one future after filtering")
        
        logger.info(f"\nFiltered data summary:")
        logger.info(f"  Futures: {len(future_rows)}")
        logger.info(f"  Options: {len(option_rows)}")
        
        # Log the futures and options we're keeping
        for _, future in future_rows.iterrows():
            logger.info(f"  Future: {future['key']} -> {future['bloomberg_symbol']}")
            
        for _, option in option_rows.head(5).iterrows():
            logger.info(f"  Option: {option['key']} -> {option['bloomberg_symbol']} (in positions: {option['bloomberg_symbol'] in positions_snapshot})")
            
        # 6. Prepare result
        result = (batch_id, Path(filepath_str).name, df_filtered)
        logger.info(f"\n✓ Worker simulation complete - would queue result with {len(df_filtered)} rows")
        
        
if __name__ == '__main__':
    unittest.main(verbosity=2)