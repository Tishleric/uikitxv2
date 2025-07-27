# PnL Removal Manifest

## Metadata
- **Start Date**: 2025-07-25 14:17:13
- **Rollback Tag**: pre-pnl-removal-20250725-141713
- **Strategy**: Clean slate removal (pre-production system)

## Removed Component Log
| Timestamp | Component | Location | Reason | Commit Hash |
|-----------|-----------|----------|--------|-------------|
| 2025-07-25 14:21:00 | PnL Dashboard | apps/dashboards/pnl/ | Complete removal | [pending] |
| 2025-07-25 14:21:30 | PnL V2 Dashboard | apps/dashboards/pnl_v2/ | Complete removal | [pending] |
| 2025-07-25 14:22:00 | Main Dashboard PnL | apps/dashboards/main/app.py | Removed PnL references | [pending] |
| 2025-07-25 14:25:00 | PnL Scripts | scripts/*pnl*.py (29 files) | Complete removal | [pending] |
| 2025-07-25 14:25:30 | TYU5 Scripts | scripts/*tyu5*.py (23 files) | Complete removal | [pending] |
| 2025-07-25 14:26:00 | PnL-dependent Scripts | scripts/* (24 files) | Used PnL classes | [pending] |
| 2025-07-25 14:28:00 | Test Directories | tests/pnl_integration/, tests/fullpnl/, tests/actant_pnl/ | Complete removal | [pending] |
| 2025-07-25 14:28:30 | Trading Tests | tests/trading/pnl_calculator/, test_tyu5_*.py, test_unified_*.py | Complete removal | [pending] |
| 2025-07-25 14:30:00 | UnifiedPnLService | lib/trading/pnl_calculator/unified_service.py | Service layer removal | [pending] |
| 2025-07-25 14:30:10 | PnLService | lib/trading/pnl_calculator/service.py | Service layer removal | [pending] |
| 2025-07-25 14:30:20 | UnifiedPnLAPI | lib/trading/pnl_integration/unified_pnl_api.py | Service layer removal | [pending] |
| 2025-07-25 14:30:30 | Controller | lib/trading/pnl_calculator/controller.py | Depends on services | [pending] |
| 2025-07-25 14:30:40 | DataAggregator | lib/trading/pnl_calculator/data_aggregator.py | Depends on services | [pending] |
| 2025-07-25 14:32:00 | TYU5 PnL System | lib/trading/pnl/ | Complete directory removal | [pending] |
| 2025-07-25 14:32:30 | PnL Calculator Files | lib/trading/pnl_calculator/* (12 files) | Calculation engines | [pending] |
| 2025-07-25 14:33:00 | PnL Integration Files | lib/trading/pnl_integration/* (19 files) | TYU5 and integration | [pending] |
| 2025-07-25 14:33:30 | FULLPNL Directory | lib/trading/fullpnl/ | Complete removal | [pending] |
| 2025-07-25 14:35:00 | Database Tables | All PnL tables (26 tables) | Dropped all PnL tables | [pending] |
| 2025-07-25 14:35:30 | PnL Database | data/output/pnl/pnl_tracker.db | Complete removal | [pending] |
| 2025-07-25 14:36:00 | PnL Output Directory | data/output/pnl/ | All output files removed | [pending] |
| 2025-07-25 14:38:00 | TradePreprocessor | lib/trading/pnl_calculator/trade_preprocessor.py | Converted to skeleton | [pending] |
| 2025-07-25 14:39:00 | PnL Pipeline Watcher | lib/trading/pnl_integration/pnl_pipeline_watcher.py | Converted to skeleton | [pending] |

## Preserved Components
| Component | Location | Modification Plan |
|-----------|----------|------------------|
| File Watchers | lib/trading/pnl_calculator/trade_preprocessor.py | ✓ Stripped PnL logic, kept file detection |
| File Watchers | lib/trading/pnl_integration/pnl_pipeline_watcher.py | ✓ Converted to skeleton |
| File Watchers | lib/trading/market_prices/file_monitor.py | Keep for price updates |
| File Watchers | lib/trading/actant/spot_risk/file_watcher.py | Keep for spot risk |

## Database Backup Location
- **Backup Directory**: backups/pre-removal-20250725/
- **Files Backed Up**: 
  - pnl_tracker.db
  - market_prices.db
  - spot_risk.db
  - pnl_tracker_schema.sql

## Removal Stages

### Stage 1: Peripheral Code (Safe Removals)
- [x] Dashboard code (pnl/, pnl_v2/)
- [x] Standalone scripts
- [x] Test files

### Stage 2: Service Layer
- [x] UnifiedPnLService
- [x] PnLService
- [x] UnifiedPnLAPI

### Stage 3: Calculation Engines
- [x] lib/trading/pnl_calculator/
- [x] lib/trading/pnl/

### Stage 4: Database Cleanup
- [x] Drop all PnL tables
- [x] Remove database files

### Stage 5: File Watcher Modification
- [x] Convert to minimal skeletons
- [x] Remove all PnL processing logic 