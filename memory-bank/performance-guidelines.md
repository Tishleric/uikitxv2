# Performance Guidelines for Observability System

## Executive Summary

The observability system can handle **418k+ records/second** at the queue level but is bottlenecked by SQLite at **~1,089 operations/second**. This guide provides practical strategies to work within these constraints.

## Performance Characteristics

### System Bottlenecks

```
Function Call → Queue → BatchWriter → SQLite → Disk
   <50μs       418k/s     10Hz       1,089/s    ~100MB/s
```

**Key Insight**: SQLite is the bottleneck, not the monitoring infrastructure.

### Measured Performance

- **Decorator Overhead**: <50μs per function call
- **Queue Throughput**: 418,662 records/second capability
- **SQLite Writer**: 1,089 operations/second sustained
- **Memory Usage**: ~1KB per record in queue

## Tuning Parameters

### 1. Drain Interval (BatchWriter)

Current default: **0.1 seconds (10Hz)**

```python
# In sqlite_writer.py
time.sleep(0.1)  # Drain interval
```

**Tuning Guide**:

| Use Case | Drain Interval | Batch Size | Latency | Notes |
|----------|---------------|------------|---------|-------|
| Low Latency | 0.05s (20Hz) | 50 | ~50ms | For near real-time monitoring |
| Balanced | 0.1s (10Hz) | 100 | ~100ms | **Current default** |
| High Throughput | 0.5s (2Hz) | 500 | ~500ms | Maximum batching efficiency |

**Trade-offs**:
- **Shorter intervals**: Lower latency, more DB writes, higher overhead
- **Longer intervals**: Higher latency, fewer DB writes, risk of queue buildup

### 2. Sampling Rates

Use sampling for high-frequency functions:

```python
@monitor(sample_rate=0.01)  # Monitor 1% of calls
def process_market_tick(price):
    # Called 100k times/second
    pass
```

**Sampling Strategy Matrix**:

| Function Frequency | Recommended Sample Rate | Example Use Case |
|-------------------|------------------------|------------------|
| > 10k/sec | 0.001 - 0.01 (0.1-1%) | Market data ticks |
| 1k-10k/sec | 0.01 - 0.1 (1-10%) | Order book updates |
| 100-1k/sec | 0.1 - 0.5 (10-50%) | Risk calculations |
| < 100/sec | 1.0 (100%) | Trade execution |

### 3. Process Groups for Selective Monitoring

Use process groups to categorize and potentially filter:

```python
# Critical path - always monitor
@monitor(process_group="trading.execution")
def execute_trade(order):
    pass

# Hot path - sample aggressively  
@monitor(process_group="market.data", sample_rate=0.001)
def on_price_update(symbol, price):
    pass

# Analytics - monitor in development only
@monitor(process_group="analytics.research")
def backtest_strategy(params):
    pass
```

## Real-World Scenarios

### Scenario 1: High-Frequency Trading System

**Challenge**: 50k price updates/second across 100 symbols

**Solution**:
```python
# Price handler with aggressive sampling
@monitor(
    process_group="market.data.prices",
    sample_rate=0.001,  # 0.1% sampling = 50 events/second
)
def handle_price_update(symbol, bid, ask):
    update_order_book(symbol, bid, ask)

# Critical execution path - full monitoring
@monitor(process_group="trading.execution")
def execute_order(order):
    # This runs 100x/second - all captured
    return send_to_exchange(order)
```

**Configuration**:
- Drain interval: 0.5s (buffer more)
- Batch size: 500
- Result: ~100 records/second to SQLite

### Scenario 2: Real-Time Analytics Dashboard

**Challenge**: Need low-latency monitoring for user experience

**Solution**:
```python
# UI interactions - full monitoring with fast drain
@monitor(process_group="ui.interactions")
def handle_button_click(button_id):
    # User clicks ~10/second - all captured
    return process_action(button_id)

# Background calculations - sampled
@monitor(
    process_group="analytics.calculations",
    sample_rate=0.1  # 10% sampling
)
def recalculate_portfolio():
    # Runs every 100ms, sample 1 in 10
    return compute_risk_metrics()
```

**Configuration**:
- Drain interval: 0.05s (20Hz for low latency)
- Batch size: 50
- Result: Near real-time UI monitoring

### Scenario 3: Batch Processing System

**Challenge**: Process millions of records efficiently

**Solution**:
```python
# Batch job monitoring
@monitor(process_group="batch.etl")
def process_batch(batch_id):
    # Runs once per batch - always monitor
    return transform_records(batch_id)

# Individual record processing - heavily sampled
@monitor(
    process_group="batch.records",
    sample_rate=0.0001  # 0.01% = 1 in 10,000
)
def process_record(record):
    # Millions of calls, sample tiny fraction
    return validate_and_store(record)
```

**Configuration**:
- Drain interval: 1.0s (maximize batching)
- Batch size: 1000
- Result: Minimal overhead on batch jobs

## Performance Best Practices

### 1. Identify Hot Paths Early

```python
# During development - monitor everything
@monitor()  # Default: sample_rate=1.0

# Before production - add sampling to hot paths
@monitor(sample_rate=0.01)  # Sample 1%
```

### 2. Use Process Groups Wisely

```python
# Good: Specific, hierarchical groups
@monitor(process_group="trading.fx.spot.execution")
@monitor(process_group="risk.var.calculation")

# Bad: Too generic
@monitor(process_group="functions")
@monitor(process_group="important")
```

### 3. Configure by Environment

```python
# Production configuration
if ENVIRONMENT == "production":
    config = {
        "market_data_sampling": 0.001,
        "drain_interval": 0.5,
        "batch_size": 500,
    }
else:
    # Development - monitor everything
    config = {
        "market_data_sampling": 1.0,
        "drain_interval": 0.1,
        "batch_size": 100,
    }
```

### 4. Monitor Queue Depth

```python
# Check queue statistics periodically
stats = observability_queue.get_stats()
if stats["normal_queue_size"] > 8000:  # 80% full
    logger.warning(f"Queue filling up: {stats}")
    # Consider increasing sampling or drain rate
```

## Scaling Beyond SQLite

When you hit SQLite limits (~1000 ops/sec), consider:

1. **Short Term**: Increase sampling rates
2. **Medium Term**: Use separate SQLite files by process group
3. **Long Term**: Graduate to TimescaleDB or ClickHouse

```python
# Future: Pluggable writers
if daily_volume > 100_000_000:
    writer = ClickHouseWriter(...)
else:
    writer = SQLiteWriter(...)
```

## Troubleshooting Performance

### Symptom: Queue Memory Growing

**Diagnosis**: Writer can't keep up
```python
stats = observability_queue.get_stats()
# If recovered_count keeps increasing, queue is overflowing
```

**Solutions**:
1. Increase batch size
2. Increase drain interval  
3. Add sampling to hot functions

### Symptom: High Latency in UI

**Diagnosis**: Drain interval too high
```python
# Current: 0.5s drain = 500ms max latency
# Need: <100ms for responsive UI
```

**Solution**: Decrease drain interval for UI process groups

### Symptom: Database File Growing Fast

**Diagnosis**: Too much data captured
```bash
# Check data rate
sqlite3 observability.db "SELECT COUNT(*) FROM process_trace WHERE ts > datetime('now', '-1 minute')"
```

**Solutions**:
1. Add sampling to verbose functions
2. Reduce retention period
3. Exclude debug process groups in production

## Summary

The observability system is designed to be tuned for your specific needs:

- **Default Settings**: Good for most applications
- **Hot Path Sampling**: Essential for high-frequency operations  
- **Process Groups**: Enable targeted monitoring strategies
- **Drain Tuning**: Balance latency vs throughput

Remember: It's better to sample intelligently than to drop data randomly. Use these guidelines to maintain complete observability within performance constraints. 