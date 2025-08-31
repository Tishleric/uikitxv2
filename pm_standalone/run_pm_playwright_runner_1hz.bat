@echo on
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

set "PYCMD=python"
where python >nul 2>nul || set "PYCMD=py -3"

echo Running: %PYCMD% -X utf8 pm_runner_playwright_1hz.py
%PYCMD% -X utf8 pm_runner_playwright_1hz.py

echo.

echo Exited 1Hz runner. Press any key to close.
pause >nul

endlocal