"""
Test to investigate time-to-expiry calculations in spot risk pipeline.

This test traces how VTEXP values are loaded, parsed, and converted
to show exactly what parameters are sent to Greek calculations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from tabulate import tabulate
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Import modules to test
from lib.trading.actant.spot_risk.parser import (
    parse_spot_risk_csv, 
    extract_datetime_from_filename,
    parse_expiry_from_key
)
# We'll use these functions if needed later
from lib.trading.market_prices.rosetta_stone import RosettaStone

def investigate_time_to_expiry():
    """Investigate time-to-expiry calculations step by step."""
    
    logger.info("="*80)
    logger.info("TIME-TO-EXPIRY INVESTIGATION")
    logger.info("="*80)
    
    # Load test data
    csv_file = Path("tests/data/spot_risk_test/bav_analysis_20250801_140005_chunk_01_of_16.csv")
    vtexp_file = Path("tests/data/spot_risk_test/vtexp_20250802_120234.csv")
    
    # Extract timestamp from filename
    timestamp = extract_datetime_from_filename(csv_file.name)
    logger.info(f"\nCSV Timestamp: {timestamp}")
    logger.info(f"Date: {timestamp.date()}")
    
    # Load raw VTEXP data
    logger.info("\n" + "="*60)
    logger.info("RAW VTEXP DATA:")
    logger.info("="*60)
    vtexp_df = pd.read_csv(vtexp_file)
    logger.info(f"\nVTEXP file: {vtexp_file.name}")
    logger.info("Contents:")
    for _, row in vtexp_df.iterrows():
        logger.info(f"  {row['symbol']}: {row['vtexp']:.6f} years")
    
    # Parse spot risk CSV
    logger.info("\n" + "="*60)
    logger.info("PARSING SPOT RISK CSV:")
    logger.info("="*60)
    
    df = parse_spot_risk_csv(csv_file)
    
    # Filter to options only
    options_df = df[df['itype'].isin(['C', 'P'])].copy()
    
    # Extract future price
    future_row = df[df['itype'] == 'F'].iloc[0]
    future_price = future_row['midpoint_price']
    logger.info(f"\nFuture Price: {future_price}")
    
    # Initialize components
    rosetta = RosettaStone()
    
    # Load VTEXP data
    vtexp_data = vtexp_df.set_index('symbol')['vtexp'].to_dict()
    
    logger.info("\n" + "="*60)
    logger.info("OPTION ANALYSIS:")
    logger.info("="*60)
    
    results = []
    
    for idx, row in options_df.iterrows():
        logger.info(f"\n{idx+1}. {row['key']}")
        logger.info("-" * 40)
        
        # Parse expiry date
        expiry_str = parse_expiry_from_key(row['key'])
        logger.info(f"Expiry string from key: {expiry_str}")
        
        # Get Bloomberg symbol
        bloomberg_symbol = row['bloomberg_symbol']
        logger.info(f"Bloomberg symbol: {bloomberg_symbol}")
        
        # Extract components from Bloomberg symbol
        # Format: TYWQ25C1 112 Comdty
        parts = bloomberg_symbol.split()
        if len(parts) >= 2:
            option_code = parts[0]  # TYWQ25C1
            strike = float(parts[1])
            
            # Parse option code
            # TY = underlying, W = month code, Q25 = quarter/year, C1 = call series 1
            logger.info(f"Option code: {option_code}")
            logger.info(f"Strike: {strike}")
        
        # Get VTEXP value
        vtexp_value = vtexp_data.get(bloomberg_symbol, None)
        logger.info(f"VTEXP value: {vtexp_value} years" if vtexp_value else "VTEXP value: NOT FOUND")
        
        # Get market price
        if row['price_source'] == 'adjtheor':
            market_price = row['adjtheor']
        else:
            market_price = row['midpoint_price']
        
        # Collect all parameters
        result = {
            'actant_symbol': row['key'],
            'bloomberg_symbol': bloomberg_symbol,
            'type': 'call' if row['itype'] == 'C' else 'put',
            'strike': row['strike'],
            'future_price': future_price,
            'market_price': market_price,
            'price_source': row['price_source'],
            'vtexp_years': vtexp_value,
            'expiry_str': expiry_str,
            'csv_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        results.append(result)
        
        # Display all parameters
        logger.info(f"\nGREEK CALCULATION PARAMETERS:")
        logger.info(f"  Model: bachelier_v1")
        logger.info(f"  Future Price (F): {future_price}")
        logger.info(f"  Strike (K): {row['strike']}")
        logger.info(f"  Time to Expiry (T): {vtexp_value} years")
        logger.info(f"  Market Price: {market_price}")
        logger.info(f"  Option Type: {'call' if row['itype'] == 'C' else 'put'}")
        logger.info(f"  DV01: 64.2")
        logger.info(f"  Convexity: 0.0042")
    
    # Create summary table
    logger.info("\n" + "="*60)
    logger.info("PARAMETER SUMMARY TABLE:")
    logger.info("="*60)
    
    summary_data = []
    for r in results:
        summary_data.append([
            r['actant_symbol'],
            r['type'].upper(),
            f"{r['strike']:.2f}",
            f"{r['future_price']:.6f}",
            f"{r['market_price']:.6f}",
            r['price_source'],
            f"{r['vtexp_years']:.6f}" if r['vtexp_years'] else "N/A",
            r['expiry_str']
        ])
    
    headers = ['Symbol', 'Type', 'Strike', 'Future', 'Mkt Price', 'Price Src', 'T (years)', 'Expiry']
    logger.info("\n" + tabulate(summary_data, headers=headers, tablefmt='grid'))
    
    # Analyze the time to expiry issue
    logger.info("\n" + "="*60)
    logger.info("TIME TO EXPIRY ANALYSIS:")
    logger.info("="*60)
    
    logger.info(f"\nCSV Date: {timestamp.date()} (2025-08-01)")
    logger.info(f"Option Expiry: 06AUG25 (2025-08-06)")
    logger.info(f"Expected days to expiry: 5 days")
    logger.info(f"Expected years to expiry: ~0.0137 years (5/365)")
    logger.info(f"\nActual VTEXP value: 2.583333 years")
    logger.info(f"This corresponds to: ~943 days")
    
    logger.info("\nPOSSIBLE ISSUES:")
    logger.info("1. VTEXP file might be stale or for wrong date")
    logger.info("2. Date parsing might be incorrect")
    logger.info("3. VTEXP calculation might include extra time")
    
    # Check VTEXP file timestamp
    vtexp_timestamp = datetime.strptime("20250802_120234", "%Y%m%d_%H%M%S")
    logger.info(f"\nVTEXP file timestamp: {vtexp_timestamp}")
    logger.info(f"VTEXP generated on: 2025-08-02 12:02:34")
    
    # Manual calculation
    logger.info("\nMANUAL CALCULATION:")
    csv_date = datetime(2025, 8, 1)
    expiry_date = datetime(2025, 8, 6)
    days_diff = (expiry_date - csv_date).days
    years_diff = days_diff / 365.0
    logger.info(f"CSV date: {csv_date.date()}")
    logger.info(f"Expiry date: {expiry_date.date()}")
    logger.info(f"Days difference: {days_diff}")
    logger.info(f"Years difference: {years_diff:.6f}")
    
    # Save detailed results
    output_dir = Path("tests/output/time_to_expiry_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / "parameter_analysis.csv", index=False)
    logger.info(f"\nDetailed results saved to: {output_dir / 'parameter_analysis.csv'}")

if __name__ == "__main__":
    investigate_time_to_expiry()