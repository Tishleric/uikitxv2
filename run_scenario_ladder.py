#!/usr/bin/env python
"""
Entry point script for running Scenario Ladder dashboard.

This script runs the ladder visualization tool for analyzing 
price scenarios and P&L calculations.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Change to the app directory so relative paths work
    os.chdir(os.path.join(project_root, "apps", "dashboards", "ladder"))
    
    # Import and run the app
    from apps.dashboards.ladder.scenario_ladder import app
    
    print("Starting Scenario Ladder Dashboard...")
    app.run(debug=True, host="127.0.0.1", port=8051) 