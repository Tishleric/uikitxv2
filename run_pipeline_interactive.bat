@echo off
setlocal

:: ============================================================================
:: run_pipeline_interactive.bat
:: ----------------------------
:: Starts the complete spot risk pipeline in INTERACTIVE mode.
::
:: This script will:
:: 1. Open three separate, visible command prompt windows.
:: 2. Run each of the three core services in its own window.
:: 3. Title each window descriptively (e.g., "PRODUCER - Spot Risk Watcher").
::
:: This is the RECOMMENDED script for testing and debugging, as it allows
:: you to see the live log output of each service in real-time.
::
:: To use:
:: 1. Run this script.
:: 2. Arrange the three new terminal windows on your screen.
:: 3. Drop spot risk chunk files into the input directory.
:: 4. Observe the live output in each window.
:: 5. To stop all services, you must close each of the three windows manually.
:: ============================================================================

echo.
echo  -- Launching Spot Risk Pipeline in 3 Separate Windows --
echo.
echo  Window 1: Price Updater (Consumer)
echo  Window 2: Positions Aggregator (Consumer)
echo  Window 3: Spot Risk Watcher (Producer)
echo.
echo  Please arrange the new windows on your screen for monitoring.
echo  Close each window manually to stop the services.
echo.

:: Start the two consumer services in new, parallel windows.
:: The "start" command with a title creates a new window.
start "CONSUMER 1 - Price Updater" cmd /k "python run_price_updater_service.py"
start "CONSUMER 2 - Positions Aggregator" cmd /k "python run_positions_aggregator_service.py"

:: Add a small delay to ensure the consumers have time to initialize and subscribe
echo  Waiting for 5 seconds for consumer services to start...
timeout /t 5 /nobreak > nul

:: Start the producer service in a new window as well.
start "PRODUCER - Spot Risk Watcher" cmd /k "python run_spot_risk_watcher.py"

endlocal 