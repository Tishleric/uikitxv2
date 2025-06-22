# Observability Dashboard Implementation Plan
Generated: 2025-01-14

## 1. Goal & Architecture Overview

**Objective**: Build production-ready observability dashboard within `apps/dashboards/main/app.py` with seamless integration alongside existing pages.

**Key Design Requirements**:
- **7 Canonical Columns**: Process | Data | Data Type | Data Value | Timestamp | Status | Exception
- **5-Tab Structure**: Overview → Trace Explorer → (Skip Flow Viz) → Code Inspector → Alerts
- **Staleness Detection**: Compare consecutive values, flag if repeated >5 times
- **Parent-Child Traces**: Expandable rows showing call hierarchy
- **Integration Strategy**: Add new "Observability" sidebar entry, keep old "Logs" page until fully validated

## 2. Implementation Phases

### Phase A: Foundation & Navigation (Day 1)
1. **Add sidebar entry** in `create_sidebar()`:
   ```python
   {"id": "nav-observability", "label": "Observability", "icon": "📊"},
   ```

2. **Create base container structure**:
   ```python
   def create_observability_content():
       return Container(
           id="obs-main-container",
           children=[
               # Tab structure
               Tabs(
                   id="obs-tabs",
                   tabs=[
                       ("Overview", create_obs_overview_tab()),
                       ("Trace Explorer", create_obs_trace_tab()),
                       ("Code Inspector", create_obs_code_tab()),
                       ("Alerts", create_obs_alerts_tab())
                   ],
                   theme=default_theme
               ).render(),
               # Hidden stores for state
               dcc.Store(id="obs-refresh-interval-store", data=5000),
               dcc.Store(id="obs-filter-store", data={}),
               dcc.Interval(id="obs-refresh-timer", interval=5000)
           ]
       )
   ```

3. **Wire navigation** in `handle_navigation()` callback

### Phase B: Overview Tab (Day 2)
Components:
- **Metrics Grid** (2x2):
  - Error Rate: Sparkline + current value
  - Throughput: Traces/sec with trend
  - Queue Depth: Current buffer size
  - Writer Status: OK/DELAYED/CIRCUIT_OPEN

- **Recent Errors Table** (last 10):
  - Timestamp | Process | Exception (truncated)
  - Click → opens Trace Explorer filtered

- **Process Group Summary**:
  - Pie chart of traces by group
  - Click segment → filter traces

### Phase C: Trace Explorer Tab (Day 3-4)
**Core Requirements**:
1. **7-Column DataTable** with server-side pagination
2. **Filter Controls**:
   - Time range selector (presets: 5m, 1h, 6h, 24h)
   - Process group dropdown
   - Error-only toggle
   - Search box for process name

3. **Query Optimization**:
   ```sql
   CREATE INDEX idx_trace_explorer ON data_trace(
       timestamp DESC,
       status,
       process_group
   );
   ```

4. **Parent-Child Expansion**:
   - Click row → expand to show child traces
   - Indentation to show hierarchy
   - Shared trace_id links parent/child

### Phase D: Code Inspector Tab (Day 5)
**Features**:
1. **Function selector** (autocomplete from traced functions)
2. **Split pane**:
   - Left: Syntax-highlighted source code
   - Right: Performance metrics table

3. **Metrics shown**:
   - Call count
   - Avg duration
   - Error rate
   - P50/P95/P99 latencies
   - Memory delta

4. **Historical graph** (last 24h of performance)

### Phase E: Alerts Tab (Day 6)
**Staleness Detection Rules**:
- Rule builder (process + variable + threshold)
- Active alerts table
- Webhook configuration
- Compare consecutive values approach

### Phase F: Testing & Migration (Day 7-8)
1. **Integration tests** for each tab
2. **Performance benchmarks** with 100k rows
3. **Side-by-side comparison** with old logs page
4. **Gradual rollout**:
   - Week 1: Both pages available
   - Week 2: Deprecation notice on old page
   - Week 3: Remove old page

## 3. Critical Implementation Details

### Database Connection Management
- Singleton connection pool
- WAL mode enabled
- 5-second query timeout
- Error boundaries on all queries

### Performance Caps
- Max 10k rows per query
- 5-second query timeout
- Client-side caching of process lists
- Debounced filter inputs (300ms)

## 4. File Changes Summary
1. `apps/dashboards/main/app.py`:
   - Add `create_observability_content()` (~200 LOC)
   - Add navigation handler case (~5 LOC)
   - Add 6 new callbacks (~300 LOC)

2. `memory-bank/observability-dashboard-plan.md` (THIS FILE)

3. `memory-bank/activeContext.md`:
   - Update focus to "Observability Dashboard Implementation"

4. `memory-bank/code-index.md`:
   - Document new functions/components

5. `logs/main_dashboard_logs.db`:
   - Add new indices for performance

## 5. Success Metrics
- [ ] Overview page loads in <200ms with 100k rows
- [ ] Trace filtering returns results in <500ms
- [ ] No UI freezes during refresh
- [ ] All existing pages continue working
- [ ] Memory usage stays under +50MB
- [ ] Parent-child expansion works smoothly

## 6. Rollback Plan
If issues arise:
1. Feature flag: `ENABLE_NEW_OBSERVABILITY = False`
2. Revert navigation handler to skip new page
3. Old logs page remains untouched
4. No shared database schema changes

This plan prioritizes **incremental delivery** and **zero disruption** to existing functionality.

## 7. MVC Architecture Approach
- **Model**: SQLite queries wrapped in safe_query(), connection pooling
- **View**: Dash components (DataTable, Graph, Container)
- **Controller**: Callbacks handling user interactions and data flow
- **Separation**: No business logic in callbacks, all queries in helper functions 