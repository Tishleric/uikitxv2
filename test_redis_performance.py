"""Test Redis publish performance to diagnose the 2-second delay."""
import redis
import time
import pickle
import json

def test_redis_performance():
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    
    # Test 1: Basic ping
    start = time.time()
    r.ping()
    ping_time = (time.time() - start) * 1000
    print(f"Redis PING: {ping_time:.2f} ms")
    
    # Test 2: Small publish (1KB)
    small_data = "x" * 1024
    start = time.time()
    r.publish("test_channel", small_data)
    small_publish_time = (time.time() - start) * 1000
    print(f"Small publish (1KB): {small_publish_time:.2f} ms")
    
    # Test 3: Medium publish (1MB)
    medium_data = "x" * (1024 * 1024)
    start = time.time()
    r.publish("test_channel", medium_data)
    medium_publish_time = (time.time() - start) * 1000
    print(f"Medium publish (1MB): {medium_publish_time:.2f} ms")
    
    # Test 4: Large publish (10MB)
    large_data = "x" * (10 * 1024 * 1024)
    start = time.time()
    r.publish("test_channel", large_data)
    large_publish_time = (time.time() - start) * 1000
    print(f"Large publish (10MB): {large_publish_time:.2f} ms")
    
    # Test 5: Pickled data (similar to actual usage)
    test_payload = {
        'batch_id': 'test_batch',
        'publish_timestamp': time.time(),
        'format': 'arrow',
        'data': b"x" * (5 * 1024 * 1024)  # 5MB binary data
    }
    pickled = pickle.dumps(test_payload)
    print(f"\nPickled payload size: {len(pickled) / (1024*1024):.2f} MB")
    
    start = time.time()
    r.publish("test_channel", pickled)
    pickle_publish_time = (time.time() - start) * 1000
    print(f"Pickled publish: {pickle_publish_time:.2f} ms")
    
    # Test 6: Multiple rapid publishes
    print("\nTesting 10 rapid publishes:")
    times = []
    for i in range(10):
        start = time.time()
        r.publish("test_channel", f"Message {i}")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f"  Publish {i+1}: {elapsed:.2f} ms")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage publish time: {avg_time:.2f} ms")
    print(f"Max publish time: {max(times):.2f} ms")
    print(f"Min publish time: {min(times):.2f} ms")

if __name__ == "__main__":
    test_redis_performance()