# PnL Module Integration Specification

## Overview
This document specifies the integration requirements for a new PnL module to replace the removed legacy systems. The codebase has been cleaned of all existing PnL logic, leaving only minimal file watchers and clean integration points.

## Integration Points

### 1. File Watchers (Skeleton Code Available)

#### Trade File Watcher
- **Location**: `lib/trading/pnl_calculator/trade_preprocessor.py`
- **Class**: `TradeFileWatcher`
- **Purpose**: Monitors `data/input/trade_ledger/` for new trade CSV files
- **Integration Method**: 
  ```python
  from lib.trading.pnl_calculator.trade_preprocessor import TradeFileWatcher, TradeInput
  
  def handle_trades(trades: List[TradeInput], file_path: Path):
      # Your PnL logic here
      pass
  
  watcher = TradeFileWatcher(
      watch_dir="data/input/trade_ledger",
      callback=handle_trades
  )
  watcher.watch()
  ```

#### Pipeline Watcher
- **Location**: `lib/trading/pnl_integration/pnl_pipeline_watcher.py`
- **Class**: `PipelineWatcher`
- **Purpose**: Generic file monitoring with callbacks
- **Integration Method**:
  ```python
  from lib.trading.pnl_integration.pnl_pipeline_watcher import PipelineWatcher
  
  watcher = PipelineWatcher()
  watcher.add_watch(
      directory="data/input/market_prices",
      file_pattern=".csv",
      callback=your_price_handler
  )
  watcher.start()
  ```

### 2. Data Input Formats

#### Trade Input Format
```python
@dataclass
class TradeInput:
    timestamp: datetime       # Trade execution time
    symbol: str              # Canonical symbol format
    action: str              # 'B' or 'S'
    quantity: float          # Always positive
    price: float             # Trade price
    original_symbol: str     # As received from file
    file_source: str         # Source file path
```

#### Expected CSV Columns
- **Trade Files**: `TradeID, Symbol, TradeTime, Side, Quantity, Price`
- **Price Files**: (Define based on your requirements)

### 3. Database Requirements

#### Removed Infrastructure
- All PnL tables have been dropped
- `pnl_tracker.db` has been removed
- No existing schema constraints

#### New Module Should Create
- Its own database file(s)
- Tables with clear namespace (e.g., `newpnl_*`)
- Proper indexes for performance

#### Preserved Databases
- `market_prices.db` - Contains price data
- `spot_risk.db` - Contains spot risk data

### 4. Directory Structure

```
data/
├── input/
│   ├── trade_ledger/        # Trade CSV files
│   ├── market_prices/       # Price CSV files
│   └── spot_risk/          # Spot risk files
└── output/
    └── [your_module]/      # Create your output directory
```

### 5. Symbol Format Requirements

#### Legacy Formats (Removed)
Multiple symbol translators existed but have been removed:
- SymbolTranslator (Bloomberg ↔ Actant)
- TreasuryNotationMapper (Bloomberg/Actant/CME)
- SpotRiskSymbolTranslator

#### New Module Requirements
- Implement a single canonical symbol format
- Handle symbol normalization in `_normalize_symbol()` method
- Document format clearly

### 6. Essential Features to Implement

Based on removed functionality, the new module should provide:

#### Core Calculations
- [ ] FIFO position tracking (long and short)
- [ ] P&L calculation with proper cost basis
- [ ] Support for multiple asset types (futures, options)
- [ ] Proper handling of:
  - SOD (start-of-day) positions
  - Exercise/assignment (zero price trades)
  - Settlement boundaries

#### Data Management
- [ ] Trade ingestion and validation
- [ ] Position state persistence
- [ ] Historical P&L tracking
- [ ] Audit trail/logging

#### Real-time Features
- [ ] Incremental position updates
- [ ] Live P&L calculations
- [ ] Integration with price feeds

### 7. Service Interface Recommendations

Based on removed services, consider implementing:

```python
class PnLService:
    """Main service interface for PnL calculations"""
    
    def process_trades(self, trades: List[TradeInput]) -> None:
        """Process new trades and update positions"""
        pass
    
    def get_current_positions(self) -> pd.DataFrame:
        """Get current open positions"""
        pass
    
    def get_pnl_summary(self) -> Dict[str, float]:
        """Get P&L summary by symbol"""
        pass
    
    def get_historical_pnl(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical P&L for date range"""
        pass
```

### 8. Dashboard Integration

#### Removed Dashboards
- `apps/dashboards/pnl/` - Basic PnL dashboard
- `apps/dashboards/pnl_v2/` - Enhanced version
- Main dashboard PnL references

#### Integration Approach
- Create new dashboard in `apps/dashboards/[your_module]/`
- Follow existing dashboard patterns
- Use wrapped components from `@/components`

### 9. Monitoring Integration

The codebase uses a monitoring decorator pattern:

```python
from lib.monitoring.decorators import monitor

@monitor()
def your_calculation_method():
    pass
```

### 10. Testing Strategy

#### Test Directories
- Create tests in `tests/[your_module]/`
- Follow existing test patterns
- Include unit and integration tests

#### Critical Test Cases
- FIFO calculation accuracy
- Position state consistency
- Edge cases (SOD, exercises)
- Performance under load

## Migration Considerations

### From TradePreprocessor System
- Basic FIFO, long positions only
- Used `processed_trades` and `positions` tables
- Symbol translation via SymbolTranslator

### From TYU5 System
- Advanced FIFO with shorts
- Greeks and attribution
- Settlement P&L splits
- Used `tyu5_*` tables

### Key Differences to Consider
- Settlement handling (2pm boundaries)
- Option pricing models
- Risk calculations
- Symbol format standardization

## Rollback Information

If integration fails:
- Git tag: `pre-pnl-removal-20250725-141713`
- Database backups: `backups/pre-removal-20250725/`
- Full removal manifest: `memory-bank/pnl_migration/removal_manifest.md`

## Next Steps

1. Review this specification
2. Design your module architecture
3. Implement core functionality
4. Integrate with file watchers
5. Create database schema
6. Build service layer
7. Add dashboard (if needed)
8. Comprehensive testing
9. Production deployment

## Questions to Address

Before implementation:
1. Which calculation methodology (basic FIFO vs advanced)?
2. Symbol format decision
3. Database technology (SQLite, PostgreSQL, etc.)
4. Performance requirements
5. UI/Dashboard needs
6. Integration timeline

## Support Files

- Phase 1 Mapping: `memory-bank/pnl_migration/phase1_mapping.md`
- Phase 2 Removal Plan: `memory-bank/pnl_migration/phase2_removal_plan.md`
- Removal Manifest: `memory-bank/pnl_migration/removal_manifest.md` 