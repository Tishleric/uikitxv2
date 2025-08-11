"""
Run Critical Pre-Production Tests
=================================
Minimal test suite for production readiness.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run critical tests only"""
    
    print("""
========================================
CRITICAL PRE-PRODUCTION TESTS
========================================

Running minimal test suite...
""")
    
    # Change to project root
    import os
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    tests = [
        ("Edge Cases", "python tests/diagnostics/test_edge_cases.py"),
        ("Live Redis", "python tests/diagnostics/test_live_redis.py --timeout 5"),
    ]
    
    failed = False
    
    for name, cmd in tests:
        print(f"\n{'='*40}")
        print(f"Running: {name}")
        print('='*40)
        
        result = subprocess.run(cmd.split(), capture_output=False)
        
        if result.returncode != 0:
            print(f"\n✗ {name} failed")
            failed = True
        else:
            print(f"\n✓ {name} passed")
    
    print("\n" + "="*40)
    if not failed:
        print("ALL CRITICAL TESTS PASSED ✓")
        print("\nReady for production deployment.")
        print("See PRODUCTION_ROLLBACK_PLAN.md for deployment steps.")
    else:
        print("TESTS FAILED ✗")
        print("Fix issues before deploying.")
    print("="*40)
    
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())