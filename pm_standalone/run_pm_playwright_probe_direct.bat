@echo on
setlocal

cd /d "%~dp0"

set "PYCMD=python"
where python >nul 2>nul || set "PYCMD=py -3"

echo Running: %PYCMD% -X utf8 pm_playwright_probe.py
%PYCMD% -X utf8 pm_playwright_probe.py

echo.
echo Done. Press any key to close.
pause >nul

endlocal
