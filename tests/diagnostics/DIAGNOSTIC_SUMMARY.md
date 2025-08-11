# Price Updater Latency Diagnostic Summary

## Problem Statement
- **Symptom**: Live prices in FRGMonitor dashboard are severely delayed
- **Pattern**: Latency increases linearly - 0.001s → 16s → 30s → 44s → 58s (+14s per message)
- **Impact**: Dashboard shows stale prices; delay accumulates over time

## Root Cause Analysis
The linear accumulation pattern (+14 seconds per message) strongly indicates:
1. **Sequential Processing**: Price updater processes messages one at a time
2. **Processing Time > Arrival Rate**: Each message takes ~14s to process
3. **Queue Buildup**: Messages backing up, each waits for previous to complete

## Diagnostic Approach

### 1. Created Three Diagnostic Tools

#### A. test_database_bottleneck.py
- Tests database operations in isolation
- Measures single update vs batch performance
- Checks WAL mode and concurrent access
- Tests file system I/O performance

#### B. monitor_price_pipeline.py
- Non-intrusive live monitoring
- Tracks Redis message flow in real-time
- Measures latency without interference
- Monitors database lock events

#### C. price_updater_diagnostic.py
- Full pipeline simulation with timing
- Breaks down each operation:
  - Pickle deserialization
  - Arrow deserialization
  - Symbol translation
  - Database updates
- Identifies slowest component

### 2. Key Hypotheses to Test

#### Hypothesis 1: Database Bottleneck (Most Likely)
**Evidence**: 14-second delay matches typical slow database commit
**Possible Causes**:
- Individual commits per symbol (no batching)
- WAL mode disabled (lock contention)
- Synchronous=FULL mode (excessive fsync)
- Slow file system (HDD vs SSD)

#### Hypothesis 2: Redis Configuration Issue
**Evidence**: 'localhost' vs '127.0.0.1' inconsistency
**Possible Causes**:
- DNS resolution delays (IPv6 vs IPv4)
- Connection establishment overhead
- No connection pooling

#### Hypothesis 3: Symbol Translation
**Evidence**: RosettaStone database lookups
**Possible Causes**:
- No caching of translations
- Database query per symbol
- Connection overhead

## How to Run Diagnostics

### Quick Start
```bash
# Windows
tests\diagnostics\run_all_diagnostics.bat

# Or Python
python tests\diagnostics\run_diagnostics.py
```

### Individual Tests
```bash
# 1. Database test (fastest, most likely culprit)
python tests\diagnostics\test_database_bottleneck.py

# 2. Live monitoring (30 seconds)
python tests\diagnostics\monitor_price_pipeline.py --duration 30 --db-monitor

# 3. Full simulation
python tests\diagnostics\price_updater_diagnostic.py
```

## What to Look For

### In Database Test Results:
- **Single update time > 1 second** = Database is the bottleneck
- **WAL mode = delete** = Lock contention likely
- **Synchronous = 2 (FULL)** = Excessive disk syncing
- **Concurrent locks > 0** = Write contention

### In Pipeline Monitor:
- **Latency growing over time** = Processing bottleneck confirmed
- **Consistent 14s latency** = Systemic issue
- **"Database locked" messages** = Contention problem

### In Full Simulation:
- **db_total > 10 seconds** = Database operations are slow
- **db_commit > 10 seconds** = Commit is the bottleneck
- **symbol translation > 1 second** = Translation needs caching

## Expected Findings

Based on the symptoms, we expect to find:

1. **Database commits taking 10-14 seconds**
   - Due to synchronous=FULL mode
   - Or file system sync delays
   - Or lock contention without WAL

2. **Individual commits per symbol**
   - No transaction batching
   - Excessive overhead

3. **No connection pooling**
   - Connection creation overhead
   - Resource exhaustion

## Recommended Fixes (Pending Diagnosis)

### If Database is Bottleneck:
1. Enable WAL mode: `PRAGMA journal_mode=WAL`
2. Set synchronous=NORMAL: `PRAGMA synchronous=NORMAL`
3. Batch updates in single transaction
4. Add connection pooling

### If Redis is Bottleneck:
1. Standardize to '127.0.0.1' (avoid DNS)
2. Add connection pooling
3. Increase buffer sizes

### If Symbol Translation is Slow:
1. Add in-memory caching
2. Preload common symbols
3. Batch lookups

## Next Steps

1. **Run diagnostics** to confirm exact bottleneck
2. **Share results** for analysis
3. **Implement targeted fix** based on findings
4. **Re-test** to verify improvement

The diagnostic tools are designed to be:
- **Safe**: Read-only, no production changes
- **Fast**: Complete in < 10 minutes
- **Comprehensive**: Cover all likely causes
- **Actionable**: Provide clear next steps