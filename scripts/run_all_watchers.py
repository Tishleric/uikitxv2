#!/usr/bin/env python3
"""
Unified Watcher Service - Runs all file watchers for the trading system.

This script starts and manages four watchers:
1. Market Price File Monitor - Monitors futures/options price files (2pm/4pm)
2. Spot Risk Watcher - Processes spot risk files and updates current prices
3. PNL Pipeline Watcher - Monitors for changes to trigger TYU5 calculations
4. EOD P&L Monitor - Monitors for 4pm settlement prices and calculates EOD snapshots
"""

import sys
import os
import signal
import logging
import threading
import time
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the watchers
from lib.trading.market_prices import MarketPriceFileMonitor
from lib.trading.actant.spot_risk.file_watcher import SpotRiskWatcher
from lib.trading.pnl_integration.pnl_pipeline_watcher import PNLPipelineWatcher
from lib.trading.pnl_integration.eod_snapshot_service import EODSnapshotService
from lib.trading.pnl_integration.lot_snapshot_service import LotSnapshotService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for watchers
market_price_monitor = None
spot_risk_watcher = None
pnl_pipeline_watcher = None
eod_monitor = None
lot_snapshot_monitor = None
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping all watchers...")
    shutdown_event.set()
    
    # Stop all watchers
    if market_price_monitor:
        try:
            market_price_monitor.stop()
            logger.info("Market Price Monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping Market Price Monitor: {e}")
    
    if spot_risk_watcher:
        try:
            spot_risk_watcher.stop()
            logger.info("Spot Risk Watcher stopped")
        except Exception as e:
            logger.error(f"Error stopping Spot Risk Watcher: {e}")
    
    if pnl_pipeline_watcher:
        try:
            pnl_pipeline_watcher.stop()
            logger.info("PNL Pipeline Watcher stopped")
        except Exception as e:
            logger.error(f"Error stopping PNL Pipeline Watcher: {e}")
    
    if eod_monitor:
        try:
            eod_monitor.stop_monitoring()
            logger.info("EOD P&L Monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping EOD P&L Monitor: {e}")
    
    sys.exit(0)


def run_market_price_monitor():
    """Run the market price file monitor in a thread."""
    global market_price_monitor
    
    try:
        logger.info("Starting Market Price File Monitor...")
        market_price_monitor = MarketPriceFileMonitor()
        
        # Add callbacks for logging
        def futures_callback(filepath, result):
            if result:
                logger.info(f"✓ Processed futures file: {filepath.name}")
            else:
                logger.warning(f"✗ Failed to process futures file: {filepath.name}")
        
        def options_callback(filepath, result):
            if result:
                logger.info(f"✓ Processed options file: {filepath.name}")
            else:
                logger.warning(f"✗ Failed to process options file: {filepath.name}")
        
        market_price_monitor.futures_callback = futures_callback
        market_price_monitor.options_callback = options_callback
        
        market_price_monitor.start()
        logger.info("Market Price File Monitor started successfully")
        
        # Keep thread alive
        while not shutdown_event.is_set():
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in Market Price Monitor: {e}", exc_info=True)


def run_spot_risk_watcher():
    """Run the spot risk watcher in a thread."""
    global spot_risk_watcher
    
    try:
        logger.info("Starting Spot Risk Watcher...")
        
        # Use the same directories as the standalone script
        input_dir = Path("data/input/actant_spot_risk")
        output_dir = Path("data/output/spot_risk")
        
        spot_risk_watcher = SpotRiskWatcher(str(input_dir), str(output_dir))
        spot_risk_watcher.start()
        logger.info("Spot Risk Watcher started successfully")
        
        # Keep thread alive
        while not shutdown_event.is_set():
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in Spot Risk Watcher: {e}", exc_info=True)


def run_pnl_pipeline_watcher():
    """Run the PNL pipeline watcher in a thread."""
    global pnl_pipeline_watcher
    
    try:
        logger.info("Starting PNL Pipeline Watcher...")
        pnl_pipeline_watcher = PNLPipelineWatcher()
        pnl_pipeline_watcher.start()
        logger.info("PNL Pipeline Watcher started successfully")
        
        # Keep thread alive
        while not shutdown_event.is_set():
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in PNL Pipeline Watcher: {e}", exc_info=True)


def run_eod_monitor():
    """Run the EOD P&L monitor in a thread."""
    global eod_monitor
    
    try:
        logger.info("Starting EOD P&L Monitor...")
        eod_monitor = EODSnapshotService()
        
        # Create async event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the monitor (3pm-6pm window, 60 second checks)
        loop.run_until_complete(
            eod_monitor.monitor_for_eod(check_interval=60)
        )
        
    except Exception as e:
        logger.error(f"Error in EOD P&L Monitor: {e}", exc_info=True)


def run_lot_snapshot_monitor():
    """Run the 2pm lot snapshot monitor in a thread."""
    global lot_snapshot_monitor
    
    try:
        logger.info("Starting 2PM Lot Snapshot Monitor...")
        lot_snapshot_monitor = LotSnapshotService()
        
        # Simple monitoring loop that checks every minute
        while not shutdown_event.is_set():
            try:
                # Check if 2pm snapshot is needed
                if lot_snapshot_monitor.is_2pm_snapshot_needed():
                    logger.info("2PM snapshot needed - capturing...")
                    counts = lot_snapshot_monitor.capture_snapshot()
                    logger.info(f"Captured snapshots for {len(counts)} symbols")
                    
            except Exception as e:
                logger.error(f"Error capturing 2PM snapshot: {e}")
            
            # Wait 60 seconds before next check
            for _ in range(60):
                if shutdown_event.is_set():
                    break
                time.sleep(1)
                
    except Exception as e:
        logger.error(f"Error in 2PM Lot Snapshot Monitor: {e}", exc_info=True)


def main():
    """Main entry point."""
    logger.info("="*80)
    logger.info("UNIFIED WATCHER SERVICE")
    logger.info("="*80)
    logger.info("Starting all file watchers:")
    logger.info("  1. Market Price File Monitor - Monitors futures/options price files")
    logger.info("  2. Spot Risk Watcher - Processes spot risk files and updates prices")
    logger.info("  3. PNL Pipeline Watcher - Monitors for TYU5 pipeline triggers")
    logger.info("  4. EOD P&L Monitor - Calculates EOD snapshots at 4pm")
    logger.info("  5. Lot Snapshot Monitor - Captures open lot snapshots at 2pm")
    logger.info("")
    logger.info("Press Ctrl+C to stop all watchers...")
    logger.info("="*80)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create threads for each watcher
    threads = []
    
    # Market Price Monitor thread
    market_thread = threading.Thread(
        target=run_market_price_monitor,
        name="MarketPriceMonitor",
        daemon=False
    )
    threads.append(market_thread)
    
    # Spot Risk Watcher thread
    spot_risk_thread = threading.Thread(
        target=run_spot_risk_watcher,
        name="SpotRiskWatcher",
        daemon=False
    )
    threads.append(spot_risk_thread)
    
    # PNL Pipeline Watcher thread
    pnl_thread = threading.Thread(
        target=run_pnl_pipeline_watcher,
        name="PNLPipelineWatcher",
        daemon=False
    )
    threads.append(pnl_thread)
    
    # EOD P&L Monitor thread
    eod_thread = threading.Thread(
        target=run_eod_monitor,
        name="EODMonitor",
        daemon=False
    )
    threads.append(eod_thread)
    
    # Lot Snapshot Monitor thread
    snapshot_thread = threading.Thread(
        target=run_lot_snapshot_monitor,
        name="LotSnapshotMonitor",
        daemon=False
    )
    threads.append(snapshot_thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
        logger.info(f"Started thread: {thread.name}")
        time.sleep(2)  # Small delay between starts to avoid conflicts
    
    logger.info("\nAll watchers started successfully!")
    logger.info("="*80)
    
    try:
        # Keep main thread alive and monitor threads
        while not shutdown_event.is_set():
            # Check if any thread died unexpectedly
            for thread in threads:
                if not thread.is_alive():
                    logger.error(f"Thread {thread.name} died unexpectedly!")
                    shutdown_event.set()
                    break
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
    finally:
        # Signal all threads to stop
        shutdown_event.set()
        
        # Wait for all threads to finish
        logger.info("Waiting for all threads to finish...")
        for thread in threads:
            thread.join(timeout=10)
            if thread.is_alive():
                logger.warning(f"Thread {thread.name} did not stop cleanly")
        
        logger.info("All watchers stopped.")


if __name__ == "__main__":
    main() 