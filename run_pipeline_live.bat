@echo off
setlocal

:: =============================================================================
:: Unified Pipeline Live Startup
:: =============================================================================
:: This script starts all necessary services for the real-time spot risk
:: and P&L processing pipeline.
::
:: It replaces older scripts by launching the correct, modern services
:: that use Redis for communication and in-memory caching for performance.
::
:: Each service will open in its own console window for live log monitoring.
:: =============================================================================

echo =================================================
echo  Unified Pipeline Live Startup
echo =================================================
echo.

:: Ensure we are in the project root directory
cd /d "%~dp0"
echo Running from: %CD%
echo.

echo [Step 1 of 3] Starting Consumer Services...
echo -------------------------------------------------
echo.
echo  > Starting Price Updater Service (Consumer 1)
echo    - Listens for new prices from spot risk files.
echo    - Updates the 'market_prices' table in trades.db.
start "Price Updater" cmd /k "python run_price_updater_service.py"

timeout /t 3 >nul

echo.
echo  > Starting Positions Aggregator Service (Consumer 2)
echo    - Maintains an in-memory cache of all positions.
echo    - Listens for new Greek data (via Arrow/Redis).
echo    - Listens for trade changes (via Redis signal).
echo    - Updates the master 'positions' table in trades.db.
start "Positions Aggregator" cmd /k "python run_positions_aggregator_service.py"

echo.
echo  > Starting SOD Roll Service (Consumer 3)
echo    - Rolls latest close -> sodTod at ~5:00 PM Chicago time.
echo    - Publishes 'positions:changed' to refresh positions view.
start "SOD Roll Service" cmd /k "python scripts\run_sod_roll_service.py"

echo.
echo All consumer services started. Waiting 5 seconds for them to initialize...
timeout /t 5 >nul
echo.


echo [Step 2 of 3] Starting Notifier Services...
echo -------------------------------------------------
echo.
echo  > Starting Trade Ledger Watcher (Notifier 1)
echo    - Monitors for new trade files.
echo    - Processes trades into the FIFO/LIFO engine.
echo    - Publishes 'positions:changed' signal to Redis.
start "Trade Ledger Watcher" cmd /k "python scripts\run_trade_ledger_watcher.py --debug"

timeout /t 3 >nul

echo.
echo  > Starting Close Price Watcher (Notifier 2)
echo    - Monitors external directories for daily close prices.
echo    - Updates 'close_price' in the 'market_prices' table.
start "Close Price Watcher" cmd /k "python scripts\run_close_price_watcher.py"
echo.

echo All notifier services started.
timeout /t 3 >nul
echo.

echo [Step 3 of 3] Starting Producer Service...
echo -------------------------------------------------
echo.
echo  > Starting Spot Risk Watcher (Producer)
echo    - Monitors for new spot risk CSV chunks.
echo    - Dispatches calculation jobs to a parallel worker pool.
echo    - Publishes results (prices and Greeks) to Redis using Apache Arrow.
start "Spot Risk Watcher" cmd /k "python run_spot_risk_watcher.py --debug"
echo.

echo Starting Actant Spot Risk Archiver (Independent Service)
echo    - Mirrors/moves files to HistoricalMarketData hourly to keep source light.
echo    - See docs\archiver_service_windows_setup.md for service install details.
start "Spot Risk Archiver" cmd /k "python scripts\run_actant_spot_risk_archiver.py --config configs\actant_spot_risk_archiver.yaml"
echo.

echo =================================================
echo  All Pipeline Services Started Successfully!
echo =================================================
echo.
echo - Each service is running in a separate, visible command window.
echo - To stop the entire pipeline, simply close all spawned windows.
echo.

endlocal
pause
