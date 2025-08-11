# Price Updater Profiling Guide

## Quick Start

Run this to profile the price updater and find the 14-second bottleneck:

```bash
tests\diagnostics\run_price_updater_profile.bat
```

## What This Does

### 1. Check Database Settings First
```bash
python tests\diagnostics\check_db_settings.py
```
This shows current SQLite configuration (read-only check).

### 2. Capture Real Messages
```bash
python tests\diagnostics\capture_redis_messages.py 3
```
- Captures 3 real messages from Redis
- Requires spot risk watcher to be running
- Saves to `captured_messages/` directory

### 3. Profile Offline (Safest)
```bash
python tests\diagnostics\profile_current_implementation.py --offline
```
- Uses captured messages
- No live connections
- Shows exactly where time is spent

### 4. Profile Live (Optional)
```bash
python tests\diagnostics\profile_current_implementation.py --live
```
- Creates separate profiling instance
- Does NOT interfere with production
- Stops after 3 messages

## Expected Output

You'll see something like:
```
Timing Breakdown:
- Pickle loads: 0.001s
- Arrow deserialize: 0.012s
- Extract prices (10 symbols): 0.087s
- Database updates: 13.900s  ← THE PROBLEM
- TOTAL: 14.000s

Top Functions by Cumulative Time:
1. sqlite3.Connection.commit - 13.8s (10 calls)
2. cursor.execute - 0.9s (10 calls)
```

## What We're Looking For

The 14-second delay is likely in one of:
1. **conn.commit()** - If synchronous=FULL, each commit forces disk sync
2. **Individual commits** - 10 symbols = 10 commits = 10x overhead
3. **Connection creation** - New connection per message

## Production Safety

- **NO production code is modified**
- All profiling uses wrapper classes
- Captured messages allow offline testing
- Limited to 3 messages to minimize impact
- Clear rollback plan in ROLLBACK_PLAN.md

## Next Steps

After identifying the bottleneck:
1. Test optimizations offline first
2. Implement minimal fix (likely batch commits)
3. Verify improvement with same profiling tools