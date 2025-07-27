@echo off
REM Test PnL System Startup Script - Uses test database (trades_test.db)
REM This allows testing all watchers without affecting production trades.db

echo ========================================
echo TEST PnL System Startup (SAFE MODE)
echo Using TEST DATABASE: trades_test.db
echo ========================================
echo.

REM Set test database name
set TEST_DB=trades_test.db

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Navigate to project root
cd /d "%~dp0"

echo Step 1: Creating/Checking test database...
if not exist "%TEST_DB%" (
    echo Creating new test database: %TEST_DB%
    python -c "import sqlite3; conn = sqlite3.connect('%TEST_DB%'); conn.close()"
) else (
    echo Test database already exists: %TEST_DB%
)

echo.
echo Step 2: Creating tables in test database...
python create_test_tables.py %TEST_DB%
if errorlevel 1 (
    echo ERROR: Failed to create tables
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying processed files status in TEST database...
python scripts/verify_processed_files.py --db %TEST_DB%

echo.
echo Step 4: Marking existing files as processed in TEST database...
echo This prevents reprocessing of historical data
python scripts/mark_existing_files_processed.py --db %TEST_DB%
if errorlevel 1 (
    echo WARNING: Failed to mark files as processed, but continuing...
)

echo.
echo ========================================
echo Starting ALL watchers with TEST DATABASE
echo ========================================
echo.

REM Create logs directory
if not exist "logs" mkdir logs

REM Get timestamp for log files
set timestamp=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

echo Starting watchers with TEST database...
echo.

REM Start Trade Ledger Watcher
echo Starting Trade Ledger Watcher (TEST)...
start "Trade Ledger Watcher TEST" /min cmd /c "python scripts\run_trade_ledger_watcher.py --db %TEST_DB% > logs\test_trade_ledger_%timestamp%.log 2>&1"

REM Start Spot Risk Price Watcher
echo Starting Spot Risk Price Watcher (TEST)...
start "Spot Risk Price Watcher TEST" /min cmd /c "python scripts\run_spot_risk_price_watcher.py --db %TEST_DB% > logs\test_spot_risk_price_%timestamp%.log 2>&1"

REM Start Spot Risk Processing Watcher (if needed)
echo Starting Spot Risk Processing Watcher (TEST)...
start "Spot Risk Processing Watcher TEST" /min cmd /c "python scripts\run_spot_risk_watcher.py > logs\test_spot_risk_processor_%timestamp%.log 2>&1"

REM Start Market Price Monitor (if exists)
if exist "scripts\run_corrected_market_price_monitor.py" (
    echo Starting Market Price Monitor (TEST)...
    start "Market Price Monitor TEST" /min cmd /c "python scripts\run_corrected_market_price_monitor.py > logs\test_market_price_monitor_%timestamp%.log 2>&1"
)

REM Start Positions Watcher (if exists)
if exist "scripts\run_positions_watcher.py" (
    echo Starting Positions Watcher (TEST)...
    start "Positions Watcher TEST" /min cmd /c "python scripts\run_positions_watcher.py > logs\test_positions_watcher_%timestamp%.log 2>&1"
)

echo.
echo ========================================
echo TEST WATCHERS STARTED!
echo.
echo Using TEST DATABASE: %TEST_DB%
echo Log files: logs\test_*_%timestamp%.log
echo.
echo To stop watchers, close this window and run:
echo   stop_all_watchers.bat
echo.
echo To view test database contents:
echo   python -c "import sqlite3; conn = sqlite3.connect('%TEST_DB%'); print(conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"
echo ========================================
pause 