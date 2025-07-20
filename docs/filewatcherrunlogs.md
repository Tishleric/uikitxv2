
PS Z:\uikitxv2> python scripts\run_corrected_market_price_monitor.py
Z:\uikitxv2\scripts\run_corrected_market_price_monitor.py:3: SyntaxWarning: invalid escape sequence '\T'
  Corrected market price monitor that watches Z:\Trade_Control directories.
2025-07-20 19:07:37,884 - __main__ - INFO - ============================================================
2025-07-20 19:07:37,885 - __main__ - INFO - CORRECTED MARKET PRICE FILE MONITOR
2025-07-20 19:07:37,885 - __main__ - INFO - ============================================================
2025-07-20 19:07:37,885 - __main__ - INFO - Monitoring directories:
2025-07-20 19:07:37,885 - __main__ - INFO -   - Z:\Trade_Control\Futures
2025-07-20 19:07:37,885 - __main__ - INFO -   - Z:\Trade_Control\Options
2025-07-20 19:07:37,886 - __main__ - INFO -   - data\input\actant_spot_risk (recursive)
2025-07-20 19:07:37,886 - __main__ - INFO -
2025-07-20 19:07:37,886 - __main__ - INFO - Processing windows:
2025-07-20 19:07:37,886 - __main__ - INFO -   - Spot Risk: Updates Current_Price (continuous)
2025-07-20 19:07:37,886 - __main__ - INFO -   - 2:00 PM CDT: Updates Flash_Close (current prices)
2025-07-20 19:07:37,886 - __main__ - INFO -   - 4:00 PM CDT: Updates prior_close (settlement prices)
2025-07-20 19:07:37,886 - __main__ - INFO -   - 3:00 PM files are ignored
2025-07-20 19:07:37,886 - __main__ - INFO -
2025-07-20 19:07:37,886 - __main__ - INFO - TYU5 P&L auto-calculation: DISABLED
2025-07-20 19:07:37,886 - __main__ - INFO - Press Ctrl+C to stop...
2025-07-20 19:07:37,886 - __main__ - INFO - ============================================================
2025-07-20 19:07:37,886 - __main__ - INFO -
Processing existing files...
2025-07-20 19:07:37,925 - lib.trading.market_prices.storage - INFO - Database initialized at Z:\uikitxv2\data\output\market_prices\market_prices.db
[MONITOR] lib.trading.market_prices.storage._init_database executed in 24.199ms
2025-07-20 19:07:39,199 - __main__ - INFO - Found 12 existing futures files
2025-07-20 19:07:39,199 - __main__ - INFO - Processing existing futures file: Futures_20250717_1400.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 6.964ms
2025-07-20 19:07:39,219 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,220 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250717_1400.csv
2025-07-20 19:07:39,220 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,220 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-17 14:00:00-05:00
2025-07-20 19:07:39,220 - lib.trading.market_prices.futures_processor - INFO - Window type: 2pm
2025-07-20 19:07:39,220 - lib.trading.market_prices.futures_processor - INFO - Action: update_flash
2025-07-20 19:07:39,235 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 63.555ms
2025-07-20 19:07:39,305 - lib.trading.market_prices.futures_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-17
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 32.703ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.601ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 18.347ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 18.491ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 17.725ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.920ms
2025-07-20 19:07:39,453 - lib.trading.market_prices.futures_processor - INFO - 2pm processing complete: 5 prices updated, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_2pm_file executed in 147.710ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 17.228ms
2025-07-20 19:07:39,479 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250717_1400.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 279.913ms
2025-07-20 19:07:39,481 - __main__ - INFO - Processing existing futures file: Futures_20250717_1500.csv
2025-07-20 19:07:39,481 - lib.trading.market_prices.futures_processor - WARNING - Skipping file Futures_20250717_1500.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 0.155ms
2025-07-20 19:07:39,482 - __main__ - INFO - Processing existing futures file: Futures_20250717_1600.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 4.184ms
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250717_1600.csv
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-17 16:00:00-05:00
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - Window type: 4pm
2025-07-20 19:07:39,489 - lib.trading.market_prices.futures_processor - INFO - Action: insert_next_day
2025-07-20 19:07:39,493 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 23.745ms
2025-07-20 19:07:39,520 - lib.trading.market_prices.futures_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-18
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 17.106ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 18.370ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 21.376ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.757ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 18.253ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.323ms
2025-07-20 19:07:39,650 - lib.trading.market_prices.futures_processor - INFO - 4pm processing complete: 5 prior closes inserted, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_4pm_file executed in 129.922ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 16.202ms
2025-07-20 19:07:39,672 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250717_1600.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 190.322ms
2025-07-20 19:07:39,674 - __main__ - INFO - Processing existing futures file: Futures_20250718_1104.csv
2025-07-20 19:07:39,674 - lib.trading.market_prices.futures_processor - WARNING - Skipping file Futures_20250718_1104.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 0.199ms
2025-07-20 19:07:39,675 - __main__ - INFO - Processing existing futures file: Futures_20250718_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.126ms
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250718_1404.csv
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-18 14:04:00-05:00
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - Window type: 2pm
2025-07-20 19:07:39,680 - lib.trading.market_prices.futures_processor - INFO - Action: update_flash
2025-07-20 19:07:39,683 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 16.523ms
2025-07-20 19:07:39,703 - lib.trading.market_prices.futures_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-18
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.773ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.301ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.208ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.423ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.290ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.400ms
2025-07-20 19:07:39,822 - lib.trading.market_prices.futures_processor - INFO - 2pm processing complete: 5 prices updated, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_2pm_file executed in 119.454ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 16.003ms
2025-07-20 19:07:39,843 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250718_1404.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 168.439ms
2025-07-20 19:07:39,844 - __main__ - INFO - Processing existing futures file: Futures_20250718_1500.csv
2025-07-20 19:07:39,845 - lib.trading.market_prices.futures_processor - WARNING - Skipping file Futures_20250718_1500.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 0.146ms
2025-07-20 19:07:39,846 - __main__ - INFO - Processing existing futures file: Futures_20250718_1601.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.683ms
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250718_1601.csv
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-18 16:01:00-05:00
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - Window type: 4pm
2025-07-20 19:07:39,851 - lib.trading.market_prices.futures_processor - INFO - Action: insert_next_day
2025-07-20 19:07:39,855 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 16.947ms
2025-07-20 19:07:39,875 - lib.trading.market_prices.futures_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-19
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 18.227ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 17.158ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 17.043ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.700ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.359ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.862ms
2025-07-20 19:07:39,997 - lib.trading.market_prices.futures_processor - INFO - 4pm processing complete: 5 prior closes inserted, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_4pm_file executed in 122.575ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 14.989ms
2025-07-20 19:07:40,018 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250718_1601.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 172.281ms
2025-07-20 19:07:40,020 - __main__ - INFO - Processing existing futures file: Futures_20250718_1851.csv
2025-07-20 19:07:40,020 - lib.trading.market_prices.futures_processor - WARNING - Skipping file Futures_20250718_1851.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 0.208ms
2025-07-20 19:07:40,021 - __main__ - INFO - Processing existing futures file: Futures_20250719_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.286ms
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250719_1404.csv
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-19 14:04:00-05:00
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - Window type: 2pm
2025-07-20 19:07:40,027 - lib.trading.market_prices.futures_processor - INFO - Action: update_flash
2025-07-20 19:07:40,031 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.882ms
2025-07-20 19:07:40,052 - lib.trading.market_prices.futures_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-19
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 18.771ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.702ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.773ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.249ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 19.444ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.917ms
2025-07-20 19:07:40,175 - lib.trading.market_prices.futures_processor - INFO - 2pm processing complete: 5 prices updated, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_2pm_file executed in 123.565ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 16.260ms
2025-07-20 19:07:40,197 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250719_1404.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 176.164ms
2025-07-20 19:07:40,198 - __main__ - INFO - Processing existing futures file: Futures_20250719_1601.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.683ms
2025-07-20 19:07:40,203 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,203 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250719_1601.csv
2025-07-20 19:07:40,203 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,204 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-19 16:01:00-05:00
2025-07-20 19:07:40,204 - lib.trading.market_prices.futures_processor - INFO - Window type: 4pm
2025-07-20 19:07:40,204 - lib.trading.market_prices.futures_processor - INFO - Action: insert_next_day
2025-07-20 19:07:40,208 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.101ms
2025-07-20 19:07:40,228 - lib.trading.market_prices.futures_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-20
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 14.501ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 16.016ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 20.827ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.263ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 16.308ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.606ms
2025-07-20 19:07:40,349 - lib.trading.market_prices.futures_processor - INFO - 4pm processing complete: 5 prior closes inserted, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_4pm_file executed in 121.632ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 13.951ms
2025-07-20 19:07:40,369 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250719_1601.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 170.675ms
2025-07-20 19:07:40,370 - __main__ - INFO - Processing existing futures file: Futures_20250720_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.969ms
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250720_1404.csv
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-20 14:04:00-05:00
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - Window type: 2pm
2025-07-20 19:07:40,377 - lib.trading.market_prices.futures_processor - INFO - Action: update_flash
2025-07-20 19:07:40,381 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.727ms
2025-07-20 19:07:40,403 - lib.trading.market_prices.futures_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-20
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.639ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 14.854ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 15.778ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.012ms
[MONITOR] lib.trading.market_prices.storage.update_futures_flash_close executed in 16.762ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 16.161ms
2025-07-20 19:07:40,523 - lib.trading.market_prices.futures_processor - INFO - 2pm processing complete: 5 prices updated, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_2pm_file executed in 120.563ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 15.503ms
2025-07-20 19:07:40,545 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250720_1404.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 174.521ms
2025-07-20 19:07:40,546 - __main__ - INFO - Processing existing futures file: Futures_20250720_1601.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.946ms
2025-07-20 19:07:40,551 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,552 - lib.trading.market_prices.futures_processor - INFO - FUTURES FILE PROCESSING: Futures_20250720_1601.csv
2025-07-20 19:07:40,552 - lib.trading.market_prices.futures_processor - INFO - ============================================================
2025-07-20 19:07:40,552 - lib.trading.market_prices.futures_processor - INFO - File timestamp: 2025-07-20 16:01:00-05:00
2025-07-20 19:07:40,552 - lib.trading.market_prices.futures_processor - INFO - Window type: 4pm
2025-07-20 19:07:40,552 - lib.trading.market_prices.futures_processor - INFO - Action: insert_next_day
2025-07-20 19:07:40,556 - lib.trading.market_prices.futures_processor - INFO - Loaded 5 rows from CSV
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.911ms
2025-07-20 19:07:40,577 - lib.trading.market_prices.futures_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-21
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 18.582ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.847ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 16.497ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 15.204ms
[MONITOR] lib.trading.market_prices.storage.insert_futures_prior_close executed in 14.265ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.454ms
2025-07-20 19:07:40,693 - lib.trading.market_prices.futures_processor - INFO - 4pm processing complete: 5 prior closes inserted, 0 errors
[MONITOR] lib.trading.market_prices.futures_processor._process_4pm_file executed in 116.420ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 13.615ms
2025-07-20 19:07:40,711 - lib.trading.market_prices.futures_processor - INFO - Successfully processed Futures_20250720_1601.csv
[MONITOR] lib.trading.market_prices.futures_processor.process_file executed in 165.377ms
2025-07-20 19:07:40,714 - __main__ - INFO - Found 12 existing options files
2025-07-20 19:07:40,714 - __main__ - INFO - Processing existing options file: Options_20250717_1400.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.256ms
2025-07-20 19:07:40,723 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:40,723 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250717_1400.csv
2025-07-20 19:07:40,723 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:40,724 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-17 14:00:00-05:00
2025-07-20 19:07:40,724 - lib.trading.market_prices.options_processor - INFO - Window type: 2pm
2025-07-20 19:07:40,724 - lib.trading.market_prices.options_processor - INFO - Action: update_flash
2025-07-20 19:07:40,728 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:07:40,728 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.512ms
2025-07-20 19:07:40,748 - lib.trading.market_prices.options_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-17
2025-07-20 19:07:40,748 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,748 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,748 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,749 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,750 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,751 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,752 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,752 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,752 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,752 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,752 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,753 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 109.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,754 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25C3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:40,755 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TYWN25P3 112.250 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 20.216ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.495ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 20.337ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.936ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 23.096ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.441ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.964ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.587ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.420ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.252ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.886ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.081ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.467ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.980ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.968ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.157ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.687ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 18.401ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.741ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.913ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.640ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.797ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.540ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.173ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.307ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.842ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.358ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.217ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.701ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.557ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.983ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.272ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.996ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.549ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.169ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.153ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.637ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.582ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.740ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.679ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.577ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.283ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.867ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.808ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.981ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.718ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 22.195ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.942ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.222ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.035ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 16.079ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.750ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.068ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.796ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.658ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.996ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.420ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.654ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.232ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.898ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.166ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.262ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.834ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.093ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.960ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.667ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.189ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.274ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.008ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.026ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.013ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.894ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.324ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.721ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.143ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.726ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 30.385ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.562ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.949ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.380ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.070ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.615ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.123ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.010ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.861ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.394ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.388ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.401ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.881ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.772ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.330ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.510ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.582ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.573ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.207ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.534ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.304ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.720ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.760ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.800ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.765ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.818ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.627ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.379ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.714ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.404ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.448ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.160ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.773ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.552ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.700ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.161ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.805ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.699ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.161ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.636ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.291ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.232ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.152ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.750ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.708ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.091ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.730ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.485ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.353ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.331ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.175ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.446ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.084ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.534ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 21.954ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.343ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.336ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.571ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.849ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.095ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.155ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.941ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.737ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.473ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.058ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.034ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.653ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.799ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.322ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.828ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.365ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.687ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.984ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.509ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.090ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.274ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.626ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.065ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.382ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 26.656ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.207ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.809ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.708ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.024ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.946ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.040ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.844ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.255ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.891ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.291ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.872ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.005ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.873ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.455ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.893ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.932ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.081ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.165ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.376ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.374ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.496ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.873ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.915ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.101ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.977ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.291ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.141ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.241ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.136ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.933ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.357ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.149ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.177ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.481ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.461ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.660ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.055ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.477ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.228ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.459ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.980ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.695ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.410ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.818ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.117ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.884ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.754ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.644ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.947ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.581ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.902ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.460ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.901ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.311ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.705ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.089ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.803ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 22.537ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.183ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.751ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.574ms
2025-07-20 19:07:44,936 - lib.trading.market_prices.options_processor - INFO - 2pm processing complete: 196 prices updated, 84 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_2pm_file executed in 4187.940ms
2025-07-20 19:07:44,938 - lib.trading.market_prices.options_processor - ERROR - Failed to process Options_20250717_1400.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 4224.139ms
2025-07-20 19:07:44,940 - __main__ - INFO - Processing existing options file: Options_20250717_1500.csv
2025-07-20 19:07:44,940 - lib.trading.market_prices.options_processor - WARNING - Skipping file Options_20250717_1500.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 0.328ms
2025-07-20 19:07:44,941 - __main__ - INFO - Processing existing options file: Options_20250717_1600.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.328ms
2025-07-20 19:07:44,945 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:44,945 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250717_1600.csv
2025-07-20 19:07:44,946 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:44,946 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-17 16:00:00-05:00
2025-07-20 19:07:44,946 - lib.trading.market_prices.options_processor - INFO - Window type: 4pm
2025-07-20 19:07:44,946 - lib.trading.market_prices.options_processor - INFO - Action: insert_next_day
2025-07-20 19:07:44,950 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:07:44,950 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 19.692ms
2025-07-20 19:07:44,975 - lib.trading.market_prices.options_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-18
2025-07-20 19:07:44,975 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:44,976 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:44,976 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:44,976 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:44,976 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:44,977 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25C2 111.000 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 25.283ms
2025-07-20 19:07:45,006 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,006 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,006 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,006 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,007 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,007 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,007 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 109.250 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.577ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.204ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.764ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.966ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.361ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.626ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.596ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.063ms
2025-07-20 19:07:45,156 - lib.trading.market_prices.options_processor - WARNING - Invalid price for VBYN25P2 110.750 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.220ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.066ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.211ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.224ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.426ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.178ms
2025-07-20 19:07:45,273 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 112.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 112.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 111.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,274 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.750 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.556ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 24.980ms
2025-07-20 19:07:45,331 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.250 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,331 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 110.000 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,331 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.750 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,331 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,332 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25P3 109.250 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.653ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.326ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.334ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.883ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.487ms
2025-07-20 19:07:45,425 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.500 Comdty: #N/A Field Not Applicable
2025-07-20 19:07:45,426 - lib.trading.market_prices.options_processor - WARNING - Invalid price for TJPN25C3 110.750 Comdty: #N/A Field Not Applicable
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.459ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.241ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.180ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.107ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.200ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.488ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.070ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.028ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.542ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.661ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.686ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.589ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.702ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.374ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.830ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.213ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.546ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.412ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.910ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.097ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.616ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.278ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.760ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.725ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.798ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.274ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.502ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.893ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.035ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.815ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.925ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.200ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.883ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.438ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.566ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.544ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.477ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.214ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.917ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.052ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.638ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.627ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.710ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.692ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.958ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.530ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.451ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.147ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.219ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.878ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.226ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.520ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.942ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.931ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.105ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.654ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.350ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.219ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.822ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.477ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.220ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.700ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.845ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.336ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.200ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.923ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.307ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.381ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.741ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.542ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.848ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.202ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.445ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.339ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.319ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.714ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.701ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.980ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.701ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.309ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.899ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.560ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.086ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.020ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.977ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.415ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.659ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.111ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.015ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.236ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.887ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.904ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.205ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.439ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.622ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.847ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.442ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.746ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.634ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.380ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.564ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.443ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.710ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.248ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.255ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.421ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.219ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.454ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.331ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.536ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.354ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 16.010ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.830ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.123ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.818ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.410ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.304ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.950ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.054ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.930ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.509ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.281ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.621ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.695ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.150ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.707ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.485ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.379ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.230ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.594ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.539ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.695ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.945ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.072ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.545ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.851ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.800ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.594ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.384ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.921ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.324ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.206ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.622ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.274ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.294ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.595ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.019ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.209ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.189ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.452ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.412ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.119ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.904ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.278ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.091ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.920ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.263ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.690ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.165ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.141ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.124ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.960ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.526ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.210ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.373ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.237ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.543ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.463ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.691ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.904ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.241ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.825ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.244ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.098ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.082ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.660ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.428ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.674ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.643ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.199ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.901ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.456ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.637ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.445ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.499ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.252ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.475ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.651ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.725ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.861ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.180ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.010ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.147ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.803ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.830ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.558ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.221ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.516ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.836ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.673ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.583ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.379ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.675ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.789ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.904ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.061ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.538ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.291ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.996ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.197ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.898ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.578ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.407ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.598ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.168ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.560ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.174ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.761ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.882ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.068ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.995ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.861ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.581ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.056ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.413ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.516ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.059ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.358ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.519ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.291ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.719ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.493ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.583ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.372ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.282ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.223ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.359ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.823ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.465ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.864ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.166ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.587ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.551ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.678ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.523ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.066ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.240ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.395ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.467ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.739ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.219ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.034ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.975ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.771ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.322ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.477ms
2025-07-20 19:07:50,137 - lib.trading.market_prices.options_processor - INFO - 4pm processing complete: 252 prior closes inserted, 28 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_4pm_file executed in 5162.789ms
2025-07-20 19:07:50,139 - lib.trading.market_prices.options_processor - ERROR - Failed to process Options_20250717_1600.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5198.446ms
2025-07-20 19:07:50,140 - __main__ - INFO - Processing existing options file: Options_20250718_1104.csv
2025-07-20 19:07:50,141 - lib.trading.market_prices.options_processor - WARNING - Skipping file Options_20250718_1104.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 0.211ms
2025-07-20 19:07:50,142 - __main__ - INFO - Processing existing options file: Options_20250718_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.657ms
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250718_1404.csv
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-18 14:04:00-05:00
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - Window type: 2pm
2025-07-20 19:07:50,148 - lib.trading.market_prices.options_processor - INFO - Action: update_flash
2025-07-20 19:07:50,151 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:07:50,152 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 16.598ms
2025-07-20 19:07:50,171 - lib.trading.market_prices.options_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-18
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.530ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.302ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.338ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.957ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.635ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.533ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.954ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.827ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.450ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.860ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.966ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.744ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.602ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.139ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.882ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.582ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.703ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.432ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.261ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.954ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.486ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.401ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.623ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.525ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.103ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.454ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.371ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.057ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.022ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.827ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.663ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.789ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.364ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.244ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.972ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.782ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.678ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.308ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.828ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.032ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.567ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.447ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 20.069ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.022ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.610ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.808ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.335ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.409ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.122ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.537ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.430ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.492ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.505ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.919ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.657ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.245ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.256ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.913ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.059ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.585ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.668ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.680ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.406ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.416ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.089ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.572ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.755ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.020ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.031ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.577ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.044ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.797ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.806ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.964ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.079ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.602ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.270ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.085ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.448ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.509ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.367ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.897ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.716ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.277ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.159ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.660ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.016ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.343ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.397ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.239ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.758ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.544ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.357ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.752ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.196ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.483ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.086ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.204ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 17.117ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.356ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.755ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.318ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.915ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.806ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.620ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.661ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.619ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.351ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.522ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.816ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.063ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.643ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.668ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.860ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.310ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.259ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.535ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.064ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.153ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.032ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.237ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.241ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.339ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.353ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.803ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.814ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.741ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.352ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.587ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.674ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.527ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.150ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.603ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.930ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.239ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.503ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.595ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.842ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.749ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.537ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.509ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.821ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 10.950ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.350ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.581ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.315ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.522ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.764ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.270ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.370ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.296ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.529ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.731ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 10.688ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.072ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.649ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.898ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.877ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.804ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.540ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.114ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.026ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.533ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.298ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.292ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.379ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.026ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.412ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.521ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.193ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.602ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.052ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.668ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.429ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.185ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.985ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.993ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.181ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.574ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.458ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.944ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.519ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.928ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.564ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.879ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.906ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 10.490ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.937ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.936ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.251ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.362ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.205ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.314ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.722ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.980ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.608ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.156ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.027ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.628ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.100ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.849ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.358ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.809ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.510ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.649ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.832ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.784ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.272ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.967ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.846ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.855ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.162ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.180ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.076ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.845ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.641ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.293ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.226ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.397ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.762ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.720ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.609ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.432ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.673ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.999ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.535ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.946ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.720ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.723ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.025ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.038ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.816ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.979ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.085ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.323ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.442ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.471ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.437ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.677ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.512ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.366ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.597ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.389ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.614ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.618ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.796ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.389ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.423ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.426ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.762ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.918ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.913ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.237ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.961ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.472ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.398ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.592ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.347ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.413ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.752ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.542ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.819ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.393ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.500ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.735ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.447ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.441ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.220ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.644ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.847ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.237ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.578ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.648ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.293ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.624ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.412ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.980ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.284ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.094ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.409ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.039ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.036ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.371ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.342ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.252ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.286ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.080ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.319ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.969ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.727ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.011ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.611ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.956ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.351ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.541ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.755ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.224ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.719ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.592ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.633ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.920ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.902ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.555ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.013ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.087ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.171ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.312ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.630ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.481ms
2025-07-20 19:07:55,565 - lib.trading.market_prices.options_processor - INFO - 2pm processing complete: 280 prices updated, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_2pm_file executed in 5393.924ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 12.296ms
2025-07-20 19:07:55,582 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250718_1404.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5440.524ms
2025-07-20 19:07:55,583 - __main__ - INFO - Processing existing options file: Options_20250718_1500.csv
2025-07-20 19:07:55,584 - lib.trading.market_prices.options_processor - WARNING - Skipping file Options_20250718_1500.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 0.174ms
2025-07-20 19:07:55,585 - __main__ - INFO - Processing existing options file: Options_20250718_1601.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.172ms
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250718_1601.csv
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-18 16:01:00-05:00
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - Window type: 4pm
2025-07-20 19:07:55,591 - lib.trading.market_prices.options_processor - INFO - Action: insert_next_day
2025-07-20 19:07:55,595 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:07:55,595 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 15.952ms
2025-07-20 19:07:55,613 - lib.trading.market_prices.options_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-19
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.394ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.807ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.765ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.886ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.734ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.702ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.037ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.183ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.484ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.577ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.806ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.201ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 23.079ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.067ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.629ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.637ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.944ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.433ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.514ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.546ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.745ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.603ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.521ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.763ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.339ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.004ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.979ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.489ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.281ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.433ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 40.664ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.475ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.372ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.039ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.072ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.712ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.273ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.212ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.135ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.101ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.948ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.629ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.365ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.121ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.288ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 39.846ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.619ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.041ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.878ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.909ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.659ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.189ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.748ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.157ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.415ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.791ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.988ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.671ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.679ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.742ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.237ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.705ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.399ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.281ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.921ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.321ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.707ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.670ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.994ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.569ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.978ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.885ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.102ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.348ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.855ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.239ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.241ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.952ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.747ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.504ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.981ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.603ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.866ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.303ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.793ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.028ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.618ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.577ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.896ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.504ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.548ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.552ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.146ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.519ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.488ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.077ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.465ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.819ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.334ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.467ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.538ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.271ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.579ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.189ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.236ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.377ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.998ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.308ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.788ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.166ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.862ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.840ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.461ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.303ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.835ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.804ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.395ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.783ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.673ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.514ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.290ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.715ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.740ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.938ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.297ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.950ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.343ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.739ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.874ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.929ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.350ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.547ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.332ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.175ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 48.107ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.431ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 28.796ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.205ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.202ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.889ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.202ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.823ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 18.112ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.585ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.961ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.637ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.693ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.253ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.366ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.730ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.585ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.165ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.750ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.585ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.677ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.328ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.603ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.511ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.460ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.534ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.852ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.809ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.315ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.159ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.151ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.721ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.015ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.351ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.957ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.026ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.605ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.482ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.014ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.309ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.855ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.243ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.634ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.660ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.624ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.022ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.994ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.130ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.788ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.235ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.552ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.450ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.854ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.482ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.949ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.313ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.703ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.632ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.809ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.079ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.702ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.214ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.571ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.385ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.165ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.812ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.561ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.950ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.593ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.614ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.450ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.308ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.938ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.341ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.805ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.933ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.291ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.077ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.328ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.077ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.666ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.937ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.822ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.194ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.670ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.983ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.325ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.915ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.848ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.525ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.049ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.560ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.221ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.220ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.838ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.138ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.798ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.744ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.611ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.582ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.915ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.640ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.558ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.506ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.185ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 20.045ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.022ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.473ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.785ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.148ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 24.148ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.647ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.183ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.882ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.792ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.455ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.038ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.222ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.309ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.992ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.969ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.600ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.581ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.234ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.778ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.791ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.871ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.549ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.000ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.970ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.822ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.639ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.142ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.462ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.359ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.097ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.114ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.339ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.446ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.027ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.899ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.392ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.093ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.682ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.602ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.223ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.227ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.435ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.628ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.556ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.434ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 16.185ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.590ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.164ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.419ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.622ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.384ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.246ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.517ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.854ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.193ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.622ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.680ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.312ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.809ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.234ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.193ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.387ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.593ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.389ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.261ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.590ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.874ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.130ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.459ms
2025-07-20 19:08:01,504 - lib.trading.market_prices.options_processor - INFO - 4pm processing complete: 280 prior closes inserted, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_4pm_file executed in 5891.294ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 14.698ms
2025-07-20 19:08:01,524 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250718_1601.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5939.108ms
2025-07-20 19:08:01,525 - __main__ - INFO - Processing existing options file: Options_20250718_1851.csv
2025-07-20 19:08:01,525 - lib.trading.market_prices.options_processor - WARNING - Skipping file Options_20250718_1851.csv - invalid timestamp or window
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 0.319ms
2025-07-20 19:08:01,527 - __main__ - INFO - Processing existing options file: Options_20250719_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.809ms
2025-07-20 19:08:01,532 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:01,532 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250719_1404.csv
2025-07-20 19:08:01,532 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:01,533 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-19 14:04:00-05:00
2025-07-20 19:08:01,533 - lib.trading.market_prices.options_processor - INFO - Window type: 2pm
2025-07-20 19:08:01,533 - lib.trading.market_prices.options_processor - INFO - Action: update_flash
2025-07-20 19:08:01,538 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:08:01,538 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 17.080ms
2025-07-20 19:08:01,558 - lib.trading.market_prices.options_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-19
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.524ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.810ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.455ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.856ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.514ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.554ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.031ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.017ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.452ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.717ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.143ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.390ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.571ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.486ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.014ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.428ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.635ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.286ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.447ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.616ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.121ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.623ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.206ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.803ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.555ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.442ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.948ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.380ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.118ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.122ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.464ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.842ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.401ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.786ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.120ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.438ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.742ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.500ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.068ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.162ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.975ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.433ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.429ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.505ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.203ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.293ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.419ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 21.058ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.315ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.474ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.798ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.375ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.152ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.365ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.756ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.352ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.337ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.937ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.312ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.393ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.922ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.671ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.004ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.201ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.846ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.922ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.432ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.190ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.643ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.908ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.189ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.242ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.309ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.106ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.289ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.070ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.588ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.180ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.461ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.531ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.998ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.703ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.128ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.452ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.998ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.354ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.658ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.254ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.669ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.702ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.527ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.530ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.592ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.722ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.260ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.550ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.720ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.682ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.363ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.256ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.126ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.459ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.739ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.206ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.803ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.855ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.842ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.407ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.246ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.602ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.261ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.135ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.447ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.499ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.732ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.327ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.378ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.638ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.560ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.595ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.528ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.783ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.464ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.480ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.589ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.131ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.248ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.014ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.948ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.413ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.715ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.957ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.880ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.390ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.370ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.375ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.360ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.337ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.023ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.437ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.037ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.181ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.222ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.585ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.895ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.389ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.051ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.329ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.551ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.841ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.034ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.244ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.093ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.372ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.812ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.258ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.347ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.703ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.022ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.649ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.135ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.205ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.750ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.212ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.135ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.195ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.204ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.897ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.941ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.652ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.489ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.009ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.428ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.092ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.191ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.688ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.967ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.980ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.421ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.959ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.811ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.045ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.533ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.583ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.128ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.625ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.867ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.151ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.385ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.291ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.692ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.990ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.125ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.478ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.603ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.726ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.295ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.496ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.429ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.823ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.135ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 23.121ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.219ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.416ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.386ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.752ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 22.225ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.763ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.262ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.887ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.236ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.092ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.184ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.463ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.657ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.558ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.323ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.938ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.327ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.336ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.914ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.657ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.049ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.895ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.002ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.751ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.556ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.748ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.373ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.437ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.094ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.916ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.201ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.749ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.225ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.761ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.545ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.123ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.715ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.566ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 10.701ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.845ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.711ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.381ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.545ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.552ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.240ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.817ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.566ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.223ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.939ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.457ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.386ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.724ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.868ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.704ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.586ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.441ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.427ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.040ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.249ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.305ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.139ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.215ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.998ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.578ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.367ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.353ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.625ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.307ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.731ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 19.405ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.701ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.042ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.545ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.070ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.334ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.262ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.782ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.805ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.650ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.091ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.315ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.333ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.838ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.538ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.237ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.120ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.126ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.724ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.285ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.013ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.853ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.359ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.102ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.790ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.239ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.174ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.310ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.426ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.150ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.095ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.188ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.837ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.350ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.811ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.662ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.140ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.407ms
2025-07-20 19:08:07,169 - lib.trading.market_prices.options_processor - INFO - 2pm processing complete: 280 prices updated, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_2pm_file executed in 5610.853ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 12.621ms
2025-07-20 19:08:07,185 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250719_1404.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5658.491ms
2025-07-20 19:08:07,186 - __main__ - INFO - Processing existing options file: Options_20250719_1601.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.399ms
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250719_1601.csv
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-19 16:01:00-05:00
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - Window type: 4pm
2025-07-20 19:08:07,192 - lib.trading.market_prices.options_processor - INFO - Action: insert_next_day
2025-07-20 19:08:07,196 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:08:07,196 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 14.779ms
2025-07-20 19:08:07,213 - lib.trading.market_prices.options_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-20
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.940ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.817ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.162ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.968ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.070ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.690ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.118ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.290ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.628ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.084ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.891ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.787ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.350ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.170ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.463ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.297ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.519ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.639ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.129ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.961ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.019ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.253ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.585ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.703ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.584ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 23.946ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.139ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.403ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.963ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.107ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.710ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.791ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.615ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.296ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.061ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.748ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.727ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.195ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.341ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.476ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.332ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.968ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.949ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.894ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.269ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.716ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.996ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.871ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.948ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.089ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.504ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.060ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.939ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.288ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.450ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.548ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.791ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.841ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.149ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 29.056ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.687ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.812ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.589ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.339ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.323ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.185ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.825ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.521ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.748ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.662ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.734ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.140ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.738ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.400ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.817ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.805ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.006ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.644ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.266ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.452ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.886ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.350ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.194ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.716ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.967ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.815ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.069ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.350ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.379ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.039ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 37.747ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.006ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.133ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.130ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.810ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.160ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.873ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.595ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.527ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.416ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.791ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.666ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.706ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.194ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.674ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.128ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.197ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.915ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.170ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.207ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.811ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.080ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.053ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.670ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.775ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.322ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.019ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.668ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.206ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.463ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 10.918ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.459ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.066ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.952ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.032ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.006ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.140ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.595ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.837ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.344ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.848ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.043ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.338ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.549ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.614ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.237ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.930ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.434ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.634ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.023ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.873ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.055ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.011ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.760ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.838ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.659ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.492ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.195ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.704ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.424ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.643ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.923ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.683ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.186ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.121ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.844ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.070ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.767ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.368ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.045ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.877ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.283ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.492ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 11.519ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.482ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.488ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.595ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.149ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.950ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.112ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.251ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.061ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.858ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.094ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.187ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.307ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.392ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.199ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.915ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.169ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.773ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.925ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.886ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.116ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.413ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.186ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.867ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.270ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.205ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.769ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.247ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.648ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.970ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.829ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.547ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.334ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.674ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.747ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.127ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.705ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.653ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.263ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.658ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.973ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.469ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.746ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.750ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.165ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.783ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.474ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.081ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.827ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.960ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.590ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.495ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.213ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.149ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.394ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.096ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.671ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.797ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.787ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.773ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.499ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.300ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.312ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.354ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.215ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.164ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.750ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 16.011ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.475ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.884ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.034ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.379ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.340ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.988ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.098ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.534ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.454ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.624ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.721ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.954ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.655ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.778ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.154ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.442ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 24.501ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.302ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.754ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.954ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.837ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.653ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.769ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.652ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.516ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.884ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.084ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.320ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.457ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.867ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.758ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.584ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.108ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.281ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.777ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.218ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.098ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.063ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.288ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.864ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.124ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.875ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.000ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.113ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.979ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.212ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.351ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.770ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 20.045ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.850ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.450ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.243ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.700ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.592ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.886ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.470ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.168ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.310ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.046ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.270ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.626ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.395ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.307ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.882ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.491ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.799ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.428ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.846ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.741ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.555ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.392ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.575ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.859ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.992ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.008ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.486ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.748ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.441ms
2025-07-20 19:08:12,961 - lib.trading.market_prices.options_processor - INFO - 4pm processing complete: 280 prior closes inserted, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_4pm_file executed in 5748.647ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 13.040ms
2025-07-20 19:08:12,979 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250719_1601.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5793.190ms
2025-07-20 19:08:12,981 - __main__ - INFO - Processing existing options file: Options_20250720_1404.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 2.538ms
2025-07-20 19:08:12,985 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:12,985 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250720_1404.csv
2025-07-20 19:08:12,985 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:12,985 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-20 14:04:00-05:00
2025-07-20 19:08:12,985 - lib.trading.market_prices.options_processor - INFO - Window type: 2pm
2025-07-20 19:08:12,986 - lib.trading.market_prices.options_processor - INFO - Action: update_flash
2025-07-20 19:08:12,989 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:08:12,989 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 15.133ms
2025-07-20 19:08:13,007 - lib.trading.market_prices.options_processor - INFO - Processing 2pm file: Updating current prices for 2025-07-20
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.036ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.644ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.292ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.948ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.417ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.555ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.845ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.145ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.547ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.117ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.638ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.970ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.638ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.589ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.993ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.921ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.591ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.488ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.041ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.336ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.292ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.318ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.973ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.213ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.043ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.041ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.148ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.334ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.076ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.040ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.488ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.166ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.819ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.620ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.419ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.184ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.636ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.616ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.981ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.514ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.993ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.958ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.565ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.103ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.115ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.387ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.044ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.630ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.628ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.860ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.514ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.944ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.744ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.434ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.336ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.149ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.037ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.687ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.781ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.487ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.248ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.418ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.519ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.199ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.024ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.493ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.080ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.920ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.127ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.345ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.193ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.757ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.938ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.652ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.841ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.994ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.163ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.274ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.952ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.588ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.722ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.288ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.795ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.375ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.775ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.416ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.531ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.611ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.001ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.887ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.580ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.004ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.470ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.876ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.488ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.969ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.064ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.522ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.575ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.615ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.985ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.503ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.291ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.661ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.732ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.282ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.084ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.381ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.646ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.562ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.904ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.230ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.333ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.099ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 11.826ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.336ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.893ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.746ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.062ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.201ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.996ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.942ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.124ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 43.401ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.067ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.743ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.739ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.777ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.687ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.973ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.720ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.558ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.227ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.817ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.253ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.443ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.713ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.695ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.450ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.085ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.429ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.058ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.847ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.452ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.429ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.521ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.165ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.449ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.768ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.605ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.468ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.590ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.358ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.782ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.901ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.665ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.428ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.651ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.131ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.481ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.722ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.633ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.794ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.023ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.492ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.912ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.595ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.635ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.149ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.960ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.138ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.383ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.427ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.356ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.060ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.004ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.423ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.463ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.832ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.689ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.993ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.323ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.234ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.642ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.017ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.687ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.525ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 17.040ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.702ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.773ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.353ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.918ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.618ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.950ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 18.546ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.349ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.750ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.433ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.378ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.746ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.445ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.950ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.812ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.075ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.379ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.276ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.312ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.078ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.167ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.289ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.896ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.467ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.510ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.294ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.460ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.180ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.533ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.099ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.412ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.828ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.191ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.449ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.913ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.009ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.840ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.076ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.630ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.090ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.224ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.291ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.842ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.247ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.991ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.441ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.848ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.287ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.399ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.547ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.074ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.607ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 30.300ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.705ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 20.530ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.478ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.122ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.383ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.180ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.532ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.308ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.821ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.882ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.842ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.905ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.340ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.020ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.886ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.276ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.022ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.663ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.598ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.645ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.673ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.427ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.349ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.676ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.309ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.477ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.757ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.437ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.515ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.720ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.594ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.750ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.213ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.878ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.726ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.891ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.281ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.280ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.214ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.565ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.503ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.514ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.688ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.254ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.155ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.396ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.357ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.000ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.480ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.433ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.318ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.005ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.922ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.052ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.537ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.873ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.447ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.457ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.226ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.777ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.191ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 12.679ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 13.822ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 14.627ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 16.048ms
[MONITOR] lib.trading.market_prices.storage.update_options_flash_close executed in 15.230ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.744ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.768ms
2025-07-20 19:08:18,510 - lib.trading.market_prices.options_processor - INFO - 2pm processing complete: 280 prices updated, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_2pm_file executed in 5503.060ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 15.746ms
2025-07-20 19:08:18,530 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250720_1404.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5549.923ms
2025-07-20 19:08:18,532 - __main__ - INFO - Processing existing options file: Options_20250720_1600.csv
[MONITOR] lib.trading.market_prices.storage.is_file_processed executed in 3.618ms
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - OPTIONS FILE PROCESSING: Options_20250720_1600.csv
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - ============================================================
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - File timestamp: 2025-07-20 16:00:00-05:00
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - Window type: 4pm
2025-07-20 19:08:18,538 - lib.trading.market_prices.options_processor - INFO - Action: insert_next_day
2025-07-20 19:08:18,542 - lib.trading.market_prices.options_processor - INFO - Loaded 280 rows from CSV
2025-07-20 19:08:18,542 - lib.trading.market_prices.options_processor - INFO - Available optional columns: ['EXPIRE_DT', 'MONEYNESS']
[MONITOR] lib.trading.market_prices.storage.record_file_processing executed in 14.745ms
2025-07-20 19:08:18,560 - lib.trading.market_prices.options_processor - INFO - Processing 4pm file: Inserting prior closes for 2025-07-21
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.693ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.223ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.890ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.921ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.423ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.854ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.638ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.818ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.428ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.641ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.602ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.608ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.282ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.949ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.401ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.800ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.223ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.662ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.570ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.919ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.517ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.376ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.630ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.806ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.014ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.246ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.700ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.221ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.246ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.549ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.537ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.992ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.665ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.776ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.191ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.160ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.127ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.556ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.427ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.103ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.776ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.906ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.170ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.756ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.808ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.624ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.055ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.183ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.209ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.178ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.268ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.774ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.217ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.088ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.767ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.095ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.025ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.408ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.482ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.509ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.231ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.977ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.660ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.571ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.615ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.939ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.362ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.090ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.555ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.559ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.836ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.209ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.197ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.371ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.227ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.645ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.788ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.404ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.224ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.668ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.210ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.245ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.484ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.675ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.657ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.158ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.071ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 15.196ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.523ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.933ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.751ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.968ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.347ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.624ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.956ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.484ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.844ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.053ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.102ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.620ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.118ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.606ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.442ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.246ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.881ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.091ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.361ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.151ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.582ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.642ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.022ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.709ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.708ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.855ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.160ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.322ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.437ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.784ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.880ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.973ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 11.954ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.455ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.159ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.331ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.677ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.927ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.412ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.363ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.823ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.316ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.028ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.435ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 19.907ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.765ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.835ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.882ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.486ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.032ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.587ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.741ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.848ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.394ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.331ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.638ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.033ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.217ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.365ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.871ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.780ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.798ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.592ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.378ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.972ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.572ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.377ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.747ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.508ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.558ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.157ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.043ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.667ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.362ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.475ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.732ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.741ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.944ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.430ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.964ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.182ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.993ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.300ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.099ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.094ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.812ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.383ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.006ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.019ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.803ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.702ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.674ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.249ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.970ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.909ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.948ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.474ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.860ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.939ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.708ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.061ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.730ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.075ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.405ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.237ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.193ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.691ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.874ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.493ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.759ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.441ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.938ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.060ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.107ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.928ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.892ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.372ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.183ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 20.138ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.381ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.689ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.779ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.242ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.435ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.885ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.536ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.320ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.883ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.456ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.670ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.765ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.462ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.806ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.612ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.635ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.549ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.181ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.261ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.089ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.097ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.415ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.961ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.386ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.076ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.315ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.136ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.605ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.540ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.217ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.082ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.099ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.749ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.286ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 14.483ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.767ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.533ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.500ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 18.642ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 21.427ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 29.127ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.424ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.615ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.761ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.798ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.940ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.400ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.428ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.738ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.323ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.495ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.263ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.912ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.834ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.285ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.890ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.964ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.965ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.750ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.143ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.298ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.111ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 12.978ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.225ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.642ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.823ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.772ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.289ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.207ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.259ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.832ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.334ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 22.053ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.659ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.756ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.759ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.099ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.871ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.740ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.386ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.227ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.143ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.887ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.872ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.235ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.027ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.062ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.564ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.034ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 13.664ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.025ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.408ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.096ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 14.194ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 15.074ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 13.296ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.554ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.079ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 16.213ms
[MONITOR] lib.trading.market_prices.storage.insert_options_prior_close executed in 17.537ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 12.889ms
[MONITOR] lib.trading.market_prices.storage.update_file_processing_progress executed in 2.583ms
2025-07-20 19:08:24,416 - lib.trading.market_prices.options_processor - INFO - 4pm processing complete: 280 prior closes inserted, 0 errors out of 280 total rows
[MONITOR] lib.trading.market_prices.options_processor._process_4pm_file executed in 5856.482ms
[MONITOR] lib.trading.market_prices.storage.complete_file_processing executed in 14.263ms
2025-07-20 19:08:24,435 - lib.trading.market_prices.options_processor - INFO - Successfully processed Options_20250720_1600.csv
[MONITOR] lib.trading.market_prices.options_processor.process_file executed in 5903.423ms
2025-07-20 19:08:24,440 - __main__ - INFO - Found 7 existing spot risk files
2025-07-20 19:08:24,440 - __main__ - INFO - Processing existing spot risk file: bav_analysis_20250720_171723.csv
2025-07-20 19:08:24,440 - lib.trading.market_prices.spot_risk_price_processor - INFO - Processing spot risk file: bav_analysis_20250720_171723.csv
2025-07-20 19:08:24,444 - lib.trading.market_prices.spot_risk_price_processor - INFO - Loaded 132 rows from bav_analysis_20250720_171723.csv
Failed to parse XCME.ZN.SEP25: Invalid XCME format: XCME.ZN.SEP25
2025-07-20 19:08:24,447 - lib.trading.market_prices.spot_risk_price_processor - INFO - Untranslatable symbol (likely historical): XCME.ZN.SEP25
2025-07-20 19:08:24,447 - lib.trading.market_prices.spot_risk_price_processor - INFO - Extracted 117 valid prices
[MONITOR] lib.trading.market_prices.storage.update_current_prices_options executed in 22.865ms
2025-07-20 19:08:24,476 - lib.trading.market_prices.spot_risk_price_processor - INFO - Updated 117 options prices
[MONITOR] lib.trading.market_prices.spot_risk_price_processor._update_database executed in 29.343ms
2025-07-20 19:08:24,480 - lib.trading.market_prices.spot_risk_price_processor - INFO - Successfully updated 117 prices in database
[MONITOR] lib.trading.market_prices.spot_risk_price_processor.process_file executed in 39.677ms
2025-07-20 19:08:24,481 - __main__ - INFO - Processing existing spot risk file: bav_analysis_20250720_171730.csv
2025-07-20 19:08:24,481 - lib.trading.market_prices.spot_risk_price_processor - INFO - Processing spot risk file: bav_analysis_20250720_171730.csv
2025-07-20 19:08:24,484 - lib.trading.market_prices.spot_risk_price_processor - INFO - Loaded 132 rows from bav_analysis_20250720_171730.csv
Failed to parse XCME.ZN.SEP25: Invalid XCME format: XCME.ZN.SEP25
2025-07-20 19:08:24,488 - lib.trading.market_prices.spot_risk_price_processor - INFO - Untranslatable symbol (likely historical): XCME.ZN.SEP25
2025-07-20 19:08:24,489 - lib.trading.market_prices.spot_risk_price_processor - INFO - Extracted 117 valid prices
[MONITOR] lib.trading.market_prices.storage.update_current_prices_options executed in 25.798ms
2025-07-20 19:08:24,518 - lib.trading.market_prices.spot_risk_price_processor - INFO - Updated 117 options prices
[MONITOR] lib.trading.market_prices.spot_risk_price_processor._update_database executed in 29.502ms
2025-07-20 19:08:24,520 - lib.trading.market_prices.spot_risk_price_processor - INFO - Successfully updated 117 prices in database
[MONITOR] lib.trading.market_prices.spot_risk_price_processor.process_file executed in 39.977ms
2025-07-20 19:08:24,522 - __main__ - INFO - Processing existing spot risk file: bav_analysis_20250720_171737.csv
2025-07-20 19:08:24,522 - lib.trading.market_prices.spot_risk_price_processor - INFO - Processing spot risk file: bav_analysis_20250720_171737.csv
2025-07-20 19:08:24,526 - lib.trading.market_prices.spot_risk_price_processor - INFO - Loaded 132 rows from bav_analysis_20250720_171737.csv
Failed to parse XCME.ZN.SEP25: Invalid XCME format: XCME.ZN.SEP25
2025-07-20 19:08:24,529 - lib.trading.market_prices.spot_risk_price_processor - INFO - Untranslatable symbol (likely historical): XCME.ZN.SEP25
2025-07-20 19:08:24,530 - lib.trading.market_prices.spot_risk_price_processor - INFO - Extracted 117 valid prices
[MONITOR] lib.trading.market_prices.storage.update_current_prices_options executed in 20.085ms
2025-07-20 19:08:24,553 - lib.trading.market_prices.spot_risk_price_processor - INFO - Updated 117 options prices
[MONITOR] lib.trading.market_prices.spot_risk_price_processor._update_database executed in 24.465ms
2025-07-20 19:08:24,567 - lib.trading.market_prices.spot_risk_price_processor - INFO - Successfully updated 117 prices in database
[MONITOR] lib.trading.market_prices.spot_risk_price_processor.process_file executed in 45.128ms
2025-07-20 19:08:24,569 - __main__ - INFO - Processing existing spot risk file: bav_analysis_20250720_171744.csv
2025-07-20 19:08:24,569 - lib.trading.market_prices.spot_risk_price_processor - INFO - Processing spot risk file: bav_analysis_20250720_171744.csv
2025-07-20 19:08:24,573 - lib.trading.market_prices.spot_risk_price_processor - INFO - Loaded 132 rows from bav_analysis_20250720_171744.csv
Failed to parse XCME.ZN.SEP25: Invalid XCME format: XCME.ZN.SEP25
2025-07-20 19:08:24,577 - lib.trading.market_prices.spot_risk_price_processor - INFO - Untranslatable symbol (likely historical): XCME.ZN.SEP25
2025-07-20 19:08:24,577 - lib.trading.market_prices.spot_risk_price_processor - INFO - Extracted 117 valid prices
[MONITOR] lib.trading.market_prices.storage.update_current_prices_options executed in 20.538ms
2025-07-20 19:08:24,601 - lib.trading.market_prices.spot_risk_price_processor - INFO - Updated 117 options prices
[MONITOR] lib.trading.market_prices.spot_risk_price_processor._update_database executed in 24.102ms
2025-07-20 19:08:24,604 - lib.trading.market_prices.spot_risk_price_processor - INFO - Successfully updated 117 prices in database
[MONITOR] lib.trading.market_prices.spot_risk_price_processor.process_file executed in 35.115ms
2025-07-20 19:08:24,605 - __main__ - INFO - Processing existing spot risk file: bav_analysis_20250720_172512.csv
2025-07-20 19:08:24,605 - lib.trading.market_prices.spot_risk_price_processor - INFO - Processing spot risk file: bav_analysis_20250720_172512.csv
2025-07-20 19:08:24,608 - lib.trading.market_prices.spot_risk_price_processor - INFO - Loaded 132 rows from bav_analysis_20250720_172512.csv
Failed to parse XCME.ZN.SEP25: Invalid XCME format: XCME.ZN.SEP25
2025-07-20 19:08:24,612 - lib.trading.market_prices.spot_risk_price_processor - INFO - Untranslatable symbol (likely historical): XCME.ZN.SEP25
2025-07-20 19:08:24,612 - lib.trading.market_prices.spot_risk_price_processor - INFO - Extracted 129 valid prices
[MONITOR] lib.trading.market_prices.storage.update_current_prices_options executed in 22.306ms
2025-07-20 19:08:24,638 - lib.trading.market_prices.spot_risk_price_processor - INFO - Updated 129 options prices
[MONITOR] lib.trading.market_prices.spot_risk_price_processor._update_database executed in 26.079ms
2025-07-20 19:08:24,640 - lib.trading.market_prices.spot_risk_price_processor - INFO - Successfully updated 129 prices in database
[MONITOR] lib.trading.market_prices.spot_risk_price_processor.process_file executed in 35.334ms
2025-07-20 19:08:24,641 - __main__ - INFO - Done processing existing files.

2025-07-20 19:08:24,645 - lib.trading.market_prices.storage - INFO - Database initialized at Z:\uikitxv2\data\output\market_prices\market_prices.db
[MONITOR] lib.trading.market_prices.storage._init_database executed in 2.973ms
2025-07-20 19:08:24,659 - __main__ - INFO - Watching futures directory: Z:\Trade_Control\Futures
2025-07-20 19:08:24,660 - __main__ - INFO - Watching options directory: Z:\Trade_Control\Options
2025-07-20 19:08:24,660 - __main__ - INFO - Watching spot risk directory (recursively): data\input\actant_spot_risk
2025-07-20 19:08:24,664 - __main__ - INFO -
File monitor started. Waiting for new files...
forrtl: error (200): program aborting due to control-C event
Image              PC                Routine            Line        Source
libifcoremd.dll    00007FFCCFD0DF54  Unknown               Unknown  Unknown
KERNELBASE.dll     00007FFD5070B0CD  Unknown               Unknown  Unknown
KERNEL32.DLL       00007FFD5156E8D7  Unknown               Unknown  Unknown
ntdll.dll          00007FFD52F9C34C  Unknown               Unknown  Unknown
PS Z:\uikitxv2>
