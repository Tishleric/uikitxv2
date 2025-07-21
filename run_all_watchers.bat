@echo off
REM Batch file to run all file watchers with Anaconda Python

echo ============================================================
echo Unified Watcher Service (Anaconda Python)
echo ============================================================
echo.
echo This will start all three file watchers:
echo   1. Market Price File Monitor - Price files (2pm/4pm)
echo   2. Spot Risk Watcher - Spot risk files + current prices
echo   3. PNL Pipeline Watcher - TYU5 P&L calculations
echo.
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

REM Check and install required libraries
echo.
echo Checking for required libraries...

REM Check watchdog
%ANACONDA_PYTHON% -c "import watchdog" 2>nul
if errorlevel 1 (
    echo Installing watchdog library...
    %ANACONDA_PYTHON% -m pip install watchdog
)

REM Check pytz
%ANACONDA_PYTHON% -c "import pytz" 2>nul
if errorlevel 1 (
    echo Installing pytz library...
    %ANACONDA_PYTHON% -m pip install pytz
)

REM Check pandas
%ANACONDA_PYTHON% -c "import pandas" 2>nul
if errorlevel 1 (
    echo Installing pandas library...
    %ANACONDA_PYTHON% -m pip install pandas
)

REM Check numpy
%ANACONDA_PYTHON% -c "import numpy" 2>nul
if errorlevel 1 (
    echo Installing numpy library...
    %ANACONDA_PYTHON% -m pip install numpy
)

REM Set monitor log level to reduce noise (ERROR, WARNING, INFO, or QUIET)
set MONITOR_LOG_LEVEL=WARNING

REM Run the unified watcher
echo.
echo ============================================================
echo Starting all file watchers...
echo Monitor log level: %MONITOR_LOG_LEVEL%
echo Press Ctrl+C to stop all watchers
echo ============================================================
echo.

%ANACONDA_PYTHON% scripts\run_all_watchers.py

pause 