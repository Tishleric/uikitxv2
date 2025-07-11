# Active Context (Current Focus)

## Current Goal
Supporting daily subfolder structure for Spot Risk file watchdog and dashboard.

## Recent Changes

### File Watcher Updates (COMPLETED)
1. **`lib/trading/actant/spot_risk/file_watcher.py`**:
   - Added `get_spot_risk_date_folder()` - determines date folder based on 3pm EST boundaries
   - Added `ensure_date_folder()` - creates date folders as needed
   - Updated `_process_file_event()` to handle files in date subfolders
   - Updated `_process_csv_file()` to maintain folder structure in output
   - Updated `SpotRiskWatcher.start()` to watch recursively
   - Updated `_process_existing_files()` to handle subfolder structure

2. **Support Scripts Created**:
   - `tests/actant_spot_risk/test_file_watcher_subfolders.py` - tests for date folder functionality
   - `examples/spot_risk_watcher_example.py` - example usage with daily subfolders
   - `scripts/spot_risk_migrate_to_daily_folders.py` - migration script for existing files

### Spot Risk Tab Updates (COMPLETED)
1. **`apps/dashboards/spot_risk/controller.py`**:
   - Added `_get_latest_date_folder()` - finds the most recent YYYY-MM-DD folder
   - Updated `_get_csv_directories()` to check date folders first, then root (backward compatible)
   - Updated `discover_csv_files()` to use recursive search with `rglob()`

## Next Steps
- Test the updated file watcher with actual files in date folders
- Verify the Spot Risk dashboard loads data from the latest date folder
- Monitor for any edge cases or issues during live operation

## Folder Structure
```
data/
├── input/
│   └── actant_spot_risk/
│       ├── 2025-01-14/     # Files from 3pm Jan 13 to 3pm Jan 14 EST
│       │   └── bav_analysis_*.csv
│       └── 2025-01-15/     # Files from 3pm Jan 14 to 3pm Jan 15 EST
│           └── bav_analysis_*.csv
└── output/
    └── spot_risk/
        ├── 2025-01-14/     # Processed files maintain date structure
        │   └── bav_analysis_processed_*.csv
        └── 2025-01-15/
            └── bav_analysis_processed_*.csv
```

## Key Design Decisions
- Files placed in root directories are ignored (as requested)
- Output folder structure mirrors input folder structure
- Backward compatibility maintained - still checks root directories
- Uses 3pm EST as the daily boundary
- Latest date folder is automatically selected for dashboard display