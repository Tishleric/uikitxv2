# FULLPNL Automation Implementation Plan

## Overview
Replacing the 10-script manual workflow with one idempotent service that (re)builds or incrementally refreshes the FULLPNL table whenever any upstream data source changes.

**Start Date**: January 2025  
**Status**: ✅ M1 Complete - Ready for M2

## Deliverables & Folder Layout
```
lib/trading/fullpnl/
│  __init__.py            
│  builder.py              – FULLPNLBuilder (orchestrator)
│  symbol_mapper.py        – all format conversions (Bloomberg ↔ Actant ↔ vtexp)
│  data_sources.py         – thin adapters for the three SQLite DBs (P&L, Spot Risk, Market)
│  validators.py           – central data-quality checks + sanitizers
│  triggers.py             – time/event trigger registration
│  monitor.py              – metrics, audit trail & alert hooks
tests/fullpnl/            – unit + integration tests
config/fullpnl_config.yaml – paths, schedules, constants
```

## Milestones

### M1 — Code Consolidation (green tests) ✅
**Goal**: Move duplicated DB-connection helpers & symbol parsing from scripts/master_pnl_table into modular components.  
**Success Criteria**: Unit tests prove identical outputs to original scripts for 3 sample symbols.

**Progress**:
- [x] Create package skeleton `lib/trading/fullpnl/`
- [x] Port symbol mapping logic to `symbol_mapper.py`
- [x] Port database connections to `data_sources.py`
- [x] Write unit tests comparing old vs new outputs
- [x] All tests green

**Notes**:
- *Started: January 2025*
- *Completed: January 2025*
- Created comprehensive SymbolMapper with all format conversions
- Implemented database adapters for all three SQLite sources
- Builder skeleton ready with table creation and symbol population
- Fixed symbol parsing for all edge cases (3MN5P format)
- All unit tests passing (7/7 tests)

### M2 — FULLPNLBuilder Skeleton (table exists) ✅ COMPLETE
**Goal**: Basic builder that can create/refresh table  
**Success Criteria**: Full rebuild succeeds end-to-end on current demo data (≈8 symbols)

**Completed**:
- [x] Table creation logic implemented
- [x] Symbol population from positions table
- [x] Implement column loaders (bid/ask, prices, Greeks)
- [x] Port logic from scripts 03-12 into builder methods
- [x] Full rebuild test passing with 8 symbols
- [x] Position columns: 100% coverage
- [x] Market prices: 75% coverage (6/8 symbols)
- [x] Spot risk data: 62.5% coverage (5/8 symbols - 2 missing due to strikes < 110.0)
- [x] Fixed futures delta_f = 63.0 applied correctly
- [x] **VERIFIED**: Our implementation correctly matches options to proper expiries
- [x] **FOUND BUG**: Manual scripts incorrectly match all options to 23JUL25

**Key Achievement**: The automated builder produces MORE ACCURATE results than the manual scripts by correctly using contract code to expiry mappings (3MN→18JUL25, VBYN→21JUL25, TYWN→23JUL25)

### M3 — Incremental Engine ⏳
**Goal**: Detect new/changed rows via hashes  
**Success Criteria**: Average refresh time ≤ 2s on 1,000 positions

### M4 — Trigger Integration ⏳
**Goal**: Time and event-based triggers  
**Success Criteria**: Automatic updates on schedule and data changes

### M5 — Data Validation & Monitoring ⏳
**Goal**: Quality checks and observatory integration  
**Success Criteria**: Validation failures logged, alerts raised

### M6 — TYU5 Coexistence Hardening ⏳
**Goal**: Seamless integration with TYU5 migration  
**Success Criteria**: FULLPNL refresh picks up TYU5 changes in <10s

## Implementation Log

### January 2025 - Session 1
- Created plan tracking document
- Starting M1 implementation
- Created package structure:
  - `lib/trading/fullpnl/__init__.py` - Package initialization
  - `lib/trading/fullpnl/symbol_mapper.py` - Consolidated symbol parsing from scripts
  - `lib/trading/fullpnl/data_sources.py` - Database adapters for P&L, Spot Risk, Market Prices
  - `lib/trading/fullpnl/builder.py` - FULLPNLBuilder skeleton
  - `tests/fullpnl/test_symbol_mapper.py` - Unit tests for symbol mapping

**Key Accomplishments**:
1. Extracted and centralized all symbol format conversion logic
2. Created unified database interfaces with common patterns
3. Implemented basic builder that can create table and populate symbols
4. Type hints throughout for better maintainability

**Challenges Encountered**:
- Mypy type checking issues with Optional types (parse methods return Optional[ParsedSymbol])
- Need to add proper type guards in tests

### January 2025 - Session 1 (Completion)
- Fixed all remaining M1 issues
- Updated symbol parser to handle all edge cases:
  - 3MN5P format (numeric prefix + letters + digit + option type)
  - VBYN25P3 format (letters + digits + option type + strike identifier)
  - Contract mapping with numeric prefixes (3MN5 -> 3MN -> 18JUL25)
- Created comprehensive test script `scripts/test_fullpnl_automation.py`
- All tests passing (100% success rate)
- Verified database connections and basic builder functionality

**Test Results**:
- Symbol mapping: ✅ All formats parsing correctly
- Database connections: ✅ All three databases accessible
- Builder basics: ✅ Table creation and symbol population working
- Unit tests: ✅ 7/7 tests passing

---

## Idiosyncrasies & Solutions

### Symbol Format Challenges
**Issue**: Multiple symbol formats in use across systems  
**Examples**:
- Bloomberg: "VBYN25P3 110.250 Comdty"
- Actant: "XCME.ZN3.18JUL25.110:25.P"
- vtexp_mappings: "XCME.ZN2.18JUL25" or "XCME.ZN.JUL25"

**Solution**: Centralized SymbolMapper with comprehensive regex patterns and mapping dictionaries

### Data Quality Issues
**Issue**: Spot risk data ~75% coverage, NaN values, placeholder 20.0 values  
**Solution**: Use SQLite database instead of CSV, implement graceful NULL handling

### Date/Time Logic
**Issue**: px_settle requires T+1 logic with weekend/holiday handling  
**Solution**: Reuse existing helper functions, dynamic date detection

### Type Checking with Optional Returns
**Issue**: Parser methods return Optional[ParsedSymbol], causing mypy errors when accessing attributes  
**Solution**: Add type guards (`assert parsed is not None`) after None checks in tests

### Complex Bloomberg Option Formats
**Issue**: Multiple Bloomberg option formats with different patterns
- 3MN5P 110.000 (numeric prefix + letters + digit + type)
- VBYN25P3 110.250 (letters + digits + type + digit)

**Solution**: Multiple regex patterns in parse_bloomberg_symbol to handle each format

---

## Risk Register

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Symbol chaos | High | Centralized SymbolMapper with exhaustive tests | ✅ |
| Data drift during migration | Medium | Work off canonical positions table only | ⏳ |
| Performance degradation | Medium | Stream queries, partial refresh | ⏳ |
| Concurrent writers | Low | BEGIN IMMEDIATE locks, retry logic | ⏳ |

---

## Testing Strategy

### Unit Tests
- [x] Symbol mapping conversions
- [ ] Database adapter queries
- [ ] Validation logic
- [ ] Individual column loaders

### Integration Tests
- [ ] Full table rebuild
- [ ] Incremental updates
- [ ] Trigger mechanisms
- [ ] TYU5 compatibility

### Performance Tests
- [ ] 1,000 position refresh time
- [ ] 10,000 position memory usage
- [ ] Concurrent access handling

---

## Notes & Decisions

- NO modification to existing master_pnl_table/ scripts during development
- Scripts become regression test reference, deleted only after parity proven
- ClosedPositionTracker integration preserved
- Compatible with in-flight TYU5 migration work
- Using Path objects throughout for cross-platform compatibility
- Row factory set to sqlite3.Row for dict-like column access
- Contract mapping handles both numeric prefixes (3MN) and suffixes (VBYN25) 