#!/usr/bin/env python3
"""
Runner script for P&L FIFO/LIFO test simulation
Executes the test as a module to handle relative imports correctly
"""

import subprocess
import sys
import os

# Get the path to the test file
test_path = os.path.join("PNLMODULEFORINTEGRATION", "pnl_system", "test_simulation.py")

# Run as a module to preserve relative imports
print("Running P&L FIFO/LIFO test simulation...")
print("=" * 60)

# Execute as module
result = subprocess.run(
    [sys.executable, "-m", "PNLMODULEFORINTEGRATION.pnl_system.test_simulation"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

sys.exit(result.returncode) 