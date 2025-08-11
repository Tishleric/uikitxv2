# Price Updater Diagnostic Guide

## Overview
We've created three diagnostic tools to identify the source of the 14-second latency in the price updater pipeline:

1. **price_updater_diagnostic.py** - Simulates the full pipeline with detailed timing
2. **monitor_price_pipeline.py** - Monitors live pipeline without interference
3. **test_database_bottleneck.py** - Focused database performance tests

## Quick Start

### 1. First, run the database bottleneck test (fastest, most likely culprit):
```bash
cd Z:\uikitxv2
python tests/diagnostics/test_database_bottleneck.py
```

This will:
- Test single update performance
- Compare batch vs individual commits
- Check WAL mode status
- Test concurrent access
- Provide optimization suggestions

### 2. Monitor the live pipeline (non-intrusive):
```bash
# Monitor for 5 minutes with database lock monitoring
python tests/diagnostics/monitor_price_pipeline.py --duration 300 --db-monitor
```

This shows:
- Real-time message latencies
- Message rates
- Database lock events
- Queue depth

### 3. Run the full diagnostic simulation:
```bash
python tests/diagnostics/price_updater_diagnostic.py
```

This will:
- Simulate spot risk messages
- Time each processing step
- Identify the slowest operation

## Interpreting Results

### If database is the bottleneck:
Look for:
- Single update time > 1 second
- WAL mode disabled
- High lock count in concurrent test
- Slow file system speeds

### If Redis is the bottleneck:
Look for:
- High deserialization times
- Growing latencies over time
- Connection timeouts

### If symbol translation is slow:
Look for:
- Translation times > 100ms
- No caching behavior

## Immediate Actions (No Code Changes)

1. **Check database configuration:**
```bash
sqlite3 trades.db "PRAGMA journal_mode;"
sqlite3 trades.db "PRAGMA synchronous;"
sqlite3 trades.db "PRAGMA busy_timeout;"
```

2. **Enable WAL mode if not already:**
```bash
sqlite3 trades.db "PRAGMA journal_mode=WAL;"
```

3. **Monitor system resources during test:**
```bash
# In another terminal
iostat -x 1
```

## Expected Findings

Based on the linear latency accumulation pattern (14s per message), we expect to find:

1. **Database commits taking 10-14 seconds each**
   - Likely due to synchronous=FULL mode
   - Or file system sync delays
   - Or lock contention without WAL

2. **Individual commits instead of batching**
   - Each symbol update commits separately
   - No transaction grouping

3. **Connection overhead**
   - Creating new connection per update
   - No connection pooling

## Next Steps

After running diagnostics:

1. Share the output logs
2. We'll identify the specific bottleneck
3. Implement targeted fix (likely batch commits + WAL mode)
4. Re-test to confirm improvement