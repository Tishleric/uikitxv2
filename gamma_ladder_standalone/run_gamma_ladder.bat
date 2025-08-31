@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Change to this script's directory
cd /d "%~dp0"

REM Try to find python
where python >nul 2>&1
if errorlevel 1 (
  echo Python not found in PATH. Please install Python 3 and ensure 'python' is in PATH.
  pause
  exit /b 1
)

REM Optionally ensure required packages (comment out if managed elsewhere)
REM python -c "import pandas, numpy" 1>nul 2>nul
REM if errorlevel 1 (
REM   echo Installing required Python packages (pandas, numpy)...
REM   python -m pip install --upgrade pip
REM   python -m pip install pandas numpy
REM )

REM Run the ladder script
python -X utf8 gamma_ladder.py

if errorlevel 1 (
  echo Script exited with error code %errorlevel%.
  pause
) else (
  echo Script started. Close this window to stop.
  REM Keep window open while the script runs
  :loop
  timeout /t 5 >nul
  goto loop
)

endlocal



