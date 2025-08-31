@echo off
setlocal ENABLEDELAYEDEXPANSION

rem Self-tee: re-run this batch with PowerShell Tee so all output is logged
if not defined __TEE_ACTIVE__ (
  set "__TEE_ACTIVE__=1"
  set "SCRIPT_DIR=%~dp0"
  cd /d "%SCRIPT_DIR%"
  set "LOGS_DIR=%SCRIPT_DIR%logs"
  if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
  set "TSTAMP=%DATE%_%TIME%"
  set "TSTAMP=%TSTAMP::=-%"
  set "TSTAMP=%TSTAMP:/=-%"
  set "TSTAMP=%TSTAMP:.=-%"
  set "TSTAMP=%TSTAMP: =_%"
  set "LOGFILE=%LOGS_DIR%\diag_batch_%TSTAMP%.log"
  where powershell >nul 2>nul
  if %ERRORLEVEL%==0 (
    powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; & '%~f0' 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"
    goto :eof
  ) else (
    echo [WARNING] PowerShell not found; continuing without full tee logging.
  )
)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Prepare logs directory and file (ensures paths exist if tee is unavailable)
set "LOGS_DIR=%SCRIPT_DIR%logs"
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
if not defined LOGFILE (
  set "TSTAMP=%DATE%_%TIME%"
  set "TSTAMP=%TSTAMP::=-%"
  set "TSTAMP=%TSTAMP:/=-%"
  set "TSTAMP=%TSTAMP:.=-%"
  set "TSTAMP=%TSTAMP: =_%"
  set "LOGFILE=%LOGS_DIR%\diag_batch_%TSTAMP%.log"
)
echo [%DATE% %TIME%] Logging to %LOGFILE%
>> "%LOGFILE%" echo [%DATE% %TIME%] Logging to %LOGFILE%

rem Target PM URL for diagnostics (opening in Edge when available)
set "PM_URL=https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c"

echo [%DATE% %TIME%] Resolving Python for diagnostics…
>> "%LOGFILE%" echo [%DATE% %TIME%] Resolving Python for diagnostics…
set "PYCMD="
if defined CONDA_PYTHON_EXE if exist "%CONDA_PYTHON_EXE%" set "PYCMD=%CONDA_PYTHON_EXE%"
if not defined PYCMD (
  for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYCMD set "PYCMD=%%~fP"
)
if not defined PYCMD (
  if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYCMD=%USERPROFILE%\Anaconda3\python.exe"
)
if not defined PYCMD (
  if exist "%ProgramData%\Anaconda3\python.exe" set "PYCMD=%ProgramData%\Anaconda3\python.exe"
)
if not defined PYCMD (
  if exist "%USERPROFILE%\miniconda3\python.exe" set "PYCMD=%USERPROFILE%\miniconda3\python.exe"
)
if not defined PYCMD (
  if exist "%ProgramData%\Miniconda3\python.exe" set "PYCMD=%ProgramData%\Miniconda3\python.exe"
)
if not defined PYCMD (
  where py >nul 2>nul && ( py -3 --version >nul 2>nul && set "PYCMD=py -3" )
)
if not defined PYCMD (
  echo [%DATE% %TIME%] ERROR: No Python interpreter found.
  >> "%LOGFILE%" echo [%DATE% %TIME%] ERROR: No Python interpreter found.
  goto :eof
)
set "PYRUN=%PYCMD%"
echo [%DATE% %TIME%] Using Python: %PYRUN%
>> "%LOGFILE%" echo [%DATE% %TIME%] Using Python: %PYRUN%

echo [%DATE% %TIME%] Ensuring Playwright is installed…
>> "%LOGFILE%" echo [%DATE% %TIME%] Ensuring Playwright is installed…
powershell -NoProfile -Command "$env:PYRUN;$env:LOGFILE; & $env:PYRUN -m pip install --upgrade playwright 2>&1 | Tee-Object -FilePath $env:LOGFILE -Append"
if errorlevel 1 (
  echo [%DATE% %TIME%] ERROR: Failed to install playwright.
  >> "%LOGFILE%" echo [%DATE% %TIME%] ERROR: Failed to install playwright.
  goto :eof
)

echo [%DATE% %TIME%] Ensuring Edge support is installed…
>> "%LOGFILE%" echo [%DATE% %TIME%] Ensuring Edge support is installed…
powershell -NoProfile -Command "$env:PYRUN;$env:LOGFILE; & $env:PYRUN -m playwright install msedge 2>&1 | Tee-Object -FilePath $env:LOGFILE -Append"

echo [!DATE! !TIME!] Optional: If you want to use current Edge profile, start Edge with remote debugging:
echo    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222 "%PM_URL%"
echo    or
echo    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222 "%PM_URL%"
echo    (You can run this manually in a separate window before continuing.)
echo.
>> "%LOGFILE%" echo [Current Edge debug commands printed above]

rem Attempt to auto-start Edge with remote debugging if found
set "EDGE_EXE="
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE_EXE if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE_EXE if exist "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%LocalAppData%\Microsoft\Edge\Application\msedge.exe"

if defined EDGE_EXE (
  echo [%DATE% %TIME%] Attempting to start Edge with remote debugging: "%EDGE_EXE%"
  >> "%LOGFILE%" echo [%DATE% %TIME%] Attempting to start Edge with remote debugging: "%EDGE_EXE%"
  start "" "%EDGE_EXE%" --remote-debugging-port=9222 "%PM_URL%"
  echo [%DATE% %TIME%] If a login is required, complete it in the Edge window.
  >> "%LOGFILE%" echo [%DATE% %TIME%] Waiting for operator to complete login if required.
  echo Press any key after you have finished logging in to Pricing Monkey...
  pause >nul
) else (
  echo [%DATE% %TIME%] Could not find Edge executable automatically; proceeding without auto-start.
  >> "%LOGFILE%" echo [%DATE% %TIME%] Could not find Edge executable automatically; proceeding without auto-start.
)

echo [%DATE% %TIME%] Starting diagnostics probe. You may switch to the other machine during Step 4.
>> "%LOGFILE%" echo [%DATE% %TIME%] Starting diagnostics probe.
powershell -NoProfile -Command "$env:PYRUN;$env:LOGFILE; & $env:PYRUN -X utf8 '%SCRIPT_DIR%\pm_playwright_probe.py' 2>&1 | Tee-Object -FilePath $env:LOGFILE -Append"
set ERR=%ERRORLEVEL%
echo [%DATE% %TIME%] Probe exit code: %ERR%
>> "%LOGFILE%" echo [%DATE% %TIME%] Probe exit code: %ERR%

echo [%DATE% %TIME%] Diagnostics finished. Check the logs folder for outputs.
>> "%LOGFILE%" echo [%DATE% %TIME%] Diagnostics finished. Check the logs folder for outputs.

endlocal
