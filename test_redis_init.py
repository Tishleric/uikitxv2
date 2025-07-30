"""Test Redis initialization issue."""
import redis
import time

print("Testing Redis() initialization times...")

# Test 1: Default initialization
start = time.time()
r1 = redis.Redis()
init_time1 = (time.time() - start) * 1000
print(f"redis.Redis() initialization: {init_time1:.2f} ms")

# Test 2: First operation after init
start = time.time()
r1.ping()
ping_time1 = (time.time() - start) * 1000
print(f"First ping after init: {ping_time1:.2f} ms")

# Test 3: Second operation
start = time.time()
r1.ping()
ping_time2 = (time.time() - start) * 1000
print(f"Second ping: {ping_time2:.2f} ms")

# Test 4: Explicit parameters
start = time.time()
r2 = redis.Redis(host='127.0.0.1', port=6379, db=0)
init_time2 = (time.time() - start) * 1000
print(f"\nredis.Redis(host='127.0.0.1', ...) initialization: {init_time2:.2f} ms")

start = time.time()
r2.ping()
ping_time3 = (time.time() - start) * 1000
print(f"First ping: {ping_time3:.2f} ms")

# Test 5: DNS resolution
import socket
start = time.time()
socket.gethostbyname('localhost')
dns_time = (time.time() - start) * 1000
print(f"\nDNS resolution for 'localhost': {dns_time:.2f} ms")

# Test 6: Connection with 'localhost'
start = time.time()
r3 = redis.Redis(host='localhost', port=6379)
r3.ping()
localhost_time = (time.time() - start) * 1000
print(f"Redis with 'localhost': {localhost_time:.2f} ms")