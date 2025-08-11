@echo off
echo ===================================================
echo Price Updater Diagnostic Suite
echo ===================================================
echo.

cd /d Z:\uikitxv2

echo [1/3] Running database bottleneck test...
echo -------------------------------------------------
python tests\diagnostics\test_database_bottleneck.py
echo.
echo Press any key to continue to next test...
pause > nul

echo [2/3] Starting live pipeline monitor (30 seconds)...
echo -------------------------------------------------
echo This will monitor the live pipeline without interference.
python tests\diagnostics\monitor_price_pipeline.py --duration 30 --db-monitor
echo.
echo Press any key to continue to next test...
pause > nul

echo [3/3] Running full diagnostic simulation...
echo -------------------------------------------------
echo This will simulate messages and measure processing time.
python tests\diagnostics\price_updater_diagnostic.py
echo.

echo ===================================================
echo Diagnostic Suite Complete!
echo ===================================================
echo.
echo Please share the output logs for analysis.
echo.
pause