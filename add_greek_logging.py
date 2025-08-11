"""
Script to add comprehensive Greek value logging to the spot risk pipeline
"""
import os
import shutil
from datetime import datetime

def add_greek_logging():
    """Add comprehensive logging to trace Greek values through the pipeline"""
    
    print("=== ADDING COMPREHENSIVE GREEK LOGGING ===\n")
    
    # 1. Backup original files
    files_to_modify = [
        "lib/trading/actant/spot_risk/calculator.py",
        "lib/trading/actant/spot_risk/file_watcher.py",
        "lib/trading/pnl_fifo_lifo/positions_aggregator.py"
    ]
    
    backup_dir = f"backups/greek_logging_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file in files_to_modify:
        if os.path.exists(file):
            backup_path = os.path.join(backup_dir, os.path.basename(file))
            shutil.copy2(file, backup_path)
            print(f"Backed up {file} to {backup_path}")
    
    # 2. Modify calculator.py to add Greek value logging
    calculator_path = "lib/trading/actant/spot_risk/calculator.py"
    with open(calculator_path, 'r') as f:
        content = f.read()
    
    # Add logging after Greek calculation
    log_addition = '''
                # COMPREHENSIVE GREEK LOGGING - START
                if result.success and result.instrument_key == 'TJWQ25C1 112.5 Comdty':
                    logger.info("=" * 80)
                    logger.info(f"GREEK VALUE TRACE - {result.instrument_key}")
                    logger.info("=" * 80)
                    logger.info(f"Strike: {result.strike}, Option Type: {result.option_type}")
                    logger.info(f"Future Price: {result.future_price}, Market Price: {result.market_price}")
                    logger.info(f"Time to Expiry: {result.time_to_expiry:.4f} years")
                    logger.info(f"Implied Volatility: {result.implied_volatility:.4f}")
                    logger.info("")
                    logger.info("RAW GREEK VALUES (from API):")
                    for greek in ['delta_F', 'delta_y', 'gamma_F', 'gamma_y', 'theta_F', 'vega_y']:
                        value = getattr(result, greek, None)
                        if value is not None:
                            logger.info(f"  {greek}: {value:.6f}")
                    logger.info("")
                    logger.info("SCALING CHECK:")
                    if hasattr(result, 'delta_y') and result.delta_y:
                        natural_delta = result.delta_y / 1000 if abs(result.delta_y) > 100 else result.delta_y
                        logger.info(f"  delta_y value: {result.delta_y:.6f}")
                        logger.info(f"  Appears to be scaled by: {result.delta_y / natural_delta:.0f}x" if natural_delta != 0 else "  Cannot determine scaling")
                    logger.info("=" * 80)
                # COMPREHENSIVE GREEK LOGGING - END
'''
    
    # Insert after line 348 (after results.append(result))
    lines = content.split('\n')
    insert_index = None
    for i, line in enumerate(lines):
        if 'results.append(result)' in line:
            insert_index = i + 1
            break
    
    if insert_index:
        lines.insert(insert_index, log_addition)
        content = '\n'.join(lines)
        
        with open(calculator_path, 'w') as f:
            f.write(content)
        print(f"\nAdded Greek value logging to {calculator_path}")
    
    # 3. Modify file_watcher.py to log DataFrame before publishing
    watcher_path = "lib/trading/actant/spot_risk/file_watcher.py"
    with open(watcher_path, 'r') as f:
        content = f.read()
    
    df_log = '''
                # COMPREHENSIVE GREEK LOGGING - DataFrame Check
                tjw_rows = full_df[full_df['key'].str.contains('TJWQ25C1 112.5', na=False)]
                if not tjw_rows.empty:
                    logger.info("=" * 80)
                    logger.info("DATAFRAME GREEK VALUES BEFORE REDIS PUBLISH")
                    logger.info("=" * 80)
                    for idx, row in tjw_rows.iterrows():
                        logger.info(f"Row for {row.get('key', 'Unknown')}:")
                        for col in ['delta_y', 'gamma_y', 'theta_F', 'vega_y']:
                            if col in row:
                                logger.info(f"  {col}: {row[col]}")
                    logger.info("=" * 80)
'''
    
    # Insert before Arrow conversion (line 228)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'arrow_table = pa.Table.from_pandas(full_df)' in line:
            lines.insert(i, df_log)
            break
    
    content = '\n'.join(lines)
    with open(watcher_path, 'w') as f:
        f.write(content)
    print(f"Added DataFrame logging to {watcher_path}")
    
    # 4. Modify positions_aggregator.py to log received Greeks
    aggregator_path = "lib/trading/pnl_fifo_lifo/positions_aggregator.py"
    if os.path.exists(aggregator_path):
        with open(aggregator_path, 'r') as f:
            content = f.read()
        
        # Add logging in the _process_greek_data method
        aggregator_log = '''
                    # COMPREHENSIVE GREEK LOGGING - Aggregator Received
                    if row.get('key', '').startswith('TJWQ25C1 112.5'):
                        logger.info("=" * 80)
                        logger.info(f"AGGREGATOR RECEIVED GREEK DATA - {row.get('key')}")
                        logger.info("=" * 80)
                        logger.info("Raw Greek values from Redis:")
                        for greek in ['delta_y', 'gamma_y', 'theta_F', 'vega_y']:
                            logger.info(f"  {greek}: {row.get(greek, 'NOT FOUND')}")
                        logger.info(f"Open Position: {self.positions_cache.loc[self.positions_cache['symbol'] == symbol, 'open_position'].values[0] if symbol in self.positions_cache['symbol'].values else 'NOT FOUND'}")
                        logger.info("=" * 80)
'''
        
        # Find where Greek data is processed
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'for _, row in df.iterrows():' in line and i > 100:  # Make sure we're in the right method
                lines.insert(i + 1, aggregator_log)
                break
        
        content = '\n'.join(lines)
        with open(aggregator_path, 'w') as f:
            f.write(content)
        print(f"Added aggregator logging to {aggregator_path}")
    
    print("\n=== LOGGING ADDED SUCCESSFULLY ===")
    print("\nTo see the logs:")
    print("1. Run the pipeline: run_pipeline_live.bat")
    print("2. Watch for lines starting with '===='")
    print("3. Focus on TJWQ25C1 112.5 Comdty position")
    print("\nLogs will show:")
    print("- Raw Greek values from calculation")
    print("- Values in DataFrame before Redis")
    print("- Values received by aggregator")
    print("- Position weighting applied")
    
    print(f"\nBackups saved to: {backup_dir}")
    print("To restore: copy files from backup directory back to original locations")

if __name__ == "__main__":
    add_greek_logging()