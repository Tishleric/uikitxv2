"""
Verify Test Setup
=================
Check that everything is ready for optimization testing.
"""

from pathlib import Path
import sys


def verify_setup():
    """Verify all required files are in place"""
    
    print("Verifying test setup...")
    print("="*50)
    
    # Check for captured messages
    possible_dirs = [
        Path("tests/diagnostics/tests/diagnostics/captured_messages"),
        Path("tests/diagnostics/captured_messages"),
        Path("captured_messages")
    ]
    
    msg_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            msg_dir = dir_path
            break
    
    if not msg_dir:
        print("✗ No captured messages found!")
        print("  Please run: python tests\\diagnostics\\capture_redis_messages.py")
        return False
    
    pkl_files = list(msg_dir.glob("message_*.pkl"))
    if not pkl_files:
        print("✗ No message files in directory!")
        return False
    
    print(f"✓ Found {len(pkl_files)} captured messages in {msg_dir}")
    
    # Check for test scripts
    test_files = [
        "tests/diagnostics/price_updater_service_optimized.py",
        "tests/diagnostics/test_deduplication_logic.py",
        "tests/diagnostics/test_price_updater_comparison.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✓ {test_file}")
        else:
            print(f"✗ Missing: {test_file}")
            return False
    
    # Check for database
    if Path("trades.db").exists():
        print("✓ trades.db found")
    else:
        print("! Warning: trades.db not found - will create minimal schema")
    
    print("\n✓ All required files present - ready to run tests!")
    return True


if __name__ == "__main__":
    if verify_setup():
        print("\nYou can now run: python tests\\diagnostics\\run_optimization_tests.py")
        sys.exit(0)
    else:
        print("\nPlease fix the issues above before running tests.")
        sys.exit(1)