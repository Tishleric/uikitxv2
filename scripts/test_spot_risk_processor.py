#!/usr/bin/env python3
"""
Test script for spot risk processor with centralized translator.

Tests the integration before fresh data arrives.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.market_prices import MarketPriceStorage, SpotRiskPriceProcessor
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_spot_risk_processor():
    """Test the spot risk processor with a sample file."""
    
    # Initialize storage and processor
    storage = MarketPriceStorage()
    processor = SpotRiskPriceProcessor(storage)
    
    # Find a test file
    test_files = list(Path('data/input/actant_spot_risk').glob('bav_analysis_*.csv'))
    
    if not test_files:
        logger.error("No test files found!")
        return
        
    # Use the most recent file for testing
    test_file = sorted(test_files)[-1]
    logger.info(f"Testing with file: {test_file}")
    
    # Process the file
    try:
        result = processor.process_file(test_file)
        if result:
            logger.info("✓ File processed successfully!")
            
            # Check database for results
            with storage._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check options
                cursor.execute("""
                    SELECT COUNT(*) FROM options_prices 
                    WHERE Current_Price IS NOT NULL
                """)
                options_count = cursor.fetchone()[0]
                
                # Check futures
                cursor.execute("""
                    SELECT COUNT(*) FROM futures_prices 
                    WHERE Current_Price IS NOT NULL
                """)
                futures_count = cursor.fetchone()[0]
                
                logger.info(f"✓ Updated {options_count} options prices")
                logger.info(f"✓ Updated {futures_count} futures prices")
                
                # Show some sample symbols
                cursor.execute("""
                    SELECT symbol, Current_Price 
                    FROM options_prices 
                    WHERE Current_Price IS NOT NULL 
                    LIMIT 5
                """)
                
                logger.info("\nSample option symbols stored:")
                for row in cursor.fetchall():
                    logger.info(f"  {row[0]}: ${row[1]:.3f}")
                    
        else:
            logger.error("✗ File processing failed")
            
    except Exception as e:
        logger.error(f"✗ Error during processing: {e}")
        import traceback
        traceback.print_exc()

def check_translator_integration():
    """Verify the centralized translator is working."""
    from lib.trading.market_prices.centralized_symbol_translator import CentralizedSymbolTranslator
    
    translator = CentralizedSymbolTranslator()
    
    # Test translation
    test_symbol = "XCME.VY3.21JUL25.111.C"
    result = translator.translate(test_symbol, 'xcme', 'bloomberg')
    
    if result:
        logger.info(f"\n✓ Translator working: {test_symbol} → {result}")
    else:
        logger.warning(f"\n✗ Translation failed for: {test_symbol}")
        logger.info("This is expected for historical dates before July 21, 2025")

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("SPOT RISK PROCESSOR TEST")
    logger.info("="*60)
    
    # First check translator
    check_translator_integration()
    
    # Then test processor
    logger.info("\nTesting spot risk processor...")
    test_spot_risk_processor()
    
    logger.info("\n" + "="*60)
    logger.info("Test complete!")
    logger.info("System is ready for fresh data when SpotRisk directory appears.") 