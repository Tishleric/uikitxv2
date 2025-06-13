@echo off
echo VOLATILITY COMPARISON TOOL
echo ========================

echo Step 1: Export Actant risk to JSON...
call C:\Scripts\ActantRiskExportAuto.bat

echo Step 2: Parse Actant JSON for F, K, T, Vol...
python actant_parser.py

echo Step 3: Scrape Pricing Monkey...
python pm_scraper.py

echo Step 4: Calculate and compare volatilities...
python compare_volatilities.py

pause 