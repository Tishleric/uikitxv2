"""
Quick Redis Activity Check
=========================
Checks if publishers and subscribers are active on the pipeline.
"""

import redis
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def check_redis_channels():
    """Check Redis pub/sub activity"""
    r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
    
    logger.info("Checking Redis pub/sub channels...")
    
    # Check all active channels
    channels_info = r.execute_command('PUBSUB', 'CHANNELS')
    if channels_info:
        logger.info(f"Active channels: {channels_info}")
    else:
        logger.info("No active channels")
    
    # Check specific channel
    channel = "spot_risk:results_channel"
    subs_info = r.execute_command('PUBSUB', 'NUMSUB', channel)
    if subs_info and len(subs_info) >= 2:
        logger.info(f"Channel '{subs_info[0]}' has {subs_info[1]} subscribers")
    
    # Check for other related channels
    for pattern in ["spot_risk:*", "positions:*", "price:*"]:
        channels = r.execute_command('PUBSUB', 'CHANNELS', pattern)
        if channels:
            logger.info(f"Channels matching '{pattern}': {channels}")
    
    # Try to check client list
    try:
        clients = r.execute_command('CLIENT', 'LIST')
        lines = clients.strip().split('\n')
        pubsub_clients = [line for line in lines if 'sub=' in line and 'sub=0' not in line]
        logger.info(f"Total Redis clients: {len(lines)}")
        logger.info(f"Pub/Sub clients: {len(pubsub_clients)}")
    except Exception as e:
        logger.error(f"Could not get client list: {e}")
    
    # Monitor for any pub/sub activity
    logger.info("\nMonitoring for any Redis activity for 10 seconds...")
    pubsub = r.pubsub()
    pubsub.psubscribe('*')  # Subscribe to all channels
    
    start_time = time.time()
    message_count = 0
    
    while time.time() - start_time < 10:
        message = pubsub.get_message(timeout=0.1)
        if message and message['type'] in ['message', 'pmessage']:
            message_count += 1
            logger.info(f"Message on channel '{message.get('channel', 'unknown')}': "
                       f"{str(message.get('data', ''))[:100]}...")
    
    logger.info(f"Total messages observed: {message_count}")
    
    # Check if price updater service might be stuck
    logger.info("\nChecking for signs of stuck price updater...")
    
    # Test publish
    test_channel = "test_diagnostic_channel"
    pubsub2 = r.pubsub()
    pubsub2.subscribe(test_channel)
    
    # Let subscription establish
    time.sleep(0.1)
    
    # Publish test message
    r.publish(test_channel, "test")
    
    # Check if we receive it
    test_msg = pubsub2.get_message(timeout=1.0)
    if test_msg and test_msg['type'] == 'message':
        logger.info("Redis pub/sub is working correctly")
    else:
        logger.error("Redis pub/sub might have issues!")
    
    pubsub2.unsubscribe()
    pubsub.punsubscribe()

if __name__ == "__main__":
    check_redis_channels()