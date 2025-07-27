@echo off
REM =====================================================
REM Stop All Python Watchers
REM =====================================================

echo ============================================
echo Stopping All Python Watchers
echo ============================================
echo.

echo Looking for Python processes running watcher scripts...
echo.

REM Kill specific watcher processes
taskkill /F /FI "WINDOWTITLE eq Trade Ledger Watcher*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Spot Risk Price Watcher*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Spot Risk Processing Watcher*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Market Price Monitor*" 2>nul

REM Also kill Python processes running our scripts
wmic process where "name='python.exe' and commandline like '%%run_trade_ledger_watcher%%'" delete 2>nul
wmic process where "name='python.exe' and commandline like '%%run_spot_risk_price_watcher%%'" delete 2>nul
wmic process where "name='python.exe' and commandline like '%%run_spot_risk_watcher%%'" delete 2>nul
wmic process where "name='python.exe' and commandline like '%%run_corrected_market_price_monitor%%'" delete 2>nul
wmic process where "name='python.exe' and commandline like '%%run_market_price_monitor%%'" delete 2>nul

echo.
echo All watcher processes have been terminated.
echo.
pause 