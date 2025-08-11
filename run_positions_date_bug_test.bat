@echo off
setlocal

:: =============================================================================
:: Positions Aggregator Date Bug Diagnostic
:: =============================================================================
:: This script demonstrates how the positions aggregator incorrectly filters
:: closed positions when trades are from future dates (e.g., August 2025).
:: =============================================================================

echo =============================================================================
echo  Positions Aggregator Date Filtering Bug Test
echo =============================================================================
echo.
echo This diagnostic shows why old closed positions appear in the dashboard
echo when your trades are from future dates (August 2025).
echo.

:: Ensure we are in the project root directory
cd /d "%~dp0"

:: Run the diagnostic
python tests\diagnostics\test_positions_date_bug.py

echo.
echo Process completed.
echo.
pause

endlocal