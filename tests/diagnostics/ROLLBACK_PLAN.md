# Rollback Plan for Price Updater Profiling

## Current Status
- **NO PRODUCTION CODE HAS BEEN MODIFIED YET**
- All profiling is done through wrapper classes
- Original services remain untouched

## Files Created (Safe to Delete)
```
tests/diagnostics/
├── capture_redis_messages.py          # Message capture tool
├── profile_current_implementation.py  # Profiling wrapper
├── captured_messages/                 # Captured test data
└── profiles/                         # Profile outputs
```

## If Temporary Production Changes Are Needed

### Minimal Timing Addition (IF NEEDED)
If we need to add timing to `update_current_price()` in production:

1. **File**: `lib/trading/pnl_fifo_lifo/data_manager.py`
2. **Backup Command**: 
   ```bash
   copy lib\trading\pnl_fifo_lifo\data_manager.py lib\trading\pnl_fifo_lifo\data_manager.py.backup
   ```

3. **Minimal Change** (lines 623-628):
   ```python
   # ADD these 3 lines for timing
   import time
   t_start = time.time()
   
   cursor.execute("""
       INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
       VALUES (?, 'now', ?, ?)
   """, (symbol, price, timestamp))
   
   # ADD this line
   t_execute = time.time()
   
   conn.commit()
   
   # ADD these 2 lines
   t_commit = time.time()
   logger.debug(f"Price update for {symbol}: execute={t_execute-t_start:.3f}s, commit={t_commit-t_execute:.3f}s")
   ```

4. **Rollback Command**:
   ```bash
   copy lib\trading\pnl_fifo_lifo\data_manager.py.backup lib\trading\pnl_fifo_lifo\data_manager.py
   ```

## Safe Testing Approach

### Step 1: Capture Messages (No Risk)
```bash
python tests\diagnostics\capture_redis_messages.py 5
```
This only reads from Redis, no modifications.

### Step 2: Offline Profiling (No Risk)
```bash
python tests\diagnostics\profile_current_implementation.py --offline
```
This profiles using captured messages, no live connection.

### Step 3: Live Profiling (Minimal Risk)
```bash
python tests\diagnostics\profile_current_implementation.py --live
```
This creates a separate price updater instance for profiling.
- Does NOT interfere with production price updater
- Processes same messages but separately
- Stops after 3 messages

## Emergency Stop

If anything goes wrong:
1. **Ctrl+C** to stop the profiling script
2. Delete all files in `tests/diagnostics/`
3. If production code was modified:
   ```bash
   copy lib\trading\pnl_fifo_lifo\data_manager.py.backup lib\trading\pnl_fifo_lifo\data_manager.py
   ```

## Production Safety Checklist

- [ ] Backup any files before modification
- [ ] Test changes offline first
- [ ] Monitor production services during testing
- [ ] Have rollback commands ready
- [ ] Limit profiling duration (3 messages max)
- [ ] No business logic changes, only timing

## Contact for Issues

If issues arise:
1. Stop all diagnostic scripts
2. Check if production price_updater_service is still running
3. Restore backups if any files were modified
4. Check Redis connectivity