@echo off
setlocal

cd /d "%~dp0"
echo ==============================================
echo  Manual SOD Roll - Dry Run
echo ==============================================
echo.
python scripts\diagnostics\manual_sod_roll_now.py --db trades.db

echo.
set /p RUNNOW=Apply changes now? (yes/no): 
if /I not "%RUNNOW%"=="yes" goto :eof

echo.
echo Creating backup copy of trades.db ...
set TS=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TS=%TS: =0%
copy /Y trades.db trades_backup_%TS%.db >nul
echo Backup created: trades_backup_%TS%.db

echo.
echo ==============================================
echo  Manual SOD Roll - EXECUTE
echo ==============================================
python scripts\diagnostics\manual_sod_roll_now.py --db trades.db --execute

echo.
echo Done.

endlocal

