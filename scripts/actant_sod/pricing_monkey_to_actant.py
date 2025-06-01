#!/usr/bin/env python3
"""
Pricing Monkey to Actant Integration Script

This script automates the complete pipeline:
1. Retrieves data from Pricing Monkey via browser automation
2. Transforms the data into actant.py compatible format  
3. Processes through actant.py logic
4. Outputs SOD format CSV
"""

import logging
import datetime
from pathlib import Path

from trading.actant.sod import (
    BrowserAutomator,
    extract_trade_data_from_pm, 
    process_trades
)
from trading.actant.sod.browser_automation import get_simple_data, PMSimpleRetrievalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main integration function that orchestrates the complete pipeline.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=== Starting Pricing Monkey to Actant Integration ===")
        
        # Step 1: Retrieve data from Pricing Monkey
        logger.info("Step 1: Retrieving data from Pricing Monkey...")
        pm_df = get_simple_data()
        
        if pm_df.empty:
            logger.error("No data retrieved from Pricing Monkey")
            return False
        
        logger.info(f"Retrieved {len(pm_df)} rows from Pricing Monkey")
        logger.debug("Pricing Monkey data preview:")
        logger.debug(f"\n{pm_df.head().to_string()}")
        
        # Step 2: Transform data using adapter
        logger.info("Step 2: Transforming data for actant processing...")
        
        # Extract trade data with Strike and Price
        trade_data = extract_trade_data_from_pm(pm_df)
        if not trade_data:
            logger.error("No valid trade data extracted from Pricing Monkey")
            return False
        
        logger.info(f"Extracted {len(trade_data)} trades with direct Strike and Price values")
        logger.debug(f"Trade data: {trade_data}")
        
        # Step 3: Process through actant logic
        logger.info("Step 3: Processing through actant logic...")
        processed_df = process_trades(trade_data)
        
        if processed_df.empty:
            logger.error("No data produced by actant processing")
            return False
        
        logger.info(f"Processed {len(processed_df)} rows through actant logic")
        logger.debug("Processed data preview:")
        logger.debug(f"\n{processed_df.head().to_string()}")
        
        # Step 4: Save to CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # FIXED: Use script directory instead of current working directory
        script_dir = Path(__file__).parent
        output_filename = script_dir / "outputs" / f"pricing_monkey_sod_{timestamp}.csv"
        
        # Additional output location
        additional_output_path = Path("Z:/SOD - Shortcut.lnk").parent / f"pricing_monkey_sod_{timestamp}.csv"
        
        # Ensure outputs directory exists
        output_filename.parent.mkdir(exist_ok=True)
        
        # Drop description column for final CSV (following actant.py behavior)
        final_df = processed_df.drop(columns=["DESCRIPTION"], errors='ignore')
        
        # Save to primary location
        final_df.to_csv(output_filename, index=False)
        logger.info(f"Step 4a: Successfully saved SOD CSV to {output_filename}")
        
        # Save to additional location
        try:
            # Check if the directory exists first
            if additional_output_path.parent.exists():
                final_df.to_csv(additional_output_path, index=False)
                logger.info(f"Step 4b: ✅ Successfully saved SOD CSV to additional location: {additional_output_path}")
                logger.info(f"Additional location file size: {additional_output_path.stat().st_size} bytes")
            else:
                logger.warning(f"Step 4b: ❌ Additional output directory does not exist: {additional_output_path.parent}")
        except PermissionError as e:
            logger.error(f"Step 4b: ❌ Permission denied saving to {additional_output_path}: {e}")
        except FileNotFoundError as e:
            logger.error(f"Step 4b: ❌ Path not found for additional location {additional_output_path}: {e}")
        except Exception as e:
            logger.error(f"Step 4b: ❌ Unexpected error saving to additional location {additional_output_path}: {e}")
        
        logger.info(f"Final CSV contains {len(final_df)} rows with {len(final_df.columns)} columns")
        
        # Show summary
        print("\n=== INTEGRATION SUMMARY ===")
        print(f"Pricing Monkey rows processed: {len(pm_df)}")
        print(f"Trade data extracted: {len(trade_data)}")
        print(f"Final SOD rows generated: {len(final_df)}")
        print(f"Output file: {output_filename}")
        
        print("\n=== First 5 rows of final output ===")
        print(final_df.head().to_string(index=False))
        
        logger.info("=== Integration completed successfully ===")
        return True
        
    except PMSimpleRetrievalError as e:
        logger.error(f"Pricing Monkey retrieval failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during integration: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 