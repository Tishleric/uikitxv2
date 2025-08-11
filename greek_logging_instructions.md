# Greek Value Logging Instructions

## Setup Complete!

The Greek value logging system has been set up. Here's how to use it:

### 1. Start the Pipeline with Logging

Run the pipeline as usual:
```
run_pipeline_live.bat
```

The spot risk watcher will now log detailed Greek values for these positions:
- TJWQ25C1 112.5
- TYWQ25C1 112.5  
- TYWQ25C1 112.25

### 2. Where to Find Logs

**Console Output**: Look for lines starting with "GREEK_TRACE" in the Spot Risk Watcher window

**Log Files**: Detailed logs are saved to:
```
logs/greek_trace/greek_values_YYYYMMDD_HHMMSS.log
```

### 3. What to Look For

The logs will show Greek values at each stage:
1. **API CALCULATION RESULT** - Raw values from the Greek calculator
2. **DATAFRAME VALUES** - Values stored in the DataFrame
3. **REDIS PUBLISH** - Values being sent to Redis
4. **AGGREGATOR RECEIVED** - Values received by the aggregator

### 4. Key Values to Compare

For TJWQ25C1 112.5 (120 contracts), expected values:
- Natural delta: ~0.024
- After 1000x scaling: ~24
- After position weighting (120x): ~2,880

If you see ~0.288, that's 10,000x too small!

### 5. To Add More Logging

To monitor the aggregator side, add this import to positions_aggregator.py:
```python
from lib.trading.actant.spot_risk.greek_monitor import monitor_dataframe_greeks
```

Then call it when processing Greek data:
```python
monitor_dataframe_greeks(df, "AGGREGATOR RECEIVED")
```

### 6. To Disable Logging

Remove or comment out this line in run_spot_risk_watcher.py:
```python
os.environ['GREEK_TRACE_ENABLED'] = '1'
```
