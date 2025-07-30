"""Test if multiprocessing Queue is causing delays."""
import multiprocessing
import time
import queue
import pandas as pd

def test_queue_performance():
    # Create a multiprocessing Queue
    mp_queue = multiprocessing.Queue()
    
    # Create test DataFrames similar to what workers produce
    test_dfs = []
    for i in range(16):  # 16 chunks like your batches
        df = pd.DataFrame({
            'key': [f'TEST{j}' for j in range(50)],
            'value': range(50),
            'delta': [0.5] * 50,
            'gamma': [0.1] * 50,
            'theta': [-0.05] * 50
        })
        test_dfs.append(df)
    
    print("Testing multiprocessing Queue get() timing:")
    
    # Put items in queue
    for i, df in enumerate(test_dfs):
        mp_queue.put(('batch_001', f'file_{i}.csv', df))
    
    # Test getting items with timeout
    times = []
    for i in range(16):
        try:
            start = time.time()
            result = mp_queue.get(timeout=20.0)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            print(f"  Get {i+1}: {elapsed:.2f} ms")
        except queue.Empty:
            print(f"  Get {i+1}: Queue empty")
            break
    
    print(f"\nAverage get time: {sum(times)/len(times) if times else 0:.2f} ms")
    
    # Test the timeout behavior
    print("\nTesting empty queue with timeout:")
    start = time.time()
    try:
        result = mp_queue.get(timeout=2.0)
    except queue.Empty:
        elapsed = (time.time() - start)
        print(f"  Timeout after {elapsed:.2f} seconds")

if __name__ == "__main__":
    test_queue_performance()