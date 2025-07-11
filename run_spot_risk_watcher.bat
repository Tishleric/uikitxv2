@echo off
REM Batch file to run Spot Risk file watcher with Anaconda Python

echo ============================================================
echo Spot Risk File Watcher Service (Anaconda Python)
echo ============================================================

REM Set Anaconda Python path
set ANACONDA_PYTHON=C:\Users\erict\anaconda3\python.exe

REM Check if Anaconda Python exists
if not exist "%ANACONDA_PYTHON%" (
    echo Error: Anaconda Python not found at %ANACONDA_PYTHON%
    echo Please update the ANACONDA_PYTHON path in this script
    pause
    exit /b 1
)

REM Install watchdog if needed
echo.
echo Checking for watchdog library...
%ANACONDA_PYTHON% -c "import watchdog" 2>nul
if errorlevel 1 (
    echo Installing watchdog library...
    %ANACONDA_PYTHON% -m pip install watchdog
)

REM Run the watcher
echo.
echo Starting file watcher...
echo Press Ctrl+C to stop
echo.
%ANACONDA_PYTHON% run_spot_risk_watcher.py

pause 