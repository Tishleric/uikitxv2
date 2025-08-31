@echo off
setlocal

:: =============================================================
:: Five-Minute Market Snapshot - Standalone Runner
:: =============================================================

:: Move to repo root (directory of this .bat)
cd /d "%~dp0"
echo Running from: %CD%
echo.

:: Clear stale lock if present
del "%PROGRAMDATA%\FiveMinuteMarket\snapshot.lock" 2>nul

:: Verify Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python not found in PATH. Install Python or add it to PATH.
  pause
  exit /b 1
)

echo Launching Five-Minute Market Snapshot service...
echo Logs will stream in the new window. Close that window to stop the service.
echo.

:: Launch in a separate, persistent console window
start "Five-Minute Market Snapshot" cmd /k "python scripts\run_five_minute_market_snapshot.py --config configs\five_minute_market.yaml"

echo Service started (new window opened). You may close this window.
endlocal
exit /b 0

