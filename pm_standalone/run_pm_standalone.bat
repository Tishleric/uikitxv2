@echo off
setlocal ENABLEDELAYEDEXPANSION

rem Determine script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [!DATE! !TIME!] Resolving Python interpreter...
rem Resolve a Python interpreter (Anaconda or system)
set "PYCMD="
if defined CONDA_PYTHON_EXE if exist "%CONDA_PYTHON_EXE%" set "PYCMD=%CONDA_PYTHON_EXE%"

if not defined PYCMD (
  echo [!DATE! !TIME!] Trying PATH: where python
  for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYCMD set "PYCMD=%%~fP"
  )
)

if not defined PYCMD (
  echo [!DATE! !TIME!] Checking %USERPROFILE%\Anaconda3\python.exe
  if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYCMD=%USERPROFILE%\Anaconda3\python.exe"
)

if not defined PYCMD (
  echo [!DATE! !TIME!] Checking %ProgramData%\Anaconda3\python.exe
  if exist "%ProgramData%\Anaconda3\python.exe" set "PYCMD=%ProgramData%\Anaconda3\python.exe"
)

if not defined PYCMD (
  echo [!DATE! !TIME!] Checking %USERPROFILE%\miniconda3\python.exe
  if exist "%USERPROFILE%\miniconda3\python.exe" set "PYCMD=%USERPROFILE%\miniconda3\python.exe"
)

if not defined PYCMD (
  echo [!DATE! !TIME!] Checking %ProgramData%\Miniconda3\python.exe
  if exist "%ProgramData%\Miniconda3\python.exe" set "PYCMD=%ProgramData%\Miniconda3\python.exe"
)

if not defined PYCMD (
  echo [!DATE! !TIME!] Trying Windows launcher: py -3
  where py >nul 2>nul && (
    py -3 --version >nul 2>nul && set "PYCMD=py -3"
  )
)

if not defined PYCMD (
  echo [!DATE! !TIME!] ERROR: No Python interpreter found. Please install Python 3 or ensure PATH/Conda is active.
  echo [!DATE! !TIME!] Sleeping 300 seconds...
  powershell -NoProfile -Command "Start-Sleep -Seconds 300"
  goto :eof
)

set "PYRUN=%PYCMD%"
echo [!DATE! !TIME!] Using Python: %PYRUN%

:loop
  echo [!DATE! !TIME!] Launching Python runner...
  %PYRUN% -X utf8 "%SCRIPT_DIR%\pm_runner.py"
  echo [!DATE! !TIME!] Sleeping 300 seconds...
  for /l %%S in (300,-1,1) do (
    powershell -NoProfile -Command "$p=$host.UI.RawUI.CursorPosition; $p.X=0; $host.UI.RawUI.CursorPosition=$p; Write-Host -NoNewline ('   '); $host.UI.RawUI.CursorPosition=$p; Write-Host -NoNewline ('{0,3}' -f %%S); Start-Sleep -Seconds 1"
  )
  echo.
  goto loop

endlocal
