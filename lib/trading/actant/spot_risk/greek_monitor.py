"""
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
