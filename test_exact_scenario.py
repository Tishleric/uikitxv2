"""Simulate the exact ResultPublisher scenario to find the delay."""
import redis
import time
import pickle
import pandas as pd
import pyarrow as pa
import numpy as np

def simulate_result_publisher():
    # Create 16 DataFrames similar to actual Greek calculation results
    print("Creating test DataFrames...")
    results = []
    for i in range(16):
        # Simulate ~500 rows per chunk (based on your logs showing ~8000 total rows)
        df = pd.DataFrame({
            'key': [f'OPTION{j:04d}' for j in range(500)],
            'bloomberg_symbol': [f'BB{j:04d}' for j in range(500)],
            'bid': np.random.rand(500),
            'ask': np.random.rand(500),
            'strike': np.random.rand(500) * 100,
            'itype': ['C' if j % 2 == 0 else 'P' for j in range(500)],
            'delta_y': np.random.rand(500),
            'gamma_y': np.random.rand(500),
            'theta_F': np.random.rand(500),
            'vega_y': np.random.rand(500),
            'speed_y': np.random.rand(500),
            'instrument_type': ['option'] * 500,
            'expiry': ['2025-12-31'] * 500,
            'underlying': ['TY'] * 500,
            'time_to_expiry': np.random.rand(500),
            'timestamp': ['2025-07-29 22:00:00'] * 500
        })
        results.append(df)
    
    # Test the exact publishing sequence
    print("\nTesting exact ResultPublisher sequence:")
    
    # 1. Concatenate DataFrames
    t0 = time.time()
    full_df = pd.concat(results, ignore_index=True)
    t1 = time.time()
    print(f"pd.concat: {(t1-t0)*1000:.2f} ms")
    print(f"Combined DataFrame shape: {full_df.shape}")
    
    # 2. Convert to Arrow
    arrow_table = pa.Table.from_pandas(full_df)
    t2 = time.time()
    print(f"pa.Table.from_pandas: {(t2-t1)*1000:.2f} ms")
    
    # 3. Serialize Arrow
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, arrow_table.schema) as writer:
        writer.write_table(arrow_table)
    buffer = sink.getvalue()
    t3 = time.time()
    print(f"pa.write_table: {(t3-t2)*1000:.2f} ms")
    print(f"Arrow buffer size: {len(buffer) / (1024*1024):.2f} MB")
    
    # 4. Create payload
    payload = {
        'batch_id': 'test_batch_001',
        'publish_timestamp': time.time(),
        'format': 'arrow',
        'data': buffer
    }
    
    # 5. Pickle the payload
    pickled = pickle.dumps(payload)
    t4 = time.time()
    print(f"pickle.dumps: {(t4-t3)*1000:.2f} ms")
    print(f"Pickled size: {len(pickled) / (1024*1024):.2f} MB")
    
    # 6. Publish to Redis
    r = redis.Redis()
    result = r.publish("spot_risk:results_channel", pickled)
    t5 = time.time()
    print(f"redis.publish: {(t5-t4)*1000:.2f} ms")
    print(f"Subscribers notified: {result}")
    
    print(f"\nTotal time: {(t5-t0)*1000:.2f} ms")
    
    # Test with explicit connection parameters
    print("\n\nTesting with different Redis configurations:")
    
    # Test 1: Explicit localhost
    r2 = redis.Redis(host='localhost', port=6379)
    start = time.time()
    r2.publish("test_channel", pickled)
    print(f"Explicit localhost: {(time.time()-start)*1000:.2f} ms")
    
    # Test 2: IP address
    r3 = redis.Redis(host='127.0.0.1', port=6379)
    start = time.time()
    r3.publish("test_channel", pickled)
    print(f"IP address (127.0.0.1): {(time.time()-start)*1000:.2f} ms")
    
    # Test 3: Default (what we use)
    r4 = redis.Redis()
    start = time.time()
    r4.publish("test_channel", pickled)
    print(f"Default config: {(time.time()-start)*1000:.2f} ms")

if __name__ == "__main__":
    simulate_result_publisher()