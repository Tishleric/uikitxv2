@echo off
setlocal

:: ============================================================================
:: run_full_pipeline.bat
:: ---------------------
:: Starts the complete, decoupled spot risk processing pipeline.
::
:: This script will:
:: 1. Define a shared log file for this run, timestamped for uniqueness.
:: 2. Start the two "consumer" services (Price Updater and Positions Aggregator)
::    in new, separate terminal windows. Their output will be logged.
:: 3. Start the main "producer" service (Spot Risk Watcher) in the current
::    window, also logging its output.
::
:: To use:
:: 1. Run this script. Three terminal windows will open.
:: 2. Drop your formatted spot risk chunk files into the input directory.
:: 3. Observe the logs in the consolidated log file.
:: 4. To stop all services, simply press Ctrl+C in this main window.
:: ============================================================================

echo.
echo  -- Preparing to Launch Spot Risk Pipeline --
echo.

:: 1. Set up a shared, timestamped log file for this entire run
set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOG_FILE=logs\pipeline_run_%TIMESTAMP%.log"

echo  Log file for this session will be: %LOG_FILE%
echo  Creating logs directory if it doesn't exist...
if not exist "logs" mkdir "logs"
echo.

:: 2. Start the Consumer Services in the background (new windows)
:: We use `start "Title" ...` to run them in parallel without blocking.
:: `>>` appends both stdout and stderr to our shared log file.

echo  Starting Price Updater Service in a new window...
start "Price Updater Service" cmd /c "python run_price_updater_service.py >> %LOG_FILE% 2>&1"

echo  Starting Positions Aggregator Service in a new window...
start "Positions Aggregator Service" cmd /c "python run_positions_aggregator_service.py >> %LOG_FILE% 2>&1"

echo.
echo  Waiting for 5 seconds for consumer services to initialize...
timeout /t 5 /nobreak > nul

:: 3. Start the Producer Service in the foreground
:: This keeps the main script alive. Closing this window will terminate the script.
echo.
echo  -- Starting Spot Risk Watcher (Producer) in this window --
echo  -- Press Ctrl+C in THIS window to stop all services --
echo.
python run_spot_risk_watcher.py >> %LOG_FILE% 2>&1

endlocal 