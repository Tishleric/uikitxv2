@echo off
setlocal

:: ============================================================================
:: run_pipeline_profiling.bat (FINAL)
:: ----------------------------------
:: Starts the pipeline with the producer under a robust Python profiler.
::
:: To use:
:: 1. Run this script. Two new windows will open for the consumers.
:: 2. This window will now run the producer via the profiling script.
:: 3. Drop your batch of files into the input directory.
:: 4. After the batch is processed, close THIS main window.
:: 5. A file named 'producer_profile_stats.prof' will be created.
:: ============================================================================

echo.
echo  -- Launching Spot Risk Pipeline for Performance Profiling --
echo.
echo  Starting Consumers in new windows...
echo  The Producer will run in THIS window under the Python profiler.
echo.

:: Start the two consumer services in new, parallel windows.
start "CONSUMER 1 - Price Updater" cmd /k "python run_price_updater_service.py"
start "CONSUMER 2 - Positions Aggregator" cmd /k "python run_positions_aggregator_service.py"

:: Add a small delay
echo  Waiting for 5 seconds for consumer services to start...
timeout /t 5 /nobreak > nul

:: Run the dedicated profiling script in this window
echo.
echo  -- Starting PRODUCER Profiler --
echo  -- Close THIS window when you are done testing to save profile stats --
echo.
python profile_watcher.py

endlocal 