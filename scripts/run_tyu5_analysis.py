#!/usr/bin/env python
"""Run TYU5 P&L Analysis

This script uses the TYU5 integration adapter to fetch data from UIKitXv2
database and run the TYU5 P&L calculation engine.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_integration import TYU5Service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run TYU5 analysis."""
    try:
        # Create TYU5 service
        logger.info("Initializing TYU5 service...")
        service = TYU5Service()
        
        # Run the analysis for all dates
        logger.info("Running TYU5 P&L analysis...")
        output_file = service.calculate_pnl(
            trade_date=None,  # Process all dates
            output_format="excel"
        )
        
        if output_file:
            logger.info(f"✅ Analysis complete! Excel file saved to: {output_file}")
            
            # Print summary
            logger.info("\nPrinting calculation summary:")
            service.print_summary()
            
        else:
            logger.error("Analysis failed - no output file generated")
        
    except Exception as e:
        logger.error(f"Error running TYU5 analysis: {e}")
        raise


if __name__ == "__main__":
    main() 