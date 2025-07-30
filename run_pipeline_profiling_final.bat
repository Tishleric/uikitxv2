@echo off
setlocal

:: ============================================================================
:: run_pipeline_profiling_final.bat
:: ---------------------------------
:: Runs the pipeline with cProfile enabled in the monitor decorator.
::
:: The profiling data will be stored in the observatory database and can be
:: viewed in the Observatory dashboard.
:: ============================================================================

echo.
echo  -- Launching Spot Risk Pipeline with Profiling Enabled --
echo.
echo  Profiling data will be stored in logs/observatory.db
echo.

:: Set environment variable to enable profiling
set MONITOR_PROFILING=1

:: Start the two consumer services in new windows
start "CONSUMER 1 - Price Updater (PROFILED)" cmd /k "set MONITOR_PROFILING=1 && python run_price_updater_service.py"
start "CONSUMER 2 - Positions Aggregator (PROFILED)" cmd /k "set MONITOR_PROFILING=1 && python run_positions_aggregator_service.py"

:: Wait for consumers to start
echo  Waiting for 5 seconds for consumer services to start...
timeout /t 5 /nobreak > nul

:: Start the producer service in a new window
start "PRODUCER - Spot Risk Watcher (PROFILED)" cmd /k "set MONITOR_PROFILING=1 && python run_spot_risk_watcher.py"

echo.
echo  All services started with profiling enabled.
echo  Check logs/observatory.db for profiling results.
echo.

endlocal 