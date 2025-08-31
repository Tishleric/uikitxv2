@echo on
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

set "PYCMD=python"
where python >nul 2>nul || set "PYCMD=py -3"

echo Running: %PYCMD% -X utf8 pm_runner_playwright.py
%PYCMD% -X utf8 pm_runner_playwright.py

echo.
echo Exited. Press any key to close.
pause >nul

endlocal
