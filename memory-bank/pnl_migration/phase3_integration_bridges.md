# Phase 3: Integration Bridge Design

## Executive Summary

This phase designs temporary integration bridges to enable safe migration from existing PnL systems to the new module while maintaining production stability.

## Integration Bridge Architecture

### 1. Service Layer Bridge

```python
# Canonical Interface Bridge
class PnLServiceBridge:
    """
    Temporary bridge that routes calls between old and new implementations
    based on feature flags or configuration.
    """
    def __init__(self):
        self.legacy_service = UnifiedPnLService()  # Current production
        self.new_service = None  # Your new module
        self.routing_config = self._load_routing_config()
    
    def calculate_pnl(self, trades, prices, **kwargs):
        if self._should_use_new_service('calculate_pnl'):
            return self._call_with_fallback(
                self.new_service.calculate_pnl,
                self.legacy_service.calculate_pnl,
                trades, prices, **kwargs
            )
        return self.legacy_service.calculate_pnl(trades, prices, **kwargs)
```

### 2. Data Migration Bridge

```python
# Database Table Bridge
class DatabaseBridge:
    """
    Handles dual-write and migration between old and new schemas
    """
    def __init__(self):
        self.old_db = "pnl_tracker.db"
        self.new_db = None  # Your new database
        self.migration_mode = "dual_write"  # dual_write, old_only, new_only
    
    def write_position(self, position_data):
        if self.migration_mode in ["dual_write", "old_only"]:
            self._write_to_old_schema(position_data)
        if self.migration_mode in ["dual_write", "new_only"]:
            self._write_to_new_schema(position_data)
```

### 3. Symbol Translation Bridge

```python
# Unified Symbol Translator
class SymbolTranslationBridge:
    """
    Centralizes all symbol translation logic during migration
    """
    def __init__(self):
        self.cto_translator = CTOSymbolTranslator()
        self.bloomberg_mapper = BloombergSymbolMapper()
        self.new_translator = None  # Your new translator
    
    def canonical(self, symbol, source_system="auto"):
        # Provides consistent symbol format across all systems
        if source_system == "auto":
            source_system = self._detect_source(symbol)
        
        # Route to appropriate translator
        if source_system == "CTO":
            return self.cto_translator.to_canonical(symbol)
        elif source_system == "Bloomberg":
            return self.bloomberg_mapper.to_canonical(symbol)
        elif source_system == "new":
            return self.new_translator.to_canonical(symbol)
```

## Bridge Implementation Phases

### Phase 3.1: Read-Only Integration (Week 1-2)
- New module reads from existing databases
- No writes from new module
- Validation and comparison mode

### Phase 3.2: Shadow Mode (Week 3-4)
- New module calculates in parallel
- Results compared but not used
- Performance benchmarking

### Phase 3.3: Dual-Write Mode (Week 5-6)
- New module writes to separate namespace
- Both systems fully operational
- A/B testing capabilities

### Phase 3.4: Primary Switch (Week 7-8)
- New module becomes primary
- Old system in read-only fallback
- Monitoring for issues

### Phase 3.5: Cleanup (Week 9-10)
- Remove old system components
- Data migration completion
- Bridge removal

## Critical Integration Points

### 1. File Watcher Integration
```python
# Adapter for existing file watchers
class FileWatcherAdapter:
    def __init__(self, new_processor):
        self.new_processor = new_processor
        self.legacy_watcher = TradeFileWatcher()
    
    def on_file_change(self, filepath):
        # Route to both systems during migration
        self.legacy_watcher.process_file(filepath)
        if self.is_migration_enabled():
            self.new_processor.process_file(filepath)
```

### 2. Dashboard Integration
```python
# Dashboard data provider bridge
class DashboardDataBridge:
    def get_pnl_data(self, request):
        if self.use_new_system(request.user):
            return self.new_service.get_dashboard_data(request)
        return self.legacy_service.get_dashboard_data(request)
```

### 3. Excel Report Integration
```python
# Excel report generator bridge
class ExcelReportBridge:
    def generate_daily_pnl(self, date):
        if self.migration_phase >= "dual_write":
            # Generate from both, compare
            old_report = self.legacy_generator.generate(date)
            new_report = self.new_generator.generate(date)
            self._validate_reports(old_report, new_report)
        return self.active_generator.generate(date)
```

## Monitoring and Validation

### Comparison Framework
```python
class PnLComparisonValidator:
    """
    Validates new system outputs against legacy
    """
    def validate_calculation(self, trades, old_result, new_result):
        differences = []
        
        # Position comparison
        if abs(old_result.position - new_result.position) > 0.0001:
            differences.append({
                'field': 'position',
                'old': old_result.position,
                'new': new_result.position
            })
        
        # PnL comparison
        if abs(old_result.pnl - new_result.pnl) > 0.01:
            differences.append({
                'field': 'pnl',
                'old': old_result.pnl,
                'new': new_result.pnl
            })
        
        return differences
```

### Metrics Collection
- Calculation time comparison
- Memory usage
- Result accuracy
- Error rates
- User impact

## Rollback Procedures

### Emergency Rollback
```bash
# 1. Feature flag disable
UPDATE config SET use_new_pnl_system = false;

# 2. Stop dual writes
UPDATE config SET migration_mode = 'old_only';

# 3. Clear new system cache
DELETE FROM new_pnl_cache;

# 4. Notify monitoring
curl -X POST monitoring.api/alert "PnL system rolled back"
```

### Gradual Rollback
1. Reduce traffic percentage to new system
2. Monitor legacy system performance
3. Investigate issues in staging
4. Fix and redeploy

## Configuration Management

```yaml
# pnl_migration_config.yaml
migration:
  phase: "shadow_mode"  # read_only, shadow_mode, dual_write, primary_switch
  
  feature_flags:
    use_new_calculator: false
    use_new_storage: false
    use_new_reports: false
  
  traffic_routing:
    new_system_percentage: 0
    user_whitelist: []
    
  validation:
    comparison_threshold: 0.01
    alert_on_mismatch: true
    
  monitoring:
    log_all_calculations: true
    performance_tracking: true
```

## Success Criteria

### Phase Gate Checklist
- [ ] All unit tests passing for bridges
- [ ] Integration tests covering edge cases
- [ ] Performance benchmarks meet targets
- [ ] Zero data loss during migration
- [ ] Rollback tested and documented
- [ ] Monitoring dashboards operational
- [ ] Team trained on new system

## Risk Mitigation

### High-Risk Areas
1. **Symbol translation inconsistencies**
   - Mitigation: Canonical function with extensive testing
   
2. **Database transaction conflicts**
   - Mitigation: Separate namespaces, row-level locking

3. **File watcher race conditions**
   - Mitigation: Queue-based processing, idempotent operations

4. **Excel report format changes**
   - Mitigation: Side-by-side comparison, user acceptance testing

5. **Dashboard real-time updates**
   - Mitigation: Gradual rollout, fallback mechanisms

## Next Steps

1. Review integration points with your new module's architecture
2. Identify any additional bridges needed
3. Implement Phase 3.1 (Read-Only Integration)
4. Set up comparison framework
5. Begin shadow mode testing 