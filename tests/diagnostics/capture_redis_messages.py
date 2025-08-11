"""
Capture Redis Messages for Profiling
===================================
Captures real messages from spot_risk:results_channel for offline testing.
"""

import redis
import pickle
import time
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_messages(num_messages=5, output_dir="tests/diagnostics/captured_messages"):
    """Capture real messages from Redis channel"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Connect to Redis
    r = redis.Redis(host='127.0.0.1', port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe('spot_risk:results_channel')
    
    logger.info(f"Listening for {num_messages} messages on spot_risk:results_channel...")
    logger.info("Make sure spot risk watcher is running!")
    
    captured = 0
    
    for message in pubsub.listen():
        if message['type'] != 'message':
            continue
            
        # Save the raw message data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_path / f'message_{timestamp}_{captured}.pkl'
        
        with open(filename, 'wb') as f:
            pickle.dump(message['data'], f)
        
        # Also save metadata
        meta_filename = output_path / f'message_{timestamp}_{captured}_meta.txt'
        with open(meta_filename, 'w') as f:
            f.write(f"Captured at: {datetime.now()}\n")
            f.write(f"Message size: {len(message['data'])} bytes\n")
            f.write(f"Channel: {message['channel']}\n")
        
        captured += 1
        logger.info(f"Captured message {captured}/{num_messages}: {filename}")
        
        if captured >= num_messages:
            break
    
    pubsub.unsubscribe()
    logger.info(f"Captured {captured} messages to {output_path}")
    
if __name__ == "__main__":
    import sys
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    capture_messages(num)