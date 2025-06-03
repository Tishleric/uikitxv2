# PmToExcel - Pricing Monkey to Excel Automation

This standalone script automates data extraction from Pricing Monkey and exports it to Excel.

## Prerequisites

- Windows operating system
- Python 3.7 or higher
- Internet browser (for opening Pricing Monkey URL)

## Setup Instructions

### 1. Install Python (if not already installed)
- Download Python from https://www.python.org/downloads/
- During installation, **make sure to check "Add Python to PATH"**

### 2. Install Required Libraries

#### Option A: Using the Batch File (Recommended)
Simply double-click `InstallDependencies.bat`

#### Option B: Using Command Prompt/PowerShell
Open Command Prompt or PowerShell and navigate to the SumoMachine folder, then run:
```bash
pip install -r requirements.txt
```

#### Option C: Manual Installation
If the above methods don't work, install each package individually:
```bash
pip install pandas
pip install pyperclip
pip install pywinauto
pip install openpyxl
```

## Required Python Libraries

- **pandas** - For data manipulation and DataFrame operations
- **pyperclip** - For clipboard operations (copy/paste)
- **pywinauto** - For keyboard automation
- **openpyxl** - For reading/writing Excel files

## Usage

1. Ensure the Excel file exists at: `C:\Users\g.shah\Documents\Pm2Excel\ActantBackend.xlsx`
2. Double-click `RunPmToExcel.bat` to run the automation

The script will:
1. Open the Pricing Monkey URL in your browser
2. Navigate to the data using keyboard commands
3. Copy 5 columns of data (Notes, Trade Amount, Price, DV01, DV01 Gamma)
4. Process the data:
   - Convert prices from XXX-YYY format to decimal (XXX + YYY/32)
   - Divide DV01 and DV01 Gamma by 1000
5. Write the processed data to Sheet1 starting at cell A2

Log files will be saved to: `C:\Users\g.shah\Documents\Pm2Excel\`

## Troubleshooting

### "Python is not recognized as an internal or external command"
- Python is not installed or not in your system PATH
- Reinstall Python and check "Add Python to PATH" during installation

### "No module named 'pandas'" (or other module)
- The required libraries are not installed
- Run `InstallDependencies.bat` or install manually using pip

### Excel file not found error
- Ensure the Excel file exists at the specified network path
- Check that you have access to the network share

### Browser automation issues
- Make sure no other browser windows are interfering
- The script expects the Pricing Monkey page to load within 3 seconds
- You may need to adjust timing constants in the script if your connection is slower

## Files in this Directory

- `PmToExcel.py` - Main automation script
- `RunPmToExcel.bat` - Batch file to run the script
- `InstallDependencies.bat` - Batch file to install required libraries
- `OpenOutputFolder.bat` - Opens the output folder in Windows Explorer
- `requirements.txt` - List of required Python packages
- `README.md` - This file 