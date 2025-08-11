"""
Analyze Captured Messages
========================
Analyze the captured Redis messages to understand their content and size.
"""

import pickle
import pyarrow as pa
from pathlib import Path
import json
import pandas as pd

def analyze_message(filepath):
    """Analyze a single captured message"""
    print(f"\nAnalyzing: {filepath}")
    print("="*60)
    
    # Load the message
    with open(filepath, 'rb') as f:
        message_data = pickle.load(f)
    
    # Unpack the payload
    payload = pickle.loads(message_data)
    
    print(f"Batch ID: {payload.get('batch_id')}")
    print(f"Format: {payload.get('format')}")
    print(f"Publish timestamp: {payload.get('publish_timestamp')}")
    
    # Deserialize Arrow data
    buffer = payload['data']
    reader = pa.ipc.open_stream(buffer)
    arrow_table = reader.read_all()
    df = arrow_table.to_pandas()
    
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Number of instruments: {len(df)}")
    
    # Analyze instrument types
    if 'itype' in df.columns:
        print(f"\nInstrument types:")
        print(df['itype'].value_counts())
    
    # Count Bloomberg symbols
    if 'bloomberg_symbol' in df.columns:
        print(f"\nSample Bloomberg symbols:")
        for symbol in df['bloomberg_symbol'].head(10):
            print(f"  {symbol}")
        
        # Count by type
        futures = df[df['bloomberg_symbol'].str.contains('Comdty') & ~df['bloomberg_symbol'].str.contains(' ')]['bloomberg_symbol'].unique()
        options = df[df['bloomberg_symbol'].str.contains(' Comdty')]['bloomberg_symbol'].unique()
        
        print(f"\nUnique futures: {len(futures)}")
        print(f"Unique options: {len(options)}")
    
    # Check for prices
    price_cols = ['bid', 'ask', 'adjtheor', 'midpoint_price']
    for col in price_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            print(f"\n{col}: {non_null}/{len(df)} have values")
    
    # Check Greeks
    greek_cols = ['delta_F', 'gamma_F', 'theta_F', 'vega_price']
    print(f"\nGreek calculations:")
    for col in greek_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            print(f"  {col}: {non_null}/{len(df)} calculated")
    
    # Message size
    print(f"\nMessage size: {len(message_data):,} bytes ({len(message_data)/1024:.1f} KB)")
    
    return df

def main():
    """Analyze all captured messages"""
    # Try multiple possible locations
    possible_dirs = [
        Path("tests/diagnostics/tests/diagnostics/captured_messages"),  # Nested path
        Path("tests/diagnostics/captured_messages"),  # Expected path
        Path("captured_messages"),  # Current directory
    ]
    
    msg_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            msg_dir = dir_path
            print(f"Found captured messages in: {msg_dir}")
            break
    
    if not msg_dir:
        print("No captured messages directory found!")
        print("Searched in:")
        for dir_path in possible_dirs:
            print(f"  - {dir_path}")
        return
    
    # Find all message files
    msg_files = sorted(msg_dir.glob("message_*.pkl"))
    
    if not msg_files:
        print("No captured messages found!")
        return
    
    print(f"Found {len(msg_files)} captured messages")
    
    all_dfs = []
    for msg_file in msg_files:
        df = analyze_message(msg_file)
        all_dfs.append(df)
    
    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY ACROSS ALL MESSAGES")
    print("="*60)
    
    total_instruments = sum(len(df) for df in all_dfs)
    print(f"Total instruments processed: {total_instruments}")
    print(f"Average instruments per message: {total_instruments/len(all_dfs):.1f}")
    
    # Extract unique symbols that would need price updates
    all_symbols = set()
    for df in all_dfs:
        if 'bloomberg_symbol' in df.columns:
            all_symbols.update(df['bloomberg_symbol'].unique())
    
    print(f"Unique Bloomberg symbols: {len(all_symbols)}")
    
    # Estimate database update time
    if len(all_symbols) > 0:
        print(f"\nIf each symbol update takes:")
        for ms in [50, 100, 200, 500]:
            total_time = len(all_symbols) * ms / 1000
            print(f"  {ms}ms -> {total_time:.1f} seconds total")

if __name__ == "__main__":
    main()