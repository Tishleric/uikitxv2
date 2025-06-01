#!/usr/bin/env python3
"""
Convenience script to run the ActantEOD dashboard.

This provides an easy entry point to start the dashboard from the project root.
"""

import sys
from pathlib import Path

# Add project root to Python path to ensure imports work
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the dashboard app
from apps.dashboards.actant_eod.app import app

if __name__ == "__main__":
    print("Starting ActantEOD Dashboard...")
    print("Navigate to http://127.0.0.1:8050/ in your browser")
    app.run(debug=True, port=8050) 