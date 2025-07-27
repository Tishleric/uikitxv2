# Phase 2: PnL Module Removal Plan

## Executive Summary

- **Total components to remove**: 47 major components across 2 parallel systems
- **Estimated timeline**: 8-10 weeks for complete removal
- **Critical risks identified**: 5 high-risk areas requiring temporary bridges
- **Recommended approach**: Gradual migration preserving TYU5 as primary during transition

## Critical Decision Points

Based on Phase 1 analysis, these strategic decisions guide the removal plan:

### 1. Primary System Selection
**Decision: Preserve TYU5 system longer**
- Rationale: More feature-complete (shorts, Greeks, Bachelier pricing)
- TradePreprocessor to be removed first after decoupling

### 2. Database Strategy
**Decision: Namespace separation with staged migration**
- Keep both systems' tables during transition
- New module writes to new namespace
- Views for backward compatibility

### 3. Service Layer Approach
**Decision: UnifiedPnLService becomes canonical interface**
- Already merges both systems
- Minimal client impact
- Can be refactored to use only new module

### 4. Symbol Format Decision
**Decision: canonical() function approach**
- Already attempts normalization
- Translators become internal implementation detail

### 5. Cutover Strategy
**Decision: Gradual migration with feature flags**
- Lower risk than big bang
- Allows A/B testing
- Easier rollback

## 2.1 Dependency Risk Assessment

### Component Risk Profile: TradePreprocessor
**Removal Risk Level**: High
**Current State**: Active - processes all incoming trades

**Inbound Dependencies**:
- File watchers → Impact: Breaks trade ingestion
- Scripts/automation → Impact: Breaks various scripts
- TYU5 trigger → Impact: Stops TYU5 calculations

**Outbound Dependencies**:
- PnLStorage → Can be mocked: Yes
- SymbolTranslator → Alternative: canonical() function
- Database writes → Alternative: New module

**Data Dependencies**:
- Tables written: processed_trades, cto_trades (unique to this system)
- Shared state: File processing state tracker

**Production Traffic Analysis**:
- Last use: Continuous (processes all trades)
- User impact if removed: Critical - no trades processed

**Removal Complexity Score**: 8/10
**Safe to Remove**: After TradeBridge implemented

### Component Risk Profile: TYU5Service
**Removal Risk Level**: High
**Current State**: Active - triggered by TradePreprocessor

**Inbound Dependencies**:
- TradePreprocessor trigger → Impact: Need new trigger
- PNLPipelineWatcher → Impact: Breaks automation
- Scripts → Impact: Multiple scripts fail

**Outbound Dependencies**:
- TradeLedgerAdapter → Can be replaced: Yes
- Market price DB → Shared resource: Yes

**Data Dependencies**:
- Tables written: All tyu5_* tables (unique)
- Tables read: processed_trades (from TradePreprocessor)

**Production Traffic Analysis**:
- Last use: Continuous (after each trade file)
- User impact: High - advanced features unavailable

**Removal Complexity Score**: 7/10
**Safe to Remove**: After new module has feature parity

### Component Risk Profile: PnLService
**Removal Risk Level**: Medium
**Current State**: Active via UnifiedPnLService

**Inbound Dependencies**:
- UnifiedPnLService → Impact: Needs refactoring
- Legacy scripts → Impact: Some scripts break

**Outbound Dependencies**:
- PnLStorage → Shared with TradePreprocessor
- PositionManager → Coupled implementation

**Removal Complexity Score**: 5/10
**Safe to Remove**: After UnifiedPnLService refactored

### Component Risk Profile: pnl/ dashboard
**Removal Risk Level**: Low
**Current State**: Dormant (commented out in main)

**Inbound Dependencies**:
- Main dashboard → Already disconnected
- No active users → No impact

**Removal Complexity Score**: 2/10
**Safe to Remove**: Immediately

### Component Risk Profile: UnifiedPnLService
**Removal Risk Level**: Critical
**Current State**: Active - used by pnl_v2 dashboard

**Inbound Dependencies**:
- pnl_v2 dashboard → Impact: Dashboard breaks
- Controller → Impact: No data for UI

**Data Dependencies**:
- Reads from both systems' tables
- No writes - read-only aggregator

**Removal Complexity Score**: 9/10
**Safe to Remove**: Only after complete replacement

### Component Risk Profile: File Watchers (Multiple)
**Removal Risk Level**: High
**Current State**: Active - multiple watchers running

**Components**:
- TradePreprocessor file watcher
- PNLPipelineWatcher
- MarketPriceFileMonitor
- SpotRiskWatcher

**Inbound Dependencies**:
- run_all_watchers.py → Orchestrates all
- Batch files → Windows automation

**Production Traffic Analysis**:
- Continuous monitoring of input directories
- Critical for real-time updates

**Removal Complexity Score**: 7/10
**Safe to Remove**: After new unified watcher implemented

### Component Risk Profile: Symbol Translators
**Removal Risk Level**: Medium
**Current State**: Active - multiple translators in use

**Components**:
- SymbolTranslator (Bloomberg ↔ Actant)
- TreasuryNotationMapper (Bloomberg/Actant/CME)
- SpotRiskSymbolTranslator (Actant spot risk)
- canonical() function

**Usage Patterns**:
- TradePreprocessor uses SymbolTranslator
- TYU5 uses multiple translators
- Spot risk has its own translator

**Removal Complexity Score**: 6/10
**Safe to Remove**: After canonical() becomes sole authority

## 2.2 System Decoupling Strategy

### Decoupling Plan: TradePreprocessor from TYU5Service

**Current Coupling Points**:
1. Direct trigger after trade processing
2. Shared processed_trades table
3. Both read market_prices.db
4. Implicit ordering dependency

**Decoupling Steps**:
1. Create event queue table - Risk: Low
2. TradePreprocessor writes events instead of direct trigger - Risk: Medium
3. TYU5Service polls events - Risk: Low
4. Remove direct import/call - Risk: Low

**Temporary Bridge Required**: Yes
- Bridge Type: Database event queue
- Implementation: Simple table with processed flag
- Lifetime: 4-6 weeks
- Rollback: Restore direct trigger

### Decoupling Plan: UnifiedPnLService from Both Systems

**Current Coupling Points**:
1. Direct SQL queries to both systems' tables
2. Merges data in memory
3. Knows both schemas intimately

**Decoupling Steps**:
1. Create interface abstraction - Risk: Low
2. Implement adapters for each system - Risk: Medium
3. Add new module adapter - Risk: Low
4. Switch adapters via config - Risk: Medium

**Temporary Bridge Required**: Yes
- Bridge Type: Adapter pattern
- Implementation: IPnLDataSource interface
- Lifetime: Entire transition period
- Rollback: Keep old adapters available

### Decoupling Plan: File Watchers Consolidation

**Current Coupling Points**:
1. Multiple independent watchers
2. Each has own state management
3. Overlapping responsibilities

**Decoupling Steps**:
1. Create unified watcher interface - Risk: Low
2. Consolidate state management - Risk: Medium
3. Route events to appropriate handlers - Risk: Low
4. Deprecate individual watchers - Risk: Medium

## 2.3 Removal Sequencing Matrix

### Phase 2.1: Safe Immediate Removals (Week 1)
| Component | Location | Verification Method | Rollback |
|-----------|----------|-------------------|----------|
| pnl/ dashboard | apps/dashboards/pnl/ | Check no imports | git restore |
| .backup files | *.backup | Check no references | git restore |
| Dead test files | tests/ orphans | CI passes | git restore |
| Commented code | Various | Grep for refs | git restore |

### Phase 2.2: Low-Risk Removals (Week 2-3)
| Component | Prerequisites | Migration Steps | Verification |
|-----------|--------------|----------------|--------------|
| Duplicate utils | Consolidate to one | 1. Find all copies<br>2. Update imports<br>3. Remove duplicates | Tests pass |
| Old migrations | Already applied | 1. Verify applied<br>2. Archive SQL<br>3. Remove files | DB state unchanged |
| Legacy scripts | Not in automation | 1. Check cron/schedulers<br>2. Document purpose<br>3. Remove | No automation breaks |

### Phase 2.3: TradePreprocessor Decoupling (Week 4-5)
| Step | Action | Risk | Verification |
|------|--------|------|--------------|
| 1 | Implement EventQueue | Low | Unit tests |
| 2 | Add queue writer to TradePreprocessor | Medium | Integration test |
| 3 | Add queue reader to TYU5Service | Low | E2E test |
| 4 | Parallel run (both paths) | Low | Output comparison |
| 5 | Disable direct trigger | High | Monitor for 48h |
| 6 | Remove trigger code | Low | Tests pass |

### Phase 2.4: Service Layer Refactoring (Week 6-7)
| Step | Action | Risk | Verification |
|------|--------|------|--------------|
| 1 | Create IPnLDataSource interface | Low | Compiles |
| 2 | Wrap existing services | Medium | Unit tests |
| 3 | Update UnifiedPnLService | Medium | Integration tests |
| 4 | Add feature flags | Low | Flag works |
| 5 | Test new module adapter | Medium | A/B test results |

### Phase 2.5: Core System Removal (Week 8-10)
| Component | Prerequisites | Steps | Rollback Time |
|-----------|--------------|-------|---------------|
| TradePreprocessor | New module ingesting | 1. Stop file watcher<br>2. Archive code<br>3. Clean imports | 1 hour |
| PnLService | No direct users | 1. Update UnifiedPnL<br>2. Remove service<br>3. Clean up | 30 min |
| TYU5Service | Feature parity | 1. Switch all clients<br>2. Monitor 1 week<br>3. Remove | 2 hours |

## 2.4 Data Preservation Strategy

### Data Preservation Plan: processed_trades
**Data Classification**:
- Business Critical: Yes
- Regulatory Required: Unknown (assume yes)
- Historical Value: High
- Recreatable: No

**Preservation Strategy**:
☑ Archive to cold storage: `/archive/pnl_migration/processed_trades_YYYYMMDD.sql`
☑ Migrate to new schema: Map to new module's trade format
☐ Export to standard format: N/A
☐ Merge with other table: N/A
☐ Safe to delete: Never

**Migration Script Required**: Yes
```sql
-- Create archive
CREATE TABLE archive_processed_trades AS 
SELECT *, CURRENT_TIMESTAMP as archived_at 
FROM processed_trades;

-- Migration mapping
INSERT INTO new_module_trades (
  id, symbol, timestamp, action, quantity, price
) SELECT 
  trade_id, symbol, timestamp, type, quantity, price
FROM processed_trades;
```

### Data Preservation Plan: tyu5_* tables
**Data Classification**:
- Business Critical: Yes (current production)
- Historical Value: High
- Recreatable: Partial (from trades)

**Preservation Strategy**:
☑ Archive entire schema: `/archive/pnl_migration/tyu5_tables_YYYYMMDD.db`
☑ Keep available for queries: Read-only mount
☐ Migrate: Not needed if new module calculates same

### Data Preservation Plan: market_prices.db
**Data Classification**:
- Business Critical: Yes
- Shared Resource: Used by all systems
- Continuously Updated: Yes

**Preservation Strategy**:
☑ Keep operational: Required by new module
☑ Clean old price types: Remove unused columns after migration
☑ Add indexes: Optimize for new access patterns

## 2.5 Functional Preservation Checklist

| Business Function | Current Implementation | New Module Coverage | Gap Handling |
|------------------|----------------------|-------------------|--------------|
| Trade Ingestion | TradePreprocessor | Required | TradeBridge until ready |
| FIFO Long Positions | Both systems | Required | None |
| FIFO Short Positions | TYU5 only | Required | None |
| Settlement P&L Split | PositionCalculator2 | Required | None |
| Greeks Calculation | TYU5 only | Nice-to-have | Accept gap or bridge |
| Risk Scenarios | TYU5 only | Nice-to-have | Accept gap |
| EOD Snapshots | Both systems | Required | None |
| Real-time Updates | File watchers | Required | New watchers |
| Historical P&L | Both systems' tables | Required | Migration needed |
| Dashboard Data | UnifiedPnLService | Required | Adapter pattern |
| Symbol Translation | Multiple translators | Required | canonical() function |
| Price Updates | Multiple sources | Required | Unified price service |

**Critical Gaps Requiring Bridges**:
1. Trade Ingestion: EventQueue until new module ready
2. Dashboard Data: Adapter pattern for gradual transition
3. Historical Queries: View layer over old+new tables
4. Symbol Translation: Temporary multi-translator bridge

## 2.6 Rollback Planning

### Rollback Checkpoint: After Safe Removals (Week 1)
**Pre-removal State Capture**:
- Database backup: `sqlite3 pnl_tracker.db .backup backup_week1.db`
- Code snapshot: `git tag removal-phase-week1`
- Configuration backup: Copy all .env and config files

**Rollback Triggers**:
☑ Any production errors in PnL calculation
☑ Dashboard shows no data
☐ Performance degradation (not expected)

**Rollback Procedure**:
1. `git checkout removal-phase-week1` - 5 minutes
2. Restore configs - 5 minutes
3. Restart services - 10 minutes
Total: 20 minutes

### Rollback Checkpoint: After TradePreprocessor Decoupling
**Rollback Triggers**:
☑ Trades not processing
☑ TYU5 calculations stopped
☑ Event queue growing unbounded

**Rollback Procedure**:
1. Re-enable direct trigger - 10 minutes
2. Drain event queue - 20 minutes
3. Verify calculations resume - 10 minutes
Total: 40 minutes

## 2.7 Temporary Bridge Specifications

### Bridge Specification: TradeEventQueue

**Purpose**: Decouple TradePreprocessor from TYU5Service during transition
**Lifetime**: 4-6 weeks

**Interface Design**:
```python
class TradeEventQueue:
    """Bridge between TradePreprocessor and TYU5Service"""
    
    def publish_trade_file_processed(self, file_path: str, record_count: int):
        """TradePreprocessor calls this instead of triggering TYU5"""
        # Write to event table with timestamp
        
    def consume_pending_events(self) -> List[TradeEvent]:
        """TYU5Service polls this for new work"""
        # Read unprocessed events, mark as processed
        
    def get_queue_depth(self) -> int:
        """Monitor queue health"""
        # Return count of unprocessed events
```

**Monitoring Requirements**:
- Alert if queue depth > 100
- Log all publish/consume operations
- Track processing latency

**Removal Criteria**:
☑ New module processing trades directly
☑ 7 days without queue usage
☑ All historical trades migrated

### Bridge Specification: PnLDataAdapter

**Purpose**: Allow UnifiedPnLService to work with old and new systems
**Lifetime**: Entire transition (8-10 weeks)

**Interface Design**:
```python
from abc import ABC, abstractmethod

class IPnLDataSource(ABC):
    @abstractmethod
    def get_positions(self) -> DataFrame:
        pass
        
    @abstractmethod  
    def get_pnl_history(self, days: int) -> DataFrame:
        pass

class LegacyPnLAdapter(IPnLDataSource):
    """Adapter for current TradePreprocessor + TYU5 data"""
    
class NewModuleAdapter(IPnLDataSource):
    """Adapter for new PnL module"""
    
class UnifiedPnLService:
    def __init__(self, data_source: IPnLDataSource):
        self.data_source = data_source
```

### Bridge Specification: SymbolTranslationBridge

**Purpose**: Handle multiple symbol formats during transition
**Lifetime**: 6-8 weeks

**Interface Design**:
```python
class SymbolTranslationBridge:
    """Temporary bridge for symbol format translation"""
    
    def __init__(self):
        self.translators = {
            'bloomberg_actant': SymbolTranslator(),
            'treasury': TreasuryNotationMapper(),
            'spot_risk': SpotRiskSymbolTranslator()
        }
    
    def to_canonical(self, symbol: str, source_format: str) -> str:
        """Convert any format to canonical"""
        if source_format == 'canonical':
            return symbol
        translator = self.translators.get(source_format)
        if translator:
            intermediate = translator.translate(symbol)
            return canonical(intermediate)
        return canonical(symbol)  # Try direct
```

## Risk Registry

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Trade processing stops | Medium | Critical | EventQueue bridge + monitoring | DevOps |
| Dashboard data missing | Medium | High | Parallel data sources | Frontend |
| Historical P&L lost | Low | High | Complete archive before removal | Data |
| Calculation differences | High | Medium | A/B testing period | QA |
| Rollback fails | Low | Critical | Test rollbacks in staging | DevOps |
| Symbol format conflicts | High | Medium | Translation bridge + testing | Backend |
| Watcher coordination fails | Medium | High | Unified watcher with fallback | DevOps |

## Go/No-Go Criteria

**Proceed to Week 1 Removals if**:
- ☑ Git tag created
- ☑ Database backed up
- ☑ Team notified

**Proceed to Decoupling if**:
- ☑ EventQueue tested in staging
- ☑ Monitoring configured
- ☑ Rollback tested

**Proceed to Core Removal if**:
- ☑ New module at feature parity
- ☑ A/B tests show < 0.01% difference
- ☑ 1 week stable operation
- ☑ All bridges functioning

## Validation Checklist

- ☑ Every component from Phase 1 has removal plan
- ☑ All production functionality preserved or bridged
- ☑ Data migration scripts provided
- ☑ Rollback procedures documented
- ☑ Risk registry complete
- ☑ Removal sequence has no circular dependencies
- ☑ Bridge implementations specified
- ☑ File watcher consolidation planned
- ☑ Symbol translation strategy defined

## Implementation Notes

### Key Technical Details Discovered:
1. **TradePreprocessor → TYU5 Trigger**: Direct function call in trade_preprocessor.py lines 429-434
2. **Database**: SQLite (not PostgreSQL) - adjust backup commands
3. **Multiple Watchers**: Need consolidation strategy to avoid gaps
4. **Symbol Formats**: At least 4 different formats in active use

### Critical Path Items:
1. **EventQueue Implementation**: Must be bulletproof - handles all trade flow
2. **Dashboard Adapter**: pnl_v2 is only active dashboard - zero downtime required
3. **Historical Data**: Both systems have unique historical data - careful merging needed

## Next Phase Preview
**Phase 3**: Data format alignment - Standardizing formats for new module integration
**Phase 4**: Integration execution - Step-by-step replacement with verification 