@echo off
REM =====================================================
REM PnL System File Watchers - Run All
REM =====================================================
REM This batch file runs all file watchers needed for the
REM real-time PnL FIFO/LIFO calculation system
REM =====================================================

echo ============================================
echo Starting PnL System File Watchers
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Set the working directory to the project root
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Get current timestamp for log files
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)
set timestamp=%mydate%_%mytime: =0%

echo Starting watchers with logs in logs\ directory...
echo.

REM =====================================================
REM 1. Trade Ledger Watcher
REM =====================================================
echo [1/4] Starting Trade Ledger Watcher...
echo      - Monitors: data\input\trade_ledger\
echo      - Purpose: Process new trades through FIFO/LIFO engine
start "Trade Ledger Watcher" /min cmd /c "python scripts\run_trade_ledger_watcher.py > logs\trade_ledger_watcher_%timestamp%.log 2>&1"
timeout /t 2 /nobreak >nul

REM =====================================================
REM 2. Spot Risk Price Watcher
REM =====================================================
echo [2/4] Starting Spot Risk Price Watcher...
echo      - Monitors: data\input\actant_spot_risk\
echo      - Purpose: Update current prices in trades.db
start "Spot Risk Price Watcher" /min cmd /c "python scripts\run_spot_risk_price_watcher.py > logs\spot_risk_price_watcher_%timestamp%.log 2>&1"
timeout /t 2 /nobreak >nul

REM =====================================================
REM 3. Spot Risk Processing Watcher (for Greeks)
REM =====================================================
echo [3/4] Starting Spot Risk Processing Watcher...
echo      - Monitors: data\input\actant_spot_risk\
echo      - Purpose: Calculate Greeks and process spot risk data
start "Spot Risk Processing Watcher" /min cmd /c "python scripts\run_spot_risk_watcher.py > logs\spot_risk_processor_%timestamp%.log 2>&1"
timeout /t 2 /nobreak >nul

REM =====================================================
REM 4. Market Price Monitor (if available)
REM =====================================================
echo [4/5] Checking Market Price Monitor...
if exist "scripts\run_corrected_market_price_monitor.py" (
    echo      Starting Market Price Monitor...
    echo      - Monitors: data\input\market_prices\
    echo      - Purpose: Process futures and options price files
    start "Market Price Monitor" /min cmd /c "python scripts\run_corrected_market_price_monitor.py > logs\market_price_monitor_%timestamp%.log 2>&1"
) else (
    echo      Market Price Monitor not available (deprecated)
)

REM =====================================================
REM 5. Positions Watcher
REM =====================================================
echo [5/5] Starting Positions Watcher...
echo      - Purpose: Aggregate and monitor position changes
if exist "scripts\run_positions_watcher.py" (
    start "Positions Watcher" /min cmd /c "python scripts\run_positions_watcher.py > logs\positions_watcher_%timestamp%.log 2>&1"
) else (
    echo      Positions Watcher script not found
)
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo All watchers started successfully!
echo ============================================
echo.
echo Watchers are running in minimized windows.
echo Log files are being written to: logs\
echo.
echo To stop all watchers:
echo   1. Close this window and all minimized watcher windows
echo   2. Or use Task Manager to end Python processes
echo.
echo Press any key to open the log directory...
pause >nul

REM Open logs directory
start "" "logs"

echo.
echo This window will stay open to show status.
echo Press Ctrl+C to stop monitoring (watchers will continue running).
echo.

REM Monitor the watchers (optional - shows they're still running)
:monitor_loop
timeout /t 30 /nobreak >nul
echo [%DATE% %TIME%] Watchers are running...
goto monitor_loop 