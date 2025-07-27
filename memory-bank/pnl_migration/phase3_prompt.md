# Phase 3: Data Migration and Bridging Strategy Prompt

## Context
Phase 1 mapping (`memory-bank/pnl_migration/phase1_mapping.md`) identified two parallel PnL systems with complex interdependencies. Phase 2 planning (`memory-bank/pnl_migration/phase2_removal_plan.md`) established a removal strategy prioritizing TYU5 preservation and gradual migration. This phase focuses on the critical data migration and temporary bridging mechanisms needed to safely transition from the existing dual-system architecture to the new unified PnL module.

## Objective
Design and implement data migration strategies and temporary bridges that:
1. Ensure zero data loss during transition
2. Maintain backward compatibility for existing consumers
3. Enable gradual cutover without production disruption
4. Provide clear audit trails for compliance
5. Support immediate rollback if issues arise

## Phase 3: Data Migration & Bridging Process

### 3.1 Data Migration Analysis

For each data store identified in Phase 1, create a migration plan:

```markdown
### Migration Plan: [Table/Data Store Name]

**Current State Analysis**:
- Table: [name]
- Database: [location]
- Schema: [current structure]
- Size: [rows/GB]
- Update frequency: [real-time/batch/daily]
- Retention policy: [current policy]

**Data Quality Assessment**:
- Null fields: [critical fields that shouldn't be null]
- Data integrity issues: [foreign key violations, orphaned records]
- Duplicate data: [identified duplicates between systems]
- Historical gaps: [missing date ranges]

**Migration Strategy**:
- Method: [Direct copy/Transform/Merge/Archive]
- Transformation required: [Yes/No - specify transformations]
- Deduplication approach: [if applicable]
- Validation criteria: [how to verify migration success]

**Consumers to Notify**:
- Dashboard: [name] - Impact: [read-only/write/both]
- Service: [name] - Impact: [API changes needed]
- Report: [name] - Impact: [query changes needed]

**Rollback Procedure**:
1. [Specific step]
2. [Specific step]
```

### 3.2 Bridge Component Design

For each temporary bridge identified in Phase 2:

```markdown
### Bridge Design: [Bridge Name]

**Purpose**: [Why this bridge is needed]
**Lifetime**: [Expected duration - weeks/months]

**Interface Specification**:
```python
# Current interface that must be preserved
class CurrentInterface:
    def existing_method(self, params) -> ReturnType:
        pass

# New interface to implement
class BridgeAdapter:
    def existing_method(self, params) -> ReturnType:
        # Transform to new system
        pass
```

**Implementation Details**:
- Location: [where bridge code will live]
- Dependencies: [what it needs to import]
- Configuration: [any settings/flags needed]
- Monitoring: [how to track bridge usage]

**Deprecation Plan**:
- Usage metrics endpoint: [how to measure adoption]
- Sunset date: [target removal date]
- Consumer migration guide: [documentation location]
```

### 3.3 Symbol Translation Bridge

Given the critical nature of symbol translation between systems:

```markdown
### Unified Symbol Translation Service

**Current State**:
- TradePreprocessor: Uses raw symbols
- TYU5: Multiple symbol translators (SymbolTranslator, canonical())
- Database: Mixed symbol formats

**Bridge Requirements**:
1. Bidirectional translation (CME ↔ Bloomberg)
2. Version tracking (know which system wrote what)
3. Caching for performance
4. Audit logging for compliance

**Implementation**:
```python
class UnifiedSymbolBridge:
    def to_canonical(self, symbol: str, source: str) -> str:
        """Convert any symbol to canonical format"""
        
    def from_canonical(self, symbol: str, target: str) -> str:
        """Convert canonical to specific format"""
        
    def get_all_variants(self, symbol: str) -> dict:
        """Return all known variants of a symbol"""
```
```

### 3.4 Database View Strategy

Create views to maintain backward compatibility:

```sql
-- Example: Unified position view combining both systems
CREATE VIEW unified_positions AS
SELECT 
    'TYU5' as source_system,
    symbol,
    quantity,
    realized_pnl,
    unrealized_pnl,
    last_updated
FROM tyu5_lot_positions
WHERE is_active = 1

UNION ALL

SELECT 
    'CTO' as source_system,
    symbol,
    SUM(quantity) as quantity,
    SUM(realized_pnl) as realized_pnl,
    0 as unrealized_pnl,  -- CTO doesn't track unrealized
    MAX(last_update) as last_updated
FROM cto_trades
GROUP BY symbol;
```

### 3.5 Data Reconciliation Framework

```markdown
### Reconciliation Process

**Daily Reconciliation Checks**:
1. Position quantities between systems
2. P&L totals by symbol
3. Trade counts and timestamps
4. Price mark consistency

**Reconciliation Report Format**:
```csv
date,symbol,metric,system1_value,system2_value,difference,status
2024-01-15,TYH4,position,100,100,0,MATCHED
2024-01-15,TYH4,realized_pnl,5000.00,4999.50,0.50,WITHIN_TOLERANCE
2024-01-15,ESH4,position,50,45,5,INVESTIGATION_REQUIRED
```

**Alerting Thresholds**:
- Position difference > 0: CRITICAL
- P&L difference > $100: WARNING
- P&L difference > $1000: CRITICAL
```

### 3.6 Cutover Sequence

```markdown
### Week-by-Week Cutover Plan

**Week 1: Read-Only Bridge Deployment**
- Deploy symbol translation bridge
- Deploy database views
- Enable shadow mode (new system runs parallel)
- Begin collecting comparison metrics

**Week 2: Non-Critical Consumer Migration**
- Migrate monitoring dashboards to views
- Update batch reports to use bridges
- Keep critical paths on original

**Week 3-4: Progressive Write Cutover**
- Route X% of new trades to new system
- Gradual increase: 10% → 25% → 50% → 100%
- Monitor reconciliation reports

**Week 5: Legacy Read Migration**
- Switch read paths to new system
- Keep legacy writes for rollback

**Week 6: Final Cutover**
- Disable legacy write paths
- Archive legacy tables
- Remove temporary bridges
```

## Required Deliverables

1. **Migration Scripts** (`migration/scripts/`)
   - Data transformation scripts
   - Validation queries
   - Rollback scripts

2. **Bridge Components** (`lib/trading/pnl/bridges/`)
   - Symbol translation bridge
   - Service adapter bridges
   - Database view definitions

3. **Monitoring Dashboard**
   - Real-time reconciliation view
   - Bridge usage metrics
   - System health indicators

4. **Documentation**
   - Consumer migration guide
   - Runbook for cutover
   - Rollback procedures

## Success Criteria

- Zero data loss during migration
- All reconciliation checks pass for 5 consecutive days
- No production incidents during cutover
- All consumers successfully migrated
- Performance metrics within 10% of baseline

## Risk Mitigation

1. **Data Loss**: Backup before each migration step
2. **Performance**: Load test bridges at 2x production volume
3. **Rollback**: Test rollback procedures in staging
4. **Communication**: Daily status updates during migration 