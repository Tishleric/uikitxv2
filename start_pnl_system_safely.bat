@echo off
REM =====================================================
REM Safe PnL System Startup
REM =====================================================
REM This script safely starts the PnL watchers by:
REM 1. Checking database exists
REM 2. Marking existing files as processed
REM 3. Starting watchers in the correct order
REM =====================================================

echo ============================================
echo Safe PnL System Startup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Navigate to project root
cd /d "%~dp0"

echo [1/4] Checking database...
if not exist "trades.db" (
    echo Creating new trades.db...
    python -c "import sqlite3; from lib.trading.pnl_fifo_lifo import create_all_tables; conn = sqlite3.connect('trades.db'); create_all_tables(conn); conn.close(); print('Database created successfully')"
) else (
    echo Database exists: trades.db
)

echo.
echo [2/4] Verifying processed files...
python scripts\verify_processed_files.py
if errorlevel 1 (
    echo ERROR: Failed to verify processed files
    pause
    exit /b 1
)

echo.
echo [3/4] Marking existing files as processed...
echo This prevents reprocessing of historical data
python scripts\mark_existing_files_processed.py
if errorlevel 1 (
    echo ERROR: Failed to mark existing files
    pause
    exit /b 1
)

echo.
echo [4/4] Starting watchers...
echo.
echo IMPORTANT: Only NEW files added after this point will be processed
echo.
pause

REM Run the main watcher startup with ALL watchers
call run_all_pnl_watchers.bat 