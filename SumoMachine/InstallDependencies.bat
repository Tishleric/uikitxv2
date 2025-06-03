@echo off
echo Installing required Python packages for PmToExcel...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Installing packages...
echo.

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing required packages...

REM Install packages from requirements.txt
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    REM Fallback to individual installations if requirements.txt is missing
    echo requirements.txt not found. Installing packages individually...
    python -m pip install pandas>=1.5.0
    python -m pip install pyperclip>=1.8.0
    python -m pip install pywinauto>=0.6.8
    python -m pip install openpyxl>=3.0.0
)

echo.
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Package installation failed!
    echo Please check the error messages above.
) else (
    echo SUCCESS: All packages installed successfully!
    echo You can now run RunPmToExcel.bat
)

echo.
echo Press any key to exit...
pause > nul 