#!/usr/bin/env python3
"""
Runner script for integrated P&L FIFO/LIFO test
"""

import subprocess
import sys
import os

print("Running integrated P&L FIFO/LIFO test simulation...")
print("=" * 60)

# Execute as module to handle relative imports
result = subprocess.run(
    [sys.executable, "-m", "lib.trading.pnl_fifo_lifo.test_simulation"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

sys.exit(result.returncode) 