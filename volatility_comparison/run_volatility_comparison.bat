@echo off
echo Starting Volatility Comparison Tool...
echo.

echo Step 1: Parsing Actant JSON data...
python actant_parser.py
if errorlevel 1 goto error

echo.
echo Step 2: Capturing Pricing Monkey data (this will open your browser)...
python pm_scraper.py
if errorlevel 1 goto error

echo.
echo Step 3: Running volatility comparison...
python compare_volatilities.py
if errorlevel 1 goto error

echo.
echo ==========================================
echo Volatility comparison completed successfully!
echo ==========================================

if exist actant_timestamp.txt (
    echo.
    echo Actant data captured at:
    type actant_timestamp.txt
)

if exist pm_timestamp.txt (
    echo.
    echo PM data captured at:
    type pm_timestamp.txt
)

echo.
echo Check the timestamped Excel file in this directory.
pause
goto end

:error
echo.
echo ERROR: Process failed! Check the error messages above.
pause

:end 