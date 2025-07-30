"""Test if decode_responses parameter affects Redis publish performance."""
import redis
import time
import pickle

def test_decode_responses_impact():
    # Test with decode_responses=False (default)
    r1 = redis.Redis()
    
    # Test with decode_responses=True (old setting)
    r2 = redis.Redis(decode_responses=True)
    
    test_payload = {
        'batch_id': 'test_batch',
        'publish_timestamp': time.time(),
        'format': 'arrow',
        'data': b"x" * (5 * 1024 * 1024)  # 5MB binary data
    }
    pickled = pickle.dumps(test_payload)
    
    print(f"Payload size: {len(pickled) / (1024*1024):.2f} MB")
    print("\nTesting with decode_responses=False (current):")
    
    # Test 1: Regular publish
    start = time.time()
    r1.publish("test_channel", pickled)
    time1 = (time.time() - start) * 1000
    print(f"  Publish time: {time1:.2f} ms")
    
    # Test 2: Explicitly set socket timeout
    r3 = redis.Redis(socket_connect_timeout=5, socket_timeout=5)
    start = time.time()
    r3.publish("test_channel", pickled)
    time3 = (time.time() - start) * 1000
    print(f"\nWith explicit socket timeouts:")
    print(f"  Publish time: {time3:.2f} ms")
    
    # Test 3: Connection pool
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    r4 = redis.Redis(connection_pool=pool)
    start = time.time()
    r4.publish("test_channel", pickled)
    time4 = (time.time() - start) * 1000
    print(f"\nWith connection pool:")
    print(f"  Publish time: {time4:.2f} ms")

if __name__ == "__main__":
    test_decode_responses_impact()