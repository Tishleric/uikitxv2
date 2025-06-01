# Backup Manifest

**Created**: January 31, 2025
**Purpose**: Backup of old file structure before cleanup following successful reorganization

## Files Backed Up

### From src/ (entire directory moved)
- `src/components/` - Original UI component files
- `src/core/` - Original core classes and protocols
- `src/decorators/` - Original decorator implementations
- `src/lumberjack/` - Original logging configuration
- `src/utils/` - Original utility files
- `src/PricingMonkey/` - Original PM modules

### From ActantEOD/
- `data_service.py` → Migrated to `lib/trading/actant/eod/data_service.py`
- `file_manager.py` → Migrated to `lib/trading/actant/eod/file_manager.py`
- `pricing_monkey_processor.py` → Migrated to `lib/trading/pricing_monkey/processors/processor.py`
- `pricing_monkey_retrieval.py` → Migrated to `lib/trading/pricing_monkey/retrieval/retrieval.py`

### From TTRestAPI/
- `tt_utils.py` → Migrated to `lib/trading/tt_api/utils.py`
- `token_manager.py` → Migrated to `lib/trading/tt_api/token_manager.py`
- `tt_config.py` → Migrated to `lib/trading/tt_api/config.py`

## Files NOT Backed Up (Still in Use)
- `ActantEOD/dashboard_eod.py` - Still the active dashboard
- `ActantEOD/*.json`, `*.csv`, `*.db` - Data files still needed
- `TTRestAPI/examples/` - Example files still useful
- `TTRestAPI/*.json` - Response examples and tokens still useful

## Restoration Instructions

If you need to restore the old structure:

1. Move `_backup_old_structure/src/` back to project root
2. Copy ActantEOD files back from `_backup_old_structure/ActantEOD/`
3. Copy TTRestAPI files back from `_backup_old_structure/TTRestAPI/`
4. Remove or rename the `lib/` directory
5. Remove or rename the `apps/` directory
6. Uninstall the package: `pip uninstall uikitxv2`
7. Update imports in dashboard_eod.py back to old style

## Migration Summary

The reorganization successfully:
- Created proper Python package structure in `lib/`
- Organized code by domain (components, monitoring, trading)
- Fixed import inconsistencies
- Maintained 100% backward compatibility
- Dashboard runs from both old and new locations 