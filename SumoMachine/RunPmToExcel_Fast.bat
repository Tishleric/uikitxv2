@echo off
echo =====================================
echo PmToExcel Automation
echo =====================================
echo.
echo Loading Python libraries...
echo (This may take a few seconds on first run)
echo.

REM Create output directory if it doesn't exist
set OUTPUT_DIR=C:\Users\g.shah\Documents\Pm2Excel
if not exist "%OUTPUT_DIR%" (
    echo Creating output directory: %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

REM Change to the directory containing the script
cd /d "%~dp0"

REM Show a loading message and run Python in the same window
echo Starting automation...
python PmToExcel.py

REM Keep the window open if there was an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Script failed with error code %ERRORLEVEL%
    echo Press any key to exit...
    pause > nul
) else (
    echo.
    echo Script completed successfully!
    echo Log files saved to: %OUTPUT_DIR%
    timeout /t 3
) 