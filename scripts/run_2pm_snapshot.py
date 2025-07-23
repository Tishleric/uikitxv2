#!/usr/bin/env python3
"""
2PM Lot Snapshot Service

Captures snapshots of open lots at 2pm CDT daily for P&L period tracking.
Can be run manually or scheduled via cron/task scheduler.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, time
import pytz
import asyncio
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from lib.trading.pnl_integration.lot_snapshot_service import LotSnapshotService
from lib.trading.pnl_integration.settlement_constants import CHICAGO_TZ

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/2pm_snapshot.log')
    ]
)
logger = logging.getLogger(__name__)


def is_business_day(dt: datetime) -> bool:
    """Check if given datetime is a business day (Mon-Fri)."""
    return dt.weekday() < 5  # Monday = 0, Friday = 4


async def monitor_2pm_snapshot(check_interval: int = 60):
    """
    Monitor for 2pm and capture snapshot when needed.
    
    Args:
        check_interval: Seconds between checks
    """
    service = LotSnapshotService()
    
    logger.info("Starting 2PM snapshot monitor")
    
    while True:
        try:
            now = datetime.now(CHICAGO_TZ)
            
            # Check if it's a business day
            if not is_business_day(now):
                logger.debug(f"Weekend - skipping snapshot check")
                await asyncio.sleep(check_interval)
                continue
            
            # Check if we need a 2pm snapshot
            if service.is_2pm_snapshot_needed():
                logger.info("2PM snapshot needed - capturing...")
                counts = service.capture_snapshot(now)
                logger.info(f"Captured snapshots for {len(counts)} symbols")
                for symbol, count in counts.items():
                    logger.info(f"  {symbol}: {count} lots")
            else:
                logger.debug("No 2PM snapshot needed at this time")
            
        except Exception as e:
            logger.error(f"Error in 2PM monitor: {e}")
        
        await asyncio.sleep(check_interval)


def capture_manual_snapshot(snapshot_date: str = None):
    """
    Manually capture a snapshot for a specific date/time.
    
    Args:
        snapshot_date: Date string in YYYY-MM-DD format (default: today)
    """
    service = LotSnapshotService()
    
    if snapshot_date:
        # Parse date and set to 2pm CDT
        dt = datetime.strptime(snapshot_date, "%Y-%m-%d")
        dt = CHICAGO_TZ.localize(dt.replace(hour=14, minute=0, second=0))
    else:
        dt = datetime.now(CHICAGO_TZ).replace(hour=14, minute=0, second=0)
    
    logger.info(f"Capturing manual snapshot for {dt}")
    
    try:
        counts = service.capture_snapshot(dt)
        logger.info(f"Successfully captured snapshots for {len(counts)} symbols")
        for symbol, count in counts.items():
            logger.info(f"  {symbol}: {count} lots")
    except Exception as e:
        logger.error(f"Error capturing snapshot: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='2PM Lot Snapshot Service')
    parser.add_argument('--monitor', action='store_true',
                       help='Run continuous monitoring (default: one-time capture)')
    parser.add_argument('--date', type=str,
                       help='Capture snapshot for specific date (YYYY-MM-DD)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Check interval in seconds for monitor mode (default: 60)')
    
    args = parser.parse_args()
    
    if args.monitor:
        logger.info("Starting 2PM snapshot monitor service")
        asyncio.run(monitor_2pm_snapshot(args.interval))
    else:
        # One-time capture
        success = capture_manual_snapshot(args.date)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 