@echo off
setlocal

cd /d "%~dp0"
echo Running SOD roll verification...
echo.

python scripts\diagnostics\verify_sod_roll.py --db trades.db | more

echo.
echo Done.

endlocal

