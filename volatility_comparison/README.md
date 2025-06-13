# Volatility Comparison Tool

A comprehensive tool for comparing implied volatilities across three sources:
1. **Actant Risk** - Risk management system volatilities
2. **Pricing Monkey** - Market implied volatilities
3. **Internal Model** - Mathematically derived volatilities using bond future option pricing

## Overview

This tool automates the collection and comparison of option volatilities to help identify pricing discrepancies and validate models. It handles ZN (10-year Treasury Note) options and can be extended to other instruments.

## Installation

### Prerequisites
- Windows OS (for Actant Risk integration)
- Python 3.8 or higher
- Actant Risk export script at `C:\Scripts\ActantRiskExportAuto.bat`
- JSON exports saved to `Z:\ActantEOD\`
- Internet connection (for Pricing Monkey scraping)

### Python Dependencies
Install required packages:
```bash
pip install pandas numpy scipy pyperclip pywinauto
```

## Usage

### Quick Start
1. Run the test script to verify your setup:
   ```bash
   python test_components.py
   ```

2. Run the complete comparison:
   ```bash
   run_volatility_comparison.bat
   ```

### Step-by-Step Usage

#### Option 1: Automated Full Run
Simply double-click `run_volatility_comparison.bat` or run from command line:
```bash
run_volatility_comparison.bat
```

The script will:
1. Check dependencies
2. Run Actant export (if available)
3. Scrape Pricing Monkey data
4. Calculate internal volatilities
5. Generate comparison reports

#### Option 2: Run Individual Components

1. **Test your setup:**
   ```bash
   python test_components.py
   ```

2. **Actant Export (optional):**
   ```bash
   python actant_export_parser.py
   ```
   - Requires ActantRisk.exe to be running
   - Creates: `actant_data.csv`

3. **Pricing Monkey Scraper:**
   ```bash
   python pricing_monkey_scraper.py
   ```
   - Opens browser automatically
   - Do not use mouse/keyboard during scraping
   - Creates: `pm_data.csv`

4. **Volatility Calculator:**
   ```bash
   python volatility_calculator.py
   ```
   - Requires `pm_data.csv` (minimum)
   - Creates comparison reports

## Output Files

### Data Files
- `actant_data.csv` - Actant option data (strike, vol, expiry, etc.)
- `pm_data.csv` - Pricing Monkey market data
- `volatility_comparison_raw.csv` - Complete comparison data
- `volatility_comparison_formatted.csv` - Summary table
- `volatility_comparison_report.html` - Visual HTML report

### Log Files
- `actant_export_parser.log` - Actant export details
- `pricing_monkey_scraper.log` - PM scraping details
- `volatility_calculator.log` - Calculation details
- `volatility_comparison_debug_*.log` - Master batch file log

## Troubleshooting

### Nothing Happens When Running the Batch File
1. Open Command Prompt and navigate to the tool directory
2. Run the batch file manually:
   ```bash
   run_volatility_comparison.bat
   ```
3. Check the generated log file: `volatility_comparison_debug_*.log`

### Python Not Found
- Ensure Python is installed and in your PATH
- Test with: `python --version`

### Import Errors
Run the test script to identify missing packages:
```bash
python test_components.py
```

Install missing packages:
```bash
pip install pandas numpy scipy pyperclip pywinauto
```

### Actant Export Issues
- **ActantRisk.exe not found**: Install Actant or skip this step
- **Export fails**: Ensure ActantRisk.exe is running before the script
- **No JSON found**: Check common export locations or specify path

To skip Actant and use only PM data:
- When prompted, enter 'Y' to skip Actant export

### Pricing Monkey Issues
- **Wrong data scraped**: Verify the URL in `pricing_monkey_scraper.py`
- **Browser doesn't open**: Check default browser settings
- **Clipboard empty**: Don't use mouse/keyboard during scraping

To skip PM scraping (for testing):
- When prompted, enter 'Y' to skip Pricing Monkey

### Calculation Errors
Check `volatility_calculator.log` for:
- Missing data files
- Invalid option parameters
- Convergence issues in volatility solver

### Remote Machine Debugging

1. **Run diagnostic test first:**
   ```bash
   python test_components.py > diagnostic_report.txt 2>&1
   ```
   Send `diagnostic_report.txt` for analysis

2. **Check all log files:**
   ```bash
   dir *.log
   type volatility_comparison_debug_*.log
   ```

3. **Test individual components:**
   ```bash
   python actant_export_parser.py > actant_test.txt 2>&1
   python pricing_monkey_scraper.py > pm_test.txt 2>&1
   python volatility_calculator.py > calc_test.txt 2>&1
   ```

4. **Common remote issues:**
   - Different Actant installation path
   - Firewall blocking browser automation
   - Different regional settings affecting number parsing

## Configuration

### Adjusting Parameters

Edit `bond_option_pricer.py` to change:
- Default DV01: `0.063`
- Default Convexity: `0.002404`

Edit `pricing_monkey_scraper.py` to change:
- PM URL
- Navigation sequence (TABs, arrows)
- Wait times

Edit `actant_export_parser.py` to change:
- Actant directory path
- Export command parameters
- JSON search paths

## Advanced Usage

### Using Existing Data Files
If you have existing CSV files from previous runs:
```bash
# Skip data collection, just run comparison
python volatility_calculator.py
```

### Custom Actant JSON Location
Edit `actant_export_parser.py` and modify the `search_paths` list in `find_actant_json()`.

### Batch Processing
Create a loop in the batch file to run periodically:
```batch
:LOOP
call run_volatility_comparison.bat
timeout /t 3600
goto LOOP
```

## Components

### 1. `bond_option_pricer.py`
Core pricing engine that calculates theoretical volatilities using:
- Black-Scholes model in yield space
- Bond-specific adjustments (DV01, convexity)
- Handles both price and yield volatility conversions

### 2. `actant_export_parser.py`
- Triggers ActantRisk.exe export
- Finds and parses JSON output
- Extracts ATM (0 shock) option data
- Handles various JSON structures

### 3. `pricing_monkey_scraper.py`
- Automates browser to navigate PM interface
- Uses keyboard shortcuts to select data
- Copies to clipboard and parses
- Extracts market prices and implied vols

### 4. `volatility_calculator.py`
- Loads data from both sources
- Matches options by strike/expiry
- Calculates internal model volatilities
- Generates comparison reports
- Creates HTML visualization

### 5. `run_volatility_comparison.bat`
- Master orchestration script
- Checks dependencies
- Runs components in sequence
- Comprehensive logging
- Error handling and recovery

### 6. `test_components.py`
- Diagnostic tool
- Tests each component
- Verifies dependencies
- Checks file structure
- Identifies issues

## Support

For issues:
1. Run `test_components.py` first
2. Check all log files
3. Verify data in CSV files
4. Test components individually
5. Enable debug logging in Python scripts

## Future Enhancements
- Support for put options
- Additional instruments beyond ZN
- Real-time monitoring mode
- Email notifications
- Database storage
- Web interface 