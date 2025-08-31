#!/usr/bin/env python
"""Run the Spot Risk Price-Only publisher sidecar.

This watcher publishes all futures and options prices (key, bid, ask, adjtheor)
from the Actant spot risk CSV chunks to the Redis channel 'spot_risk:prices_full'.
"""

import logging
import os
import signal
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.trading.actant.spot_risk_prices_full.watcher import PriceOnlyWatcher


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

INPUT_DIR = "data/input/actant_spot_risk"


def main():
    print("=" * 60)
    print("Spot Risk Price-Only Publisher (sidecar)")
    print("=" * 60)
    print(f"Monitoring: {INPUT_DIR}")
    print("Publishing to channel: spot_risk:prices_full")
    print("\nPress Ctrl+C to stop\n")

    num_workers = max(1, (os.cpu_count() or 1) - 4)
    watcher = PriceOnlyWatcher(input_dir=INPUT_DIR, num_workers=num_workers)

    def handle_sigint(signum, frame):
        print("\nShutting down...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    watcher.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_sigint(None, None)


if __name__ == "__main__":
    main()

