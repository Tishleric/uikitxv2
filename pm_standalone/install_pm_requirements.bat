@echo on
setlocal ENABLEDELAYEDEXPANSION

rem Determine script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [!DATE! !TIME!] Resolving Python interpreter for dependency installation...
set "PYCMD="
if defined CONDA_PYTHON_EXE if exist "%CONDA_PYTHON_EXE%" set "PYCMD=%CONDA_PYTHON_EXE%"

if not defined PYCMD (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYCMD set "PYCMD=%%~fP"
  )
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
  where py >nul 2>nul && (
    py -3 --version >nul 2>nul && set "PYCMD=py -3"
  )
)

if not defined PYCMD (
  echo [!DATE! !TIME!] ERROR: No Python interpreter found. Please install Python 3 or ensure PATH/Conda is active.
  goto :eof
)

set "PYRUN=%PYCMD%"
echo [!DATE! !TIME!] Using Python: %PYRUN%

echo [!DATE! !TIME!] Ensuring pip is available...
%PYRUN% -m pip --version || %PYRUN% -m ensurepip --upgrade

echo [!DATE! !TIME!] Installing required packages: pywinauto pyperclip pandas
%PYRUN% -m pip install --upgrade --disable-pip-version-check --no-color pywinauto pyperclip pandas
if errorlevel 1 (
  echo [!DATE! !TIME!] Retry install with --user
  %PYRUN% -m pip install --upgrade --disable-pip-version-check --no-color --user pywinauto pyperclip pandas
)

echo [!DATE! !TIME!] Requirement installation complete.

endlocal
