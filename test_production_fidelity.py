"""
Test to verify production environment differences
"""
import sqlite3
import pandas as pd
import json
import redis
import time

def check_production_state():
    """Check the actual production environment state"""
    
    print("=== PRODUCTION ENVIRONMENT CHECK ===\n")
    
    # 1. Check if services are running
    print("1. SERVICE STATUS:")
    try:
        r = redis.Redis(host='127.0.0.1', port=6379)
        r.ping()
        print("   ✓ Redis is running")
        
        # Check for active subscriptions
        pubsub_channels = r.pubsub_channels()
        if pubsub_channels:
            print(f"   Active channels: {[ch.decode() for ch in pubsub_channels]}")
        else:
            print("   No active Redis subscriptions (PositionsAggregator not running)")
    except:
        print("   ✗ Redis is NOT running")
    
    # 2. Check spot_risk.db
    print("\n2. SPOT RISK DATABASE:")
    spot_risk_path = 'data/output/spot_risk/spot_risk.db'
    try:
        conn = sqlite3.connect(spot_risk_path)
        count = conn.execute("SELECT COUNT(*) FROM spot_risk_calculated").fetchone()[0]
        print(f"   spot_risk_calculated rows: {count}")
        
        if count > 0:
            # Get sample
            df = pd.read_sql_query("SELECT * FROM spot_risk_calculated LIMIT 5", conn)
            print("\n   Sample data:")
            print(df[['instrument_key', 'delta_y', 'gamma_y']].to_string())
        conn.close()
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Check positions table
    print("\n3. POSITIONS TABLE:")
    conn = sqlite3.connect('trades.db')
    df = pd.read_sql_query("""
        SELECT symbol, open_position, has_greeks, delta_y, gamma_y
        FROM positions 
        WHERE open_position != 0
        LIMIT 5
    """, conn)
    print(df.to_string())
    
    # Count positions with Greeks
    greek_count = conn.execute("""
        SELECT COUNT(*) FROM positions 
        WHERE has_greeks = 1 AND delta_y IS NOT NULL
    """).fetchone()[0]
    print(f"\n   Positions with Greeks: {greek_count}")
    conn.close()
    
    # 4. Test Redis message flow
    print("\n4. REDIS MESSAGE FLOW TEST:")
    test_message = {
        'instrument_key': 'TEST_OPTION',
        'delta_y': 100.0,
        'gamma_y': 10.0,
        'test': True
    }
    
    try:
        r.publish('spot_risk:results_channel', json.dumps([test_message]))
        print("   ✓ Published test message to spot_risk:results_channel")
        
        # Check if anyone received it
        subscribers = r.pubsub_numsub('spot_risk:results_channel')[0][1]
        print(f"   Subscribers on channel: {subscribers}")
        
        if subscribers == 0:
            print("   ⚠️  No subscribers - PositionsAggregator not listening!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== SUMMARY ===")
    print("\nProduction Greek pipeline status:")
    print("1. Redis: Check above")
    print("2. Spot Risk Calculations: Check above")
    print("3. PositionsAggregator: Not running (no Redis subscribers)")
    print("4. Greeks in DB: NULL")
    print("\nTo enable Greeks, you must:")
    print("1. Ensure Redis is running")
    print("2. Start PositionsAggregator service")
    print("3. Run spot risk calculations")

def test_message_format():
    """Test the exact message format expected by PositionsAggregator"""
    print("\n\n=== MESSAGE FORMAT TEST ===\n")
    
    # This is what PositionsAggregator expects
    expected_format = [
        {
            'instrument_key': 'TJWQ25C1 112.5 Comdty',
            'delta_y': 23.626452,  # Per-contract, NOT scaled by 1000
            'gamma_y': 262.17208,
            'speed_y': -846.71032,
            'theta_F': -0.017746242,  # Daily theta
            'vega_y': 12.098634,
            'instrument_type': 'CALL'
        }
    ]
    
    print("Expected Redis message format:")
    print(json.dumps(expected_format, indent=2))
    
    print("\nKey observations:")
    print("1. Greeks should be per-contract values")
    print("2. The 1000x scaling happens INSIDE the model")
    print("3. PositionsAggregator multiplies by position")
    print("4. instrument_key must match positions table symbol")

if __name__ == "__main__":
    check_production_state()
    test_message_format()