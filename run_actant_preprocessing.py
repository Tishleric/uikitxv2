#!/usr/bin/env python3
"""
Entry point for Actant Preprocessing Dashboard - Bond Future Options Greek Analysis
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import and run the app
from apps.dashboards.actant_preprocessing.app import app

if __name__ == "__main__":
    print("Starting Actant Preprocessing Dashboard...")
    print("Navigate to http://localhost:8053")
    app.run(debug=True, port=8053, host='0.0.0.0') 