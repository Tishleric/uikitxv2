"""
Test script to diagnose volatility comparison tool issues
Run this to check each component individually
"""

import sys
import os
import subprocess
import traceback

def test_python_version():
    """Test Python version"""
    print("\n" + "="*50)
    print("TESTING PYTHON VERSION")
    print("="*50)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print("ERROR: Python 3.8+ required")
        return False
    
    print("OK: Python version is compatible")
    return True


def test_imports():
    """Test all required imports"""
    print("\n" + "="*50)
    print("TESTING IMPORTS")
    print("="*50)
    
    required_packages = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('scipy', 'scipy'),
        ('pyperclip', 'pyperclip'),
        ('pywinauto', 'pywinauto'),
        ('datetime', 'datetime'),
        ('json', 'json'),
        ('re', 're'),
        ('typing', 'typing')
    ]
    
    failed = []
    
    for package, alias in required_packages:
        try:
            exec(f"import {package} as {alias}")
            print(f"OK: {package} imported successfully")
        except ImportError as e:
            print(f"ERROR: Failed to import {package}: {e}")
            failed.append(package)
    
    if failed:
        print(f"\nMissing packages: {', '.join(failed)}")
        print("Install with: pip install " + " ".join([p for p in failed if p not in ['datetime', 'json', 're', 'typing']]))
        return False
    
    return True


def test_actant_environment():
    """Test Actant environment"""
    print("\n" + "="*50)
    print("TESTING ACTANT ENVIRONMENT")
    print("="*50)
    
    # Check if Actant directory exists
    actant_dir = r"C:\Program Files\Actant\ActantRisk"
    if os.path.exists(actant_dir):
        print(f"OK: Actant directory found: {actant_dir}")
        
        # Check if ActantRisk.exe exists
        exe_path = os.path.join(actant_dir, "ActantRisk.exe")
        if os.path.exists(exe_path):
            print(f"OK: ActantRisk.exe found")
        else:
            print(f"WARNING: ActantRisk.exe not found at {exe_path}")
            
        # Check if ActantRisk is running
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq ActantRisk.exe', '/NH'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if 'ActantRisk.exe' in result.stdout:
                print("OK: ActantRisk.exe is running")
            else:
                print("WARNING: ActantRisk.exe is not running")
                
        except Exception as e:
            print(f"ERROR checking if ActantRisk is running: {e}")
            
    else:
        print(f"WARNING: Actant directory not found: {actant_dir}")
        print("This is OK if you plan to use mock data or existing JSON files")
    
    return True


def test_file_structure():
    """Test file structure"""
    print("\n" + "="*50)
    print("TESTING FILE STRUCTURE")
    print("="*50)
    
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    required_files = [
        'bond_option_pricer.py',
        'actant_export_parser.py',
        'pricing_monkey_scraper.py',
        'volatility_calculator.py',
        'run_volatility_comparison.bat'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"OK: {file} found")
        else:
            print(f"ERROR: {file} not found")
            missing.append(file)
    
    if missing:
        print(f"\nMissing files: {', '.join(missing)}")
        return False
    
    return True


def test_bond_option_pricer():
    """Test bond option pricer module"""
    print("\n" + "="*50)
    print("TESTING BOND OPTION PRICER")
    print("="*50)
    
    try:
        from bond_option_pricer import calculate_bond_option_volatility, parse_treasury_price
        print("OK: Imported bond_option_pricer functions")
        
        # Test price parser
        test_price = "110-08.5"
        result = parse_treasury_price(test_price)
        print(f"OK: parse_treasury_price('{test_price}') = {result}")
        
        # Test volatility calculation
        vol = calculate_bond_option_volatility(
            strike=110.5,
            future_price=110.25,
            days_to_expiry=30,
            market_price_64ths=20,
            option_type='call'
        )
        print(f"OK: calculate_bond_option_volatility returned implied vol: {vol['implied_vol_price']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return False


def test_data_files():
    """Test for existing data files"""
    print("\n" + "="*50)
    print("TESTING DATA FILES")
    print("="*50)
    
    data_files = {
        'actant_data.csv': 'Actant export data',
        'pm_data.csv': 'Pricing Monkey data',
        'volatility_comparison_raw.csv': 'Raw comparison results',
        'volatility_comparison_formatted.csv': 'Formatted comparison results',
        'volatility_comparison_report.html': 'HTML report'
    }
    
    for file, desc in data_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"OK: {file} exists ({size} bytes) - {desc}")
        else:
            print(f"INFO: {file} not found - {desc}")
    
    # Check for log files
    log_files = [
        'actant_export_parser.log',
        'pricing_monkey_scraper.log',
        'volatility_calculator.log'
    ]
    
    print("\nLog files:")
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"OK: {log_file} exists ({size} bytes)")
            
            # Show last few lines
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  Last line: {lines[-1].strip()}")
            except:
                pass
        else:
            print(f"INFO: {log_file} not found")
    
    return True


def test_individual_scripts():
    """Test running individual scripts with --test flag"""
    print("\n" + "="*50)
    print("TESTING INDIVIDUAL SCRIPTS")
    print("="*50)
    
    # Test actant parser
    print("\nTesting actant_export_parser.py...")
    try:
        # Create a minimal test
        import actant_export_parser
        print("OK: actant_export_parser imports successfully")
    except Exception as e:
        print(f"ERROR importing actant_export_parser: {e}")
    
    # Test PM scraper
    print("\nTesting pricing_monkey_scraper.py...")
    try:
        import pricing_monkey_scraper
        print("OK: pricing_monkey_scraper imports successfully")
    except Exception as e:
        print(f"ERROR importing pricing_monkey_scraper: {e}")
    
    # Test calculator
    print("\nTesting volatility_calculator.py...")
    try:
        import volatility_calculator
        print("OK: volatility_calculator imports successfully")
    except Exception as e:
        print(f"ERROR importing volatility_calculator: {e}")
    
    return True


def main():
    """Run all tests"""
    print("VOLATILITY COMPARISON TOOL - DIAGNOSTIC TEST")
    print("=" * 70)
    
    tests = [
        test_python_version,
        test_imports,
        test_file_structure,
        test_bond_option_pricer,
        test_actant_environment,
        test_data_files,
        test_individual_scripts
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\nERROR in {test.__name__}: {e}")
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed < total:
        print("\nTROUBLESHOOTING:")
        print("1. Check the individual test results above")
        print("2. Look for ERROR messages")
        print("3. Check log files for more details")
        print("4. Try running scripts individually with logging")
    else:
        print("\nAll tests passed! The tool should work correctly.")
        print("If you still have issues, check the log files for runtime errors.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main()) 