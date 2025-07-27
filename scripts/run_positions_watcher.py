#!/usr/bin/env python
"""
Run Positions Watcher

Purpose: Monitor trades.db and spot_risk.db for changes and update POSITIONS table
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_fifo_lifo.positions_watcher import PositionsWatcher
import logging

def main():
    """Run positions watcher with default settings."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create watcher with default paths
    watcher = PositionsWatcher()
    
    print("Starting Positions Watcher...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        watcher.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main() 