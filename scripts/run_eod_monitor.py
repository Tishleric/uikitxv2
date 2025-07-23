#!/usr/bin/env python3
"""
EOD P&L Monitor Script

This script monitors for 4pm market price updates and triggers
EOD P&L calculations with settlement-aware logic.

IMPORTANT: P&L days run from 2pm to 2pm (settlement to settlement).
At 4pm, we calculate P&L for the period that ENDED at 2pm today.

It can run standalone or as part of the unified watcher service.
"""

import sys
import asyncio
import signal
import logging
from pathlib import Path
from datetime import datetime, time, timedelta
import pytz
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_integration.eod_snapshot_service import EODSnapshotService
from lib.trading.pnl_integration.settlement_constants import (
    CHICAGO_TZ, EOD_TIME, format_pnl_period
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance for signal handling
eod_service = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping EOD monitor...")
    if eod_service:
        eod_service.stop_monitoring()
    sys.exit(0)


async def run_eod_monitor(check_interval: int = 60, 
                         start_hour: int = 15,
                         end_hour: int = 18):
    """
    Run the EOD monitor with configurable parameters.
    
    Args:
        check_interval: Seconds between checks
        start_hour: Hour to start monitoring (24-hour, Chicago time)
        end_hour: Hour to stop monitoring (24-hour, Chicago time)
    """
    global eod_service
    
    logger.info("=" * 80)
    logger.info("EOD P&L MONITOR SERVICE")
    logger.info("=" * 80)
    logger.info(f"Check interval: {check_interval} seconds")
    logger.info(f"Monitoring window: {start_hour}:00 - {end_hour}:00 Chicago time")
    logger.info("")
    logger.info("P&L PERIOD DEFINITION:")
    logger.info("- P&L days run from 2pm to 2pm (settlement to settlement)")
    logger.info("- At 4pm, we calculate P&L for the period that ENDED at 2pm")
    logger.info("- Example: At 4pm Tuesday, we calculate Monday 2pm to Tuesday 2pm")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Create service
    eod_service = EODSnapshotService()
    
    # Check if we're within monitoring window
    while True:
        current_time = datetime.now(CHICAGO_TZ)
        current_hour = current_time.hour
        
        if start_hour <= current_hour < end_hour:
            logger.info(f"Within monitoring window - starting EOD monitor")
            
            # Log what P&L period would be calculated if triggered now
            today = current_time.date()
            logger.info(f"If triggered now, would calculate P&L for: {format_pnl_period(today)}")
            
            # Run monitoring
            await eod_service.monitor_for_eod(check_interval=check_interval)
            
        else:
            # Outside monitoring window
            logger.info(f"Outside monitoring window (current hour: {current_hour}). "
                      f"Waiting until {start_hour}:00...")
            
            # Calculate time to next window
            if current_hour >= end_hour:
                # Wait until tomorrow's start time
                tomorrow = current_time.date() + timedelta(days=1)
                next_start = CHICAGO_TZ.localize(
                    datetime.combine(tomorrow, time(start_hour, 0))
                )
            else:
                # Wait until today's start time
                next_start = CHICAGO_TZ.localize(
                    datetime.combine(current_time.date(), time(start_hour, 0))
                )
            
            wait_seconds = (next_start - current_time).total_seconds()
            logger.info(f"Sleeping for {wait_seconds/3600:.1f} hours until {next_start}")
            
            await asyncio.sleep(wait_seconds)


async def run_manual_eod(trade_date: Optional[str] = None):
    """
    Manually trigger EOD calculation for a specific date.
    
    Args:
        trade_date: Date string in YYYY-MM-DD format (defaults to today)
                   This is the P&L date - the period ENDS at 2pm on this date
    """
    logger.info("Running manual EOD calculation...")
    
    service = EODSnapshotService()
    
    if trade_date:
        pnl_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
    else:
        pnl_date = datetime.now(CHICAGO_TZ).date()
    
    logger.info(f"P&L Date: {pnl_date}")
    logger.info(f"P&L Period: {format_pnl_period(pnl_date)}")
    logger.info("(Period ended at 2pm on the P&L date)")
    
    success = await service.trigger_eod_snapshot(pnl_date)
    
    if success:
        logger.info("✓ EOD calculation completed successfully")
    else:
        logger.error("✗ EOD calculation failed")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="EOD P&L Monitor - Calculates P&L for 2pm-to-2pm periods",
        epilog="P&L days run from 2pm to 2pm. At 4pm, we calculate for the period ending at 2pm today."
    )
    parser.add_argument(
        "--manual", 
        action="store_true", 
        help="Run manual EOD calculation instead of monitoring"
    )
    parser.add_argument(
        "--date", 
        help="P&L date for manual calculation (YYYY-MM-DD). Period ENDS at 2pm on this date."
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=15,
        help="Start monitoring hour in Chicago time (default: 15 = 3pm)"
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=18,
        help="End monitoring hour in Chicago time (default: 18 = 6pm)"
    )
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.manual:
            # Run manual calculation
            asyncio.run(run_manual_eod(args.date))
        else:
            # Run monitoring service
            asyncio.run(run_eod_monitor(
                check_interval=args.interval,
                start_hour=args.start_hour,
                end_hour=args.end_hour
            ))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 