#!/usr/bin/env python3
"""
Corrected market price monitor that watches Z:\Trade_Control directories.

This script monitors the correct directories for market price files:
- Z:\Trade_Control\Futures
- Z:\Trade_Control\Options
- Z:\Trade_Control\SpotRisk

Files are processed based on their timestamps:
- Spot Risk files: Update Current_Price (from Actant spot risk analysis)
- 2:00 PM files: Update Flash_Close (current prices)
- 4:00 PM files: Update prior_close (settlement prices for next day)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import signal
import logging
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Import the processors and storage directly
from lib.trading.market_prices import (
    MarketPriceStorage, 
    FuturesProcessor, 
    OptionsProcessor,
    SpotRiskPriceProcessor,
    PriceUpdateTrigger
)
from lib.trading.market_prices.file_monitor import MarketPriceFileHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for the observer
observer = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping monitor...")
    if observer:
        observer.stop()
    sys.exit(0)

def process_existing_files():
    """Process any existing files in the Trade_Control directories."""
    storage = MarketPriceStorage()
    futures_processor = FuturesProcessor(storage)
    options_processor = OptionsProcessor(storage)
    spot_risk_processor = SpotRiskPriceProcessor(storage)
    
    # Process existing futures files
    futures_dir = Path(r"Z:\Trade_Control\Futures")
    if futures_dir.exists():
        futures_files = list(futures_dir.glob("Futures_*.csv"))
        logger.info(f"Found {len(futures_files)} existing futures files")
        
        for filepath in sorted(futures_files):
            logger.info(f"Processing existing futures file: {filepath.name}")
            try:
                futures_processor.process_file(filepath)
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
    
    # Process existing options files
    options_dir = Path(r"Z:\Trade_Control\Options")
    if options_dir.exists():
        options_files = list(options_dir.glob("Options_*.csv"))
        logger.info(f"Found {len(options_files)} existing options files")
        
        for filepath in sorted(options_files):
            logger.info(f"Processing existing options file: {filepath.name}")
            try:
                options_processor.process_file(filepath)
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
    
    # Process existing spot risk files
    spot_risk_dir = Path("data/input/actant_spot_risk")
    if spot_risk_dir.exists():
        # Get all CSV files from daily subdirectories
        spot_risk_files = list(spot_risk_dir.rglob("bav_analysis_*.csv"))
        logger.info(f"Found {len(spot_risk_files)} existing spot risk files")
        
        # Only process recent ones to avoid historical symbol issues
        for filepath in sorted(spot_risk_files)[-5:]:  # Last 5 files
            logger.info(f"Processing existing spot risk file: {filepath.name}")
            try:
                spot_risk_processor.process_file(filepath)
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")

def main():
    """Main entry point."""
    global observer
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Market price file monitor')
    parser.add_argument('--enable-tyu5', action='store_true', 
                        help='Enable automatic TYU5 P&L calculation on price updates')
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("CORRECTED MARKET PRICE FILE MONITOR")
    logger.info("="*60)
    logger.info("Monitoring directories:")
    logger.info("  - Z:\\Trade_Control\\Futures")
    logger.info("  - Z:\\Trade_Control\\Options")
    logger.info("  - data\\input\\actant_spot_risk (recursive)")
    logger.info("")
    logger.info("Processing windows:")
    logger.info("  - Spot Risk: Updates Current_Price (continuous)")
    logger.info("  - 2:00 PM CDT: Updates Flash_Close (current prices)")
    logger.info("  - 4:00 PM CDT: Updates prior_close (settlement prices)")
    logger.info("  - 3:00 PM files are ignored")
    logger.info("")
    logger.info(f"TYU5 P&L auto-calculation: {'ENABLED' if args.enable_tyu5 else 'DISABLED'}")
    logger.info("Press Ctrl+C to stop...")
    logger.info("="*60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # First process any existing files
    logger.info("\nProcessing existing files...")
    process_existing_files()
    logger.info("Done processing existing files.\n")
    
    # Create storage and handlers
    storage = MarketPriceStorage()
    flash_prior_handler = MarketPriceFileHandler(storage)
    
    # Import spot risk handler
    from lib.trading.market_prices.spot_risk_file_handler import SpotRiskFileHandler
    spot_risk_handler = SpotRiskFileHandler(storage)
    
    # Set up observer for the correct directories
    observer = Observer()
    futures_dir = Path(r"Z:\Trade_Control\Futures")
    options_dir = Path(r"Z:\Trade_Control\Options")
    spot_risk_dir = Path("data/input/actant_spot_risk")
    
    # Make sure directories exist
    if not futures_dir.exists():
        logger.warning(f"Futures directory does not exist: {futures_dir}")
    else:
        observer.schedule(flash_prior_handler, str(futures_dir), recursive=False)
        logger.info(f"Watching futures directory: {futures_dir}")
    
    if not options_dir.exists():
        logger.warning(f"Options directory does not exist: {options_dir}")
    else:
        observer.schedule(flash_prior_handler, str(options_dir), recursive=False)
        logger.info(f"Watching options directory: {options_dir}")
    
    if not spot_risk_dir.exists():
        logger.warning(f"Spot risk directory does not exist: {spot_risk_dir}")
    else:
        observer.schedule(spot_risk_handler, str(spot_risk_dir), recursive=True)
        logger.info(f"Watching spot risk directory (recursively): {spot_risk_dir}")
    
    # Create price update trigger for TYU5 calculations if enabled
    if args.enable_tyu5:
        logger.info("Initializing TYU5 price update trigger...")
        price_trigger = PriceUpdateTrigger(check_interval=30)  # Check every 30 seconds
        price_trigger.start()
    else:
        price_trigger = None
    
    # Start observer
    observer.start()
    logger.info("\nFile monitor started. Waiting for new files...")
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)  # Sleep for 1 minute
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("\nShutting down monitor...")
        if price_trigger:
            price_trigger.stop()
        observer.stop()
        observer.join()
        logger.info("Monitor stopped.")

if __name__ == "__main__":
    main() 