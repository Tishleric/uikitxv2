@echo off
REM Batch file to run spot risk processing with Anaconda Python

echo ============================================================
echo Spot Risk Processing with Anaconda Python
echo ============================================================

REM Check if input file is provided as argument
if "%~1"=="" (
    echo Usage: run_spot_risk_processing.bat [input_csv_file]
    echo Example: run_spot_risk_processing.bat data/input/actant_spot_risk/bav_analysis_20250709_193912.csv
    exit /b 1
)

REM Set Anaconda Python path
set ANACONDA_PYTHON=C:\Users\erict\anaconda3\python.exe

REM Check if Anaconda Python exists
if not exist "%ANACONDA_PYTHON%" (
    echo Error: Anaconda Python not found at %ANACONDA_PYTHON%
    echo Please update the ANACONDA_PYTHON path in this script
    exit /b 1
)

REM Run the processing
echo.
echo Processing file: %1
echo Using Python: %ANACONDA_PYTHON%
echo.

"%ANACONDA_PYTHON%" -c "import sys; sys.path.insert(0, '.'); from tests.actant_spot_risk.test_full_pipeline import process_spot_risk_csv; process_spot_risk_csv('%1')"

echo.
echo Processing complete!
pause 