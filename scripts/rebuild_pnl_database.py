#!/usr/bin/env python
"""Rebuild P&L Database

This script drops and recreates all P&L tracking tables, then reprocesses all trade files.
WARNING: This will delete all existing P&L data!

Usage:
    python scripts/rebuild_pnl_database.py
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.controller import PnLController

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to rebuild the P&L database."""
    logger.warning("=" * 80)
    logger.warning("WARNING: This will DELETE ALL P&L DATA and rebuild from CSV files!")
    logger.warning("=" * 80)
    
    response = input("\nAre you sure you want to continue? Type 'YES' to proceed: ")
    
    if response != 'YES':
        logger.info("Database rebuild cancelled.")
        return
    
    logger.info("Starting database rebuild...")
    
    try:
        # Create controller
        controller = PnLController()
        
        # Rebuild database
        controller.rebuild_database()
        
        logger.info("Database rebuild completed successfully!")
        logger.info("All trade files have been reprocessed.")
        
    except Exception as e:
        logger.error(f"Error during database rebuild: {e}")
        raise


if __name__ == "__main__":
    main() 