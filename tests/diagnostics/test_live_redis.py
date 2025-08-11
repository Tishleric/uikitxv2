"""
Live Redis Validation Test
==========================
Read-only test against live Redis feed.
"""

import sys
import time
import redis
import pickle
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.diagnostics.price_updater_service_optimized import PriceUpdaterServiceOptimized


def test_live_redis(timeout=10):
    """
    Connect to Redis and process one real message (read-only).
    """
    print("="*50)
    print("LIVE REDIS VALIDATION TEST")
    print("="*50)
    print(f"\nWaiting up to {timeout}s for a message...")
    
    # Connect to Redis
    redis_client = redis.Redis(host='127.0.0.1', port=6379)
    pubsub = redis_client.pubsub()
    pubsub.subscribe('spot_risk:results_channel')
    
    # Initialize optimized service (but don't let it write to DB)
    service = PriceUpdaterServiceOptimized()
    
    # Track updates by overriding batch update
    update_count = 0
    prices_seen = []
    
    def mock_batch_update(prices_to_update, timestamp):
        nonlocal update_count, prices_seen
        update_count += len(prices_to_update)
        for symbol, price in prices_to_update.items():
            prices_seen.append((symbol, price))
            if len(prices_seen) <= 5:  # Show first 5
                print(f"  Would update: {symbol} = {price:.6f}")
        if len(prices_to_update) > 5:
            print(f"  ... and {len(prices_to_update) - 5} more")
        return True  # Simulate success
    
    service._batch_update_prices = mock_batch_update
    
    # Wait for one message
    start_time = time.time()
    message_found = False
    
    for message in pubsub.listen():
        if time.time() - start_time > timeout:
            break
            
        if message['type'] == 'message':
            print(f"\nReceived message on channel: {message['channel'].decode()}")
            
            try:
                # Process with optimized service
                payload = pickle.loads(message['data'])
                
                # Extract some metadata
                batch_id = payload.get('batch_id', 'unknown')
                timestamp = payload.get('publish_timestamp', 0)
                print(f"  Batch ID: {batch_id}")
                print(f"  Timestamp: {time.ctime(timestamp)}")
                
                # Process the message
                service._process_single_message(message['data'])
                
                print(f"\n  ✓ Successfully processed")
                print(f"  ✓ Would have updated {update_count} prices")
                message_found = True
                break
                
            except Exception as e:
                print(f"  ✗ Error processing: {e}")
                return 1
    
    # Cleanup
    pubsub.unsubscribe()
    pubsub.close()
    
    if not message_found:
        print("\n⚠ No messages received (is spot risk watcher running?)")
        print("  This is OK on dev machines.")
        return 0
    
    print("\n" + "="*50)
    print("LIVE VALIDATION SUCCESSFUL ✓")
    print("="*50)
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=10,
                        help='Seconds to wait for message (default: 10)')
    args = parser.parse_args()
    
    sys.exit(test_live_redis(args.timeout))