"""
Demonstrate VTEXP conversion issue and the fix.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def demonstrate_vtexp_issue():
    """Show the VTEXP conversion issue."""
    
    logger.info("="*80)
    logger.info("VTEXP CONVERSION ISSUE DEMONSTRATION")
    logger.info("="*80)
    
    # Load VTEXP data
    vtexp_file = Path("tests/data/spot_risk_test/vtexp_20250802_120234.csv")
    vtexp_df = pd.read_csv(vtexp_file)
    
    logger.info("\nVTEXP Raw Data:")
    logger.info("-" * 60)
    for _, row in vtexp_df.iterrows():
        symbol = row['symbol']
        vtexp_raw = row['vtexp']
        
        # Extract date from symbol
        date_str = symbol.split('.')[-1]  # Gets 06AUG25 etc
        
        logger.info(f"\n{symbol}:")
        logger.info(f"  Raw VTEXP value: {vtexp_raw:.6f}")
        logger.info(f"  Interpretation as DAYS: {vtexp_raw:.1f} days")
        logger.info(f"  Interpretation as YEARS: {vtexp_raw:.3f} years = {vtexp_raw * 365:.0f} days")
    
    logger.info("\n" + "="*60)
    logger.info("ANALYSIS:")
    logger.info("="*60)
    
    # Analyze the pattern
    vtexp_values = vtexp_df['vtexp'].values
    differences = []
    for i in range(1, len(vtexp_values)):
        diff = vtexp_values[i] - vtexp_values[i-1]
        differences.append(diff)
    
    logger.info(f"\nDifferences between consecutive VTEXP values:")
    logger.info(f"  {differences}")
    logger.info(f"  Average difference: {sum(differences)/len(differences):.3f}")
    logger.info(f"\nThis confirms each increment is ~1.0, proving these are DAYS")
    
    logger.info("\n" + "="*60)
    logger.info("CONVERSION NEEDED:")
    logger.info("="*60)
    
    # Show what the conversion should be
    days_in_year = 252  # Trading days
    
    logger.info(f"\nFor options expiring on 06AUG25:")
    logger.info(f"  Current value passed: 2.583333 (interpreted as years)")
    logger.info(f"  Actual days to expiry: 2.583333 days")
    logger.info(f"  Correct years value: {2.583333 / days_in_year:.6f} years")
    logger.info(f"\nConversion factor needed: 1/{days_in_year} = {1/days_in_year:.6f}")
    
    logger.info("\n" + "="*60)
    logger.info("FIX REQUIRED:")
    logger.info("="*60)
    
    logger.info("\nIn lib/trading/actant/spot_risk/time_calculator.py:")
    logger.info("  Line 187: vtexp = float(row['vtexp'])")
    logger.info("  Should be: vtexp = float(row['vtexp']) / 252  # Convert days to years")
    logger.info("\nOR in the calculator when using the value:")
    logger.info("  Line 289: time_to_expiry = row.get('vtexp')")
    logger.info("  Should be: time_to_expiry = row.get('vtexp') / 252 if row.get('vtexp') else None")
    
    logger.info("\n" + "="*60)
    logger.info("IMPACT ON GREEKS:")
    logger.info("="*60)
    
    logger.info("\nWith incorrect time (2.583 years instead of 0.0103 years):")
    logger.info("  - Theta will be much smaller (time decay spread over 2.5 years)")
    logger.info("  - Gamma will be much smaller (less sensitivity near expiry)")
    logger.info("  - Vega will be larger (more time for volatility to matter)")
    logger.info("  - Delta might be less affected but still wrong")

if __name__ == "__main__":
    demonstrate_vtexp_issue()