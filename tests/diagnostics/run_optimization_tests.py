"""
Run Price Updater Optimization Tests
====================================
Execute all optimization tests in sequence.
"""

import subprocess
import sys
from pathlib import Path


def run_test(script_name, description):
    """Run a test script and check results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print('='*60)
    
    script_path = Path(__file__).parent / script_name
    result = subprocess.run([sys.executable, str(script_path)], 
                          capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n✗ {script_name} failed with code {result.returncode}")
        return False
    
    print(f"\n✓ {description} completed successfully")
    return True


def main():
    """Run all optimization tests"""
    
    # Change to project root directory to ensure all relative paths work
    import os
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
    
    print("""
====================================
Price Updater Optimization Testing
====================================

This will test the optimized implementation against the current one.
NO PRODUCTION FILES WILL BE MODIFIED.
""")
    
    tests = [
        ("test_deduplication_logic.py", "Deduplication Logic Tests"),
        ("test_price_updater_comparison.py", "Full Comparison Test"),
    ]
    
    print(f"\nWill run {len(tests)} test suites.")
    input("Press Enter to start...")
    
    all_passed = True
    
    for script, description in tests:
        if not run_test(script, description):
            all_passed = False
            print("\nStopping due to test failure.")
            break
    
    if all_passed:
        print("""

====================================
ALL TESTS PASSED! ✓
====================================

RESULTS SUMMARY:
1. Deduplication working correctly
2. Optimized version produces IDENTICAL prices
3. Significant performance improvement achieved

The optimized implementation is ready for production deployment.
""")
    else:
        print("""

====================================
TESTS FAILED ✗
====================================

Please check the error messages above.
""")


if __name__ == "__main__":
    main()