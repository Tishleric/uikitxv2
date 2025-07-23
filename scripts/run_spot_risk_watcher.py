#!/usr/bin/env python3
"""
Standalone Spot Risk File Watcher

This script runs only the spot risk file watcher which:
1. Watches for spot risk CSV files 
2. Calculates Greeks using bond future option models
3. Stores results in spot_risk.db (tables: spot_risk_sessions, spot_risk_raw, spot_risk_calculated)
4. Updates Current_Price column in market_prices.db options_prices table
5. Generates processed CSV files with Greek calculations

Database tables populated:
- spot_risk.db:
  - spot_risk_sessions: Processing session tracking
  - spot_risk_raw: Raw data from CSV files
  - spot_risk_calculated: Calculated Greeks and model outputs
- market_prices.db:
  - options_prices.Current_Price: Updated with midpoint prices from spot risk files
"""

import sys
import logging
import signal
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global watcher instance
watcher = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal, stopping watcher...")
    if watcher:
        watcher.stop()
    sys.exit(0)

def main():
    """Run the spot risk file watcher."""
    global watcher
    
    print("=" * 60)
    print("SPOT RISK FILE WATCHER")
    print("=" * 60)
    print("\nThis watcher processes spot risk CSV files to:")
    print("  1. Calculate Greeks (delta, gamma, vega, theta, etc.)")
    print("  2. Store results in spot_risk.db")
    print("  3. Update Current_Price in market_prices.db")
    print("  4. Generate processed CSV files")
    print("\nMonitoring directory:")
    print("  - data/input/actant_spot_risk/")
    print("\nOutput:")
    print("  - Database: data/output/spot_risk/spot_risk.db")
    print("  - CSV files: data/output/spot_risk/YYYY-MM-DD/")
    print("  - Market prices: data/output/market_prices/market_prices.db")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create watcher instance
        input_dir = project_root / "data" / "input" / "actant_spot_risk"
        output_dir = project_root / "data" / "output" / "spot_risk"
        
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        # Create directories if they don't exist
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize watcher
    watcher = SpotRiskWatcher(
        input_dir=str(input_dir),
        output_dir=str(output_dir)
    )
    
        # Start monitoring (this will process existing files first)
        logger.info("\nStarting file monitor...")
    watcher.start()
    
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in spot risk watcher: {e}", exc_info=True)
    finally:
        if watcher:
            try:
        watcher.stop()
            except RuntimeError:
                # Observer wasn't started yet
                pass

if __name__ == "__main__":
    main() 