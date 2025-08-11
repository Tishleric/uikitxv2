@echo off
setlocal

:: =============================================================================
:: Manual 4PM EOD Settlement Trigger
:: =============================================================================
:: This replaces the automatic 4pm roll that was previously triggered by
:: the Close Price Watcher. It performs the exact same operations:
::   1. Rolls sodTom prices to sodTod
::   2. Performs mark-to-market on all positions
:: =============================================================================

echo =============================================================================
echo  Manual 4PM EOD Settlement Trigger
echo =============================================================================
echo.

:: Ensure we are in the project root directory
cd /d "%~dp0"

:: Run the manual trigger
python scripts\manual_eod_settlement.py %*

echo.
echo Process completed.
echo.
pause

endlocal