"""
Setup comprehensive Greek value logging throughout the pipeline
This will help trace where the 10,000x discrepancy occurs
"""
import os
import re
import shutil
from datetime import datetime

def setup_greek_logging():
    """Add detailed Greek value logging to key points in the pipeline"""
    
    print("=" * 80)
    print("SETTING UP COMPREHENSIVE GREEK VALUE LOGGING")
    print("=" * 80)
    print()
    
    # Create log directory
    log_dir = "logs/greek_trace"
    os.makedirs(log_dir, exist_ok=True)
    
    # 1. Create a custom logger configuration
    logger_config = '''"""
Greek Value Trace Logger Configuration
"""
import logging
import os
from datetime import datetime

# Create formatters and handlers
def setup_greek_logger():
    logger = logging.getLogger('greek_trace')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - GREEK_TRACE - %(message)s')
    console_handler.setFormatter(console_format)
    
    # File handler
    log_file = f"logs/greek_trace/greek_values_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Global greek trace logger
greek_logger = setup_greek_logger()
'''
    
    with open("lib/trading/actant/spot_risk/greek_logger.py", "w") as f:
        f.write(logger_config)
    print("✓ Created greek_logger.py")
    
    # 2. Modify spot risk watcher to enable detailed logging
    print("\nModifying run_spot_risk_watcher.py...")
    watcher_file = "run_spot_risk_watcher.py"
    
    if os.path.exists(watcher_file):
        with open(watcher_file, 'r') as f:
            content = f.read()
        
        # Add import for greek logger
        if 'from lib.trading.actant.spot_risk.greek_logger import greek_logger' not in content:
            # Add after other imports
            import_pos = content.find('from lib.trading.actant.spot_risk.file_watcher')
            if import_pos > 0:
                content = content[:import_pos] + 'from lib.trading.actant.spot_risk.greek_logger import greek_logger\n' + content[import_pos:]
        
        # Set environment variable for detailed Greek logging
        env_addition = '''
    # Enable detailed Greek logging
    os.environ['GREEK_TRACE_ENABLED'] = '1'
    greek_logger.info("=" * 80)
    greek_logger.info("GREEK VALUE TRACING ENABLED")
    greek_logger.info("Monitoring key positions for Greek value transformations")
    greek_logger.info("=" * 80)
'''
        
        # Add after the print statements
        if 'os.environ[\'GREEK_TRACE_ENABLED\']' not in content:
            pos = content.find('print("\\nPress Ctrl+C to stop\\n")')
            if pos > 0:
                end_pos = content.find('\n', pos) + 1
                content = content[:end_pos] + env_addition + content[end_pos:]
        
        with open(watcher_file, 'w') as f:
            f.write(content)
        print("✓ Modified run_spot_risk_watcher.py")
    
    # 3. Create a monitoring patch for the calculator
    print("\nCreating calculator monitoring patch...")
    
    calculator_patch = '''"""
Greek calculation monitoring patch
Import this to add detailed logging to Greek calculations
"""
import os
import logging
from functools import wraps

# Only enable if environment variable is set
if os.environ.get('GREEK_TRACE_ENABLED') == '1':
    from lib.trading.actant.spot_risk.greek_logger import greek_logger
    
    # Positions to monitor in detail
    MONITORED_POSITIONS = [
        'TJWQ25C1 112.5',
        'TYWQ25C1 112.5',
        'TYWQ25C1 112.25'
    ]
    
    def log_greek_calculation(instrument_key, greek_values, stage=""):
        """Log Greek values for monitored positions"""
        for pos in MONITORED_POSITIONS:
            if pos in str(instrument_key):
                greek_logger.info(f"")
                greek_logger.info(f"{'='*60}")
                greek_logger.info(f"GREEK VALUES - {stage}")
                greek_logger.info(f"Instrument: {instrument_key}")
                greek_logger.info(f"{'='*60}")
                
                # Log each Greek value
                for greek_name, value in greek_values.items():
                    if value is not None:
                        greek_logger.info(f"  {greek_name:.<20} {value:>15.6f}")
                    else:
                        greek_logger.info(f"  {greek_name:.<20} {'None':>15}")
                
                # Check for scaling
                if 'delta_y' in greek_values and greek_values['delta_y'] is not None:
                    delta_val = greek_values['delta_y']
                    if abs(delta_val) > 1:
                        # Likely already scaled
                        greek_logger.info(f"")
                        greek_logger.info(f"  SCALING ANALYSIS:")
                        greek_logger.info(f"    delta_y = {delta_val:.6f}")
                        greek_logger.info(f"    If natural delta ~0.024, then scaling = {delta_val/0.024:.0f}x")
                
                greek_logger.info(f"{'='*60}")
                break
    
    def monitor_greek_api_results(original_method):
        """Decorator to monitor Greek API results"""
        @wraps(original_method)
        def wrapper(self, *args, **kwargs):
            result = original_method(self, *args, **kwargs)
            
            # Log results for monitored positions
            if hasattr(result, '__iter__'):
                for item in result:
                    if hasattr(item, 'get') and 'instrument_key' in item:
                        log_greek_calculation(
                            item['instrument_key'],
                            item.get('greeks', {}),
                            "API CALCULATION RESULT"
                        )
            
            return result
        return wrapper
    
    def monitor_dataframe_greeks(df, stage=""):
        """Log Greek values in a DataFrame"""
        if df is None or df.empty:
            return
            
        for _, row in df.iterrows():
            instrument_key = row.get('key', row.get('instrument_key', ''))
            
            for pos in MONITORED_POSITIONS:
                if pos in str(instrument_key):
                    greek_values = {}
                    for col in ['delta_y', 'gamma_y', 'theta_F', 'vega_y', 'delta_F', 'gamma_F']:
                        if col in row:
                            greek_values[col] = row[col]
                    
                    if greek_values:
                        log_greek_calculation(instrument_key, greek_values, stage)
                    break
else:
    # Dummy functions when not enabled
    def log_greek_calculation(*args, **kwargs):
        pass
    
    def monitor_greek_api_results(original_method):
        return original_method
    
    def monitor_dataframe_greeks(*args, **kwargs):
        pass
'''
    
    with open("lib/trading/actant/spot_risk/greek_monitor.py", "w") as f:
        f.write(calculator_patch)
    print("✓ Created greek_monitor.py")
    
    # 4. Create instructions file
    instructions = '''# Greek Value Logging Instructions

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
'''
    
    with open("greek_logging_instructions.md", "w") as f:
        f.write(instructions)
    print("✓ Created greek_logging_instructions.md")
    
    print("\n" + "=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print("\nTo start monitoring Greek values:")
    print("1. Run: run_pipeline_live.bat")
    print("2. Watch the Spot Risk Watcher console for GREEK_TRACE messages")
    print("3. Check logs/greek_trace/ for detailed log files")
    print("\nSee greek_logging_instructions.md for full details")

if __name__ == "__main__":
    setup_greek_logging()