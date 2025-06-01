# Transition Backup State
**Date**: May 31, 2025
**Purpose**: Document current state before completing the package transition

## Directories to be migrated:
1. **ActantEOD/** - Contains original dashboard and data processing
2. **ActantSOD/** - Contains SOD processing modules
3. **ladderTest/** - Contains ladder applications
4. **dashboard/** - Legacy main dashboard
5. **demo/** - Demo application

## Current Working State:
- ActantEOD dashboard works from both locations:
  - Original: `ActantEOD/dashboard_eod.py`
  - New: `apps/dashboards/actant_eod/app.py`
- Data is read from `Z:\ActantEOD` (network drive)
- Database created in current working directory

## Files that must be preserved:
- All JSON files in network drive (Z:\ActantEOD)
- actant_eod_data.db (SQLite database)
- Configuration files in TTRestAPI/
- Test data in ladderTest/

## Critical functionality to maintain:
1. Dashboard UI must remain unchanged
2. Data loading from Z: drive must continue
3. All imports must be updated correctly
4. Entry points must work 