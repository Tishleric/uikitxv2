@echo on
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "LOGS_DIR=%SCRIPT_DIR%logs"
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "TSTAMP=%DATE%_%TIME%"
set "TSTAMP=%TSTAMP::=-%"
set "TSTAMP=%TSTAMP:/=-%"
set "TSTAMP=%TSTAMP:.=-%"
set "TSTAMP=%TSTAMP: =_%"
set "LOGFILE=%LOGS_DIR%\diag_batch_simple_%TSTAMP%.log"
echo [%DATE% %TIME%] Logging to %LOGFILE%
>> "%LOGFILE%" echo [%DATE% %TIME%] Logging to %LOGFILE%
>> "%LOGFILE%" echo Working directory: %CD%
>> "%LOGFILE%" dir /b

set "PM_URL=https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c"

echo [%DATE% %TIME%] Resolving Python for diagnostics…
>> "%LOGFILE%" echo [%DATE% %TIME%] Resolving Python for diagnostics…
set "PYCMD="
if defined CONDA_PYTHON_EXE if exist "%CONDA_PYTHON_EXE%" set "PYCMD=%CONDA_PYTHON_EXE%"
if not defined PYCMD (
  for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYCMD set "PYCMD=%%~fP"
)
if not defined PYCMD if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYCMD=%USERPROFILE%\Anaconda3\python.exe"
if not defined PYCMD if exist "%ProgramData%\Anaconda3\python.exe" set "PYCMD=%ProgramData%\Anaconda3\python.exe"
if not defined PYCMD if exist "%USERPROFILE%\miniconda3\python.exe" set "PYCMD=%USERPROFILE%\miniconda3\python.exe"
if not defined PYCMD if exist "%ProgramData%\Miniconda3\python.exe" set "PYCMD=%ProgramData%\Miniconda3\python.exe"
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

echo [%DATE% %TIME%] Ensuring Playwright is installed…>> "%LOGFILE%"
"%PYRUN%" -m pip install --upgrade playwright >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [%DATE% %TIME%] ERROR: Failed to install playwright.>> "%LOGFILE%"
)

echo [%DATE% %TIME%] Ensuring Edge support is installed…>> "%LOGFILE%"
"%PYRUN%" -m playwright install msedge >> "%LOGFILE%" 2>&1

set "EDGE_EXE="
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE_EXE if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE_EXE if exist "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=%LocalAppData%\Microsoft\Edge\Application\msedge.exe"

if defined EDGE_EXE (
  echo [%DATE% %TIME%] Starting Edge with remote debugging and PM URL…>> "%LOGFILE%"
  start "" "%EDGE_EXE%" --remote-debugging-port=9222 "%PM_URL%"
  echo Press any key after logging into Pricing Monkey (if required)…
  pause >nul
) else (
  echo [%DATE% %TIME%] Edge executable not found; continuing without auto-start.>> "%LOGFILE%"
  echo [%DATE% %TIME%] Trying protocol launch: microsoft-edge:%PM_URL%>> "%LOGFILE%"
  start "" microsoft-edge:%PM_URL%
)

if not exist "%SCRIPT_DIR%\pm_playwright_probe.py" (
  echo [%DATE% %TIME%] ERROR: Probe script not found at %SCRIPT_DIR%\pm_playwright_probe.py>> "%LOGFILE%"
  echo [%DATE% %TIME%] ERROR: Probe script not found at %SCRIPT_DIR%\pm_playwright_probe.py
  goto :eof
)

echo [%DATE% %TIME%] Running diagnostics probe…
>> "%LOGFILE%" echo [%DATE% %TIME%] Running diagnostics probe…
"%PYRUN%" -X utf8 "%SCRIPT_DIR%\pm_playwright_probe.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [%DATE% %TIME%] Direct run failed; retrying from current directory…>> "%LOGFILE%"
  pushd "%SCRIPT_DIR%"
  "%PYRUN%" -X utf8 pm_playwright_probe.py >> "%LOGFILE%" 2>&1
  popd
)
set ERR=%ERRORLEVEL%
echo [%DATE% %TIME%] Probe exit code: %ERR%>> "%LOGFILE%"

echo [%DATE% %TIME%] Diagnostics finished. See %LOGFILE%

endlocal
