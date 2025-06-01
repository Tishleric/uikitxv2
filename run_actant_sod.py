#!/usr/bin/env python
"""
Entry point script for running ActantSOD processing.

This script handles Start of Day (SOD) processing for Actant data,
including integration with Pricing Monkey data retrieval.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Import after path setup
    from trading.actant.sod import actant_main
    
    print("Starting ActantSOD processing...")
    # Run the main ActantSOD processing
    # Note: This is a placeholder - actual implementation depends on SOD requirements
    actant_main() 