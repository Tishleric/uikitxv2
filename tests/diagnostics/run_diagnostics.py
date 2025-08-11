#!/usr/bin/env python
"""
Interactive diagnostic runner for price updater latency investigation
"""

import subprocess
import sys
import time
from pathlib import Path

def run_diagnostic(script_name, description):
    """Run a diagnostic script and display results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print('='*60)
    
    script_path = Path(__file__).parent / script_name
    result = subprocess.run([sys.executable, str(script_path)], 
                          capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\nWarning: {script_name} exited with code {result.returncode}")
    
    print(f"\nCompleted: {description}")
    input("\nPress Enter to continue...")

def main():
    """Run all diagnostics in sequence"""
    print("""
====================================
Price Updater Diagnostic Suite
====================================

This will run three diagnostic tests to identify the source
of the 14-second latency in the price updater pipeline.
""")
    
    tests = [
        ("test_database_bottleneck.py", 
         "Database Bottleneck Test - Check if DB operations are slow"),
        
        ("monitor_price_pipeline.py", 
         "Live Pipeline Monitor - Watch real-time message flow (30 seconds)"),
        
        ("price_updater_diagnostic.py", 
         "Full Pipeline Simulation - Time each processing step")
    ]
    
    print(f"Will run {len(tests)} diagnostic tests.")
    input("Press Enter to start...")
    
    for i, (script, description) in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] {description}")
        
        if script == "monitor_price_pipeline.py":
            # Run with specific arguments
            print("\nThis will monitor for 30 seconds...")
            subprocess.run([
                sys.executable, 
                str(Path(__file__).parent / script),
                "--duration", "30",
                "--db-monitor"
            ])
        else:
            run_diagnostic(script, description)
    
    print("""
====================================
Diagnostic Suite Complete!
====================================

Key things to look for in the results:

1. Database Test:
   - Single update time > 1 second indicates DB bottleneck
   - WAL mode disabled = potential lock contention
   - High concurrent lock count = contention issue

2. Pipeline Monitor:
   - Growing latency over time = processing bottleneck
   - Consistent high latency = systemic issue
   - Database locks = write contention

3. Full Simulation:
   - Which operation takes longest?
   - Is it DB commits, symbol translation, or serialization?

Please share the output logs for analysis.
""")

if __name__ == "__main__":
    main()