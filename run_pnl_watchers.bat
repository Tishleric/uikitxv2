@echo off
REM =====================================================
REM PnL FIFO/LIFO System - Core Watchers
REM =====================================================
REM Runs the essential watchers for trades.db:
REM   1. Trade Ledger Watcher - processes new trades
REM   2. Spot Risk Price Watcher - updates current prices
REM =====================================================

echo ============================================
echo PnL FIFO/LIFO System - Core Watchers
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

REM Create logs directory
if not exist "logs" mkdir logs

echo Starting core PnL watchers...
echo.

REM 1. Trade Ledger Watcher
echo [1/2] Starting Trade Ledger Watcher...
start "Trade Ledger Watcher" cmd /k "python scripts\run_trade_ledger_watcher.py"

REM Small delay between starts
timeout /t 2 /nobreak >nul

REM 2. Spot Risk Price Watcher  
echo [2/2] Starting Spot Risk Price Watcher...
start "Spot Risk Price Watcher" cmd /k "python scripts\run_spot_risk_price_watcher.py"

echo.
echo ============================================
echo Core watchers started!
echo ============================================
echo.
echo Two new windows should have opened:
echo   - Trade Ledger Watcher
echo   - Spot Risk Price Watcher
echo.
echo To stop: Close the watcher windows or press Ctrl+C in each
echo.
pause 