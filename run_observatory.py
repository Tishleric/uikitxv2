#!/usr/bin/env python
"""Run the Observatory Dashboard"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.dashboards.observatory.app import app
from lib.monitoring.decorators.monitor import start_observatory_writer


if __name__ == '__main__':
    print("🔭 Starting Observatory Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8052")
    print("📁 Using database: logs/observatory.db")
    print("")
    
    # Start the observatory writer
    writer = start_observatory_writer()
    print("✅ Observatory writer started")
    print("")
    
    # Run the app
    app.run(debug=True, port=8052) 