# Observability System Implementation Plan
_Version 1.0 • Generated from logsystem.md + O3Pro refinements_

## Executive Summary

Building a real-time observability system for UIKitXv2 using Python decorators, SQLite storage, and Dash UI. Focus on **foundation first** - get core decorator, queue, and storage working perfectly before adding advanced features.

## Core Architecture

```mermaid
graph LR
    code[Python Functions] --> |@monitor| Q(Queue<br/>maxsize=10k)
    Q --> |batch writer<br/>10Hz| DB[(SQLite WAL)]
    DB --> API[FastAPI]
    API --> UI[Dash UI]
    DB --> ALERT[Alert Engine]
```

## Phase 0: Foundation (2-3 days)

### 0.1 Monitor Decorator

```python
@monitor(
    process_group: str,                              # e.g., "trading.actant"
    sample_rate: float = 1.0,                       # 0-1 for sampling
    capture: dict = dict(args=True, result=True, locals=False),
    serializer: str | Callable = "smart",           # smart|repr|json|custom
    max_repr: int = 1_000,                          # truncate long values
    sensitive_fields: tuple[str, ...] = ("password", "api_key", "token"),
    queue_warning_threshold: int = 8_000,           # backpressure warning
)
```

**Implementation**: `lib/monitoring/decorators/monitor.py`

### 0.2 Smart Serialization

| Data Type | Strategy | Example Output |
|-----------|----------|----------------|
| primitives | `repr()` | `"42"`, `"'hello'"` |
| DataFrame | shape only | `"[DataFrame 1000×50]"` |
| ndarray | summary | `"[ndarray float64 (100,100)]"` |
| dict | shallow keys | `"{'a': ..., 'b': ..., +8 more}"` |
| custom obj | class name | `"<Portfolio at 0x123>"` |
| sensitive | masked | `"***"` |

**Implementation**: `lib/monitoring/serializers/smart.py`

### 0.3 Queue & Writer

```python
# Non-blocking producer
queue = Queue(maxsize=10_000)
queue.put_nowait(record)  # Drop if full + increment metric

# Background consumer (10Hz)
class BatchWriter(Thread):
    def run(self):
        while True:
            batch = drain_queue(max_items=100)
            if batch:
                bulk_insert(batch)  # Single transaction
            time.sleep(0.1)
```

**Implementation**: `lib/monitoring/writers/sqlite_writer.py`

### 0.4 Critical: Error-First Queue Strategy

**Requirement**: Errors must NEVER be dropped. Ideally, nothing should be dropped.

```python
class ObservabilityQueue:
    def __init__(self):
        self.error_queue = Queue()  # Unlimited size for errors
        self.normal_queue = Queue(maxsize=10_000)
        self.overflow_buffer = deque(maxlen=50_000)  # Ring buffer
        self.metrics = QueueMetrics()
    
    def put(self, record):
        if record.status == "ERR":
            # Errors always get through
            self.error_queue.put(record)
        else:
            try:
                self.normal_queue.put_nowait(record)
            except queue.Full:
                # Instead of dropping, use overflow buffer
                self.overflow_buffer.append(record)
                self.metrics.overflowed += 1
                
    def drain(self, max_items=100):
        batch = []
        # Errors first (all of them)
        while not self.error_queue.empty() and len(batch) < max_items:
            batch.append(self.error_queue.get())
        
        # Then normal records
        while not self.normal_queue.empty() and len(batch) < max_items:
            batch.append(self.normal_queue.get())
            
        # Finally, recover from overflow if space available
        while self.overflow_buffer and not self.normal_queue.full():
            self.normal_queue.put(self.overflow_buffer.popleft())
            self.metrics.recovered += 1
            
        return batch
```

**Zero-Loss Strategies**:
1. **Dual Queue System**: Separate unlimited queue for errors
2. **Overflow Buffer**: Ring buffer captures data when main queue is full
3. **Dynamic Batch Sizing**: Increase batch size under pressure
4. **Backpressure Monitoring**: Alert when approaching limits
5. **Emergency Flush**: Direct-to-disk for critical situations

### 0.5 Database Schema

```sql
-- Process-level traces
CREATE TABLE process_trace (
    ts           TEXT NOT NULL,      -- ISO format
    process      TEXT NOT NULL,      -- module.function
    status       TEXT NOT NULL,      -- OK|ERR
    duration_ms  REAL NOT NULL,
    exception    TEXT,               -- Full traceback if ERR
    PRIMARY KEY (ts, process)
);

-- Variable-level traces (one row per arg/result)
CREATE TABLE data_trace (
    ts          TEXT NOT NULL,
    process     TEXT NOT NULL,
    data        TEXT NOT NULL,       -- Variable name
    data_type   TEXT NOT NULL,       -- INPUT|OUTPUT
    data_value  TEXT NOT NULL,       -- Serialized value
    status      TEXT NOT NULL,       -- Copied from process
    exception   TEXT,                -- Copied from process
    PRIMARY KEY (ts, process, data, data_type)
);

-- Optimized indexes
CREATE INDEX idx_process_ts ON process_trace(process, ts DESC);
CREATE INDEX idx_data_process ON data_trace(process);
CREATE INDEX idx_ts_window ON process_trace(ts);
```

**Location**: `logs/observability.db`

## Phase 1: Core Features (3 days)

### 1.1 Function Type Support

| Function Type | Support | Implementation Notes |
|---------------|---------|---------------------|
| Sync functions | ✅ | Standard wrapper |
| Async functions | ✅ | `async def` wrapper with `await` |
| Generators | ✅ | Capture first `yield` only |
| Class methods | ✅ | Works with `@classmethod`, `@staticmethod` |
| Properties | ❌ | Not auto-decorated (edge case) |

### 1.2 Dash UI Components

**File**: `apps/dashboards/observability/app.py`

1. **Trace Table** (7 columns as specified)
   - Server-side pagination (50 rows/page)
   - Filters: date range, process, status, search
   - Click row → modal with details

2. **Status Bar**
   - Queue depth badge
   - Error rate (last 5 min)
   - Write lag indicator

### 1.3 Basic Alerting

```toml
# config/alerts.toml
[alerts]
check_interval_seconds = 15

[[alerts.rule]]
name = "unhandled_exception"
query = "SELECT COUNT(*) FROM process_trace WHERE status='ERR' AND ts > datetime('now', '-30 seconds')"
threshold = 1
action = "log"  # Just log for now, no external webhooks
```

## Phase 2: Advanced Features (3 days)

### 2.1 Dependency Graph
- Build from data_trace table relationships
- Cytoscape visualization
- Show last update time per node

### 2.2 Performance Metrics
- Sparkline charts in modal
- P50/P95/P99 latencies
- Execution count trends

### 2.3 Auto-Instrumentation Helper

```python
# Selective module decoration
from lib.monitoring import auto_instrument_module

auto_instrument_module(
    module=actant_pnl,
    include_regex=r"^(process_|calculate_|fetch_)",
    exclude=("test_", "_helper"),
    process_group="trading.actant_pnl"
)
```

## Technical Specifications

### Performance Targets
- Decorator overhead: <50µs (realistic target)
- Queue operations: <5µs
- Batch write: <20ms per 100 rows
- UI query response: <100ms

### Retention Strategy
- Hot storage: 6 hours (150MB @ 25k rows/min)
- Purge job: Every 60s, DELETE WHERE ts < 6h ago
- Phase 3: Daily VACUUM INTO S3

### Migration Plan
1. Create shim decorators:
   ```python
   def TraceTime(*a, **kw): 
       return monitor(process_group="legacy.time", *a, **kw)
   ```
2. Run automated replacement via ruff
3. Deprecation warnings for 1 month

## Implementation Checklist

### Week 1 Sprint
- [ ] Implement @monitor decorator with sync function support
- [ ] Create smart serializer with all type handlers  
- [ ] Build queue + batch writer thread
- [ ] Set up SQLite schema with indexes
- [ ] Add comprehensive unit tests
- [ ] Create basic Dash table view

### Week 2 Sprint  
- [ ] Add async/generator support
- [ ] Implement server-side filtering
- [ ] Build modal with code + sparkline
- [ ] Add basic alerting engine
- [ ] Create auto_instrument helper
- [ ] Performance benchmarks

### Definition of Done
1. Three high-risk functions decorated and running in prod
2. <50µs overhead confirmed via benchmarks
3. UI loads 1M rows in <100ms (paginated)
4. Zero data loss under normal load
5. All tests passing, mypy clean

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Queue overflow | Drop policy + monitoring metric |
| SQLite lock contention | WAL mode + batch writes |
| UI performance | Server-side filtering + pagination |
| Serialization errors | Try/except with fallback to class name |
| Decorator overhead | Sampling for hot paths |

## Next Immediate Actions

1. Create `lib/monitoring/decorators/monitor.py` with basic implementation
2. Set up SQLite schema and writer thread
3. Decorate `actant_main()` as proof of concept
4. Benchmark overhead and iterate
5. Build minimal Dash table to visualize traces

## Detailed Implementation Roadmap

### Overview
Implementation broken into **10 phases** across **2 weeks**, with clear breakpoints for new chat sessions.

### 📋 **Phase 1: Foundation Setup** (Day 1 Morning)
#### Goals
- Set up core infrastructure without any functionality
- Ensure all imports and package structure work

#### Tasks
1. Create directory structure:
   ```
   lib/monitoring/
   ├── decorators/
   │   ├── __init__.py
   │   └── monitor.py (empty class)
   ├── serializers/
   │   ├── __init__.py
   │   └── smart.py (empty class)
   ├── queues/
   │   ├── __init__.py
   │   └── observability_queue.py (empty class)
   └── writers/
       ├── __init__.py
       └── sqlite_writer.py (empty class)
   ```

2. Create basic decorator stub:
   ```python
   def monitor(**kwargs):
       def decorator(func):
           return func  # Pass-through for now
       return decorator
   ```

3. Create test file structure:
   ```
   tests/monitoring/observability/
   ├── __init__.py
   ├── test_monitor_decorator.py
   ├── test_serializer.py
   └── test_queue.py
   ```

#### Deliverables
- [ ] All directories created
- [ ] Basic imports work: `from lib.monitoring.decorators import monitor`
- [ ] One simple test passing

#### Communication
- Screenshot of directory structure
- Result of `pytest tests/monitoring/observability/test_monitor_decorator.py::test_import`

### 📋 **Phase 2: Basic Decorator Implementation** (Day 1 Afternoon)
#### Goals
- Implement @monitor for sync functions only
- Capture function name and execution time
- No queue, no serialization yet

#### Tasks
1. Implement basic monitor decorator:
   - Capture function metadata
   - Measure execution time
   - Print to console (no queue yet)

2. Create tests:
   - Test decoration preserves function
   - Test timing measurement
   - Test metadata capture

#### Deliverables
- [ ] @monitor captures: function name, module, execution time
- [ ] 5 unit tests passing
- [ ] Console output shows trace data

#### Testing
```python
@monitor(process_group="test")
def example_function(x, y):
    return x + y

# Should print: "test.example_function executed in 0.001ms"
```

#### Communication
- Show test output
- Share console trace examples

### 📋 **Phase 3: Smart Serializer** (Day 2 Morning)
#### Goals
- Implement serialization for all data types
- Handle edge cases gracefully

#### Tasks
1. Implement smart serializer:
   - Primitives: str, int, float, bool, None
   - Collections: list, tuple, dict, set
   - NumPy arrays (shape only)
   - Pandas DataFrames (shape only)
   - Custom objects (class name)
   - Sensitive field masking

2. Create comprehensive tests:
   - Test each data type
   - Test truncation
   - Test sensitive field masking
   - Test circular references

#### Deliverables
- [ ] 15+ serializer tests passing
- [ ] Handles all data types from plan
- [ ] Max length truncation working

#### Communication
- Test results showing each type
- Example of sensitive data masking

### 🚨 **CHECKPOINT 1: Start New Chat** 🚨
*Context: Basic decorator + serializer complete*

### 📋 **Phase 4: Queue Implementation** (Day 2 Afternoon)
#### Goals
- Implement error-first queue strategy
- Zero loss for errors
- Overflow buffer for normal records

#### Tasks
1. Implement ObservabilityQueue:
   - Dual queue system (error + normal)
   - Overflow ring buffer
   - Queue metrics tracking

2. Tests:
   - Error records never dropped
   - Normal records overflow to buffer
   - Buffer recovery mechanism
   - Metrics accuracy

#### Deliverables
- [ ] Queue handles 10k+ records
- [ ] Errors always preserved
- [ ] Overflow recovery working
- [ ] 10 queue tests passing

#### Communication
- Queue metrics under load test
- Proof that errors never drop

### 📋 **Phase 5: SQLite Schema & Writer** (Day 3 Morning)
#### Goals
- Create database schema
- Implement batch writer thread
- Connect queue to database

#### Tasks
1. Create SQLite schema:
   - process_trace table
   - data_trace table
   - All indexes

2. Implement BatchWriter:
   - 10Hz drain cycle
   - Batch inserts (100 records)
   - WAL mode
   - Error handling

3. Integration:
   - Queue → Writer → Database
   - Transaction management

#### Deliverables
- [ ] Database created at `logs/observability.db`
- [ ] Writer thread running
- [ ] Data persisting to tables
- [ ] 8 writer tests passing

#### Testing
- Insert 1000 records, verify all saved
- Simulate writer crash, verify recovery

#### Communication
- Screenshot of database tables
- Performance metrics (inserts/second)

### 📋 **Phase 6: Decorator + Queue Integration** (Day 3 Afternoon)
#### Goals
- Connect decorator to queue
- Capture inputs and outputs
- Full data flow working

#### Tasks
1. Update @monitor to:
   - Serialize function arguments
   - Serialize return values
   - Send to queue
   - Handle exceptions

2. Integration tests:
   - Decorate various functions
   - Verify data in database
   - Test error handling

#### Deliverables
- [ ] Decorator → Queue → Database pipeline
- [ ] Arguments and results captured
- [ ] Exceptions recorded with traceback
- [ ] 15 integration tests passing

#### Communication
- Show actual database records
- Demonstrate error capture

### 🚨 **CHECKPOINT 2: Start New Chat** 🚨
*Context: Core system operational, moving to advanced features*

### 📋 **Phase 7: Advanced Function Support** (Day 4)
#### Goals
- Support async functions
- Support generators
- Support class methods

#### Tasks
1. Async function wrapper
2. Generator wrapper (capture first yield)
3. Class/static method support
4. Comprehensive tests

#### Deliverables
- [ ] Async functions traced
- [ ] Generators traced
- [ ] Class methods work
- [ ] 20 tests for advanced functions

#### Communication
- Examples of each function type
- Performance impact measurements

### 📋 **Phase 8: Production Hardening** (Day 5 Morning)
#### Goals
- Performance optimization
- Migration shims for legacy decorators
- Retention management

#### Tasks
1. Performance benchmarks:
   - Measure overhead
   - Optimize hot paths
   - Add sampling support

2. Legacy decorator shims:
   ```python
   def TraceTime(*a, **kw):
       return monitor(process_group="legacy.time", *a, **kw)
   ```

3. Retention job:
   - 6-hour cleanup
   - Performance impact

#### Deliverables
- [ ] <50µs overhead confirmed
- [ ] Legacy decorators migrated
- [ ] Retention job running
- [ ] Load test passing (25k records/min)

#### Communication
- Benchmark results
- Migration guide for teams

### 📋 **Phase 9: First Production Test** (Day 5 Afternoon)
#### Goals
- Deploy to 3 critical functions
- Monitor for 24 hours
- Gather feedback

#### Tasks
1. Decorate chosen functions:
   - `actant_main()`
   - `get_token()`
   - `update_instrument_data()`

2. Monitor:
   - Performance impact
   - Data quality
   - Queue stability

#### Deliverables
- [ ] 3 functions in production
- [ ] No performance degradation
- [ ] Useful traces captured
- [ ] Zero data loss confirmed

#### Communication
- Production metrics dashboard
- Sample traces from real usage

### 🚨 **CHECKPOINT 3: Start New Chat** 🚨
*Context: Core system in production, moving to UI*

### 📋 **Phase 10: Basic UI** (Week 2)
#### Goals
- Create Dash observability dashboard
- Table view with filtering
- Basic status indicators

#### Tasks
1. Create `apps/dashboards/observability/`
2. Implement:
   - Trace table (7 columns)
   - Date range filter
   - Status filter
   - Queue depth indicator

3. Server-side pagination

#### Deliverables
- [ ] Dashboard accessible at `/observability`
- [ ] Table shows real traces
- [ ] Filters work
- [ ] Handles 1M+ rows efficiently

#### Communication
- Screenshot of dashboard
- User feedback on UI

### 📊 **Success Metrics**

#### Phase Completion Criteria
Each phase is complete when:
1. All deliverables checked ✅
2. All tests passing 🟢
3. Performance targets met 🎯
4. Documentation updated 📝

#### Go/No-Go Decision Points
- **After Phase 3**: Basic system works? → Continue or redesign
- **After Phase 6**: Performance acceptable? → Continue or optimize
- **After Phase 9**: Production ready? → Expand or fix

#### Communication Protocol
1. **Daily Updates**: 
   - Morning: Today's phase goals
   - Evening: Results + any blockers

2. **Phase Completion**:
   - Test results screenshot
   - Key metrics
   - Next phase preview

3. **Checkpoint Communication**:
   - Summary of completed work
   - Any design changes needed
   - Context for next chat

### 🎯 **Why This Approach**

1. **Small, Testable Segments**: Each phase has 4-8 hours of work
2. **Clear Boundaries**: Natural breakpoints for context switching
3. **Risk Mitigation**: Problems caught early, easy to rollback
4. **Continuous Validation**: Tests at every phase
5. **Production-First**: Get to production quickly with minimal features

---

_This plan supersedes logsystem.md and incorporates all refinements from review cycle._ 