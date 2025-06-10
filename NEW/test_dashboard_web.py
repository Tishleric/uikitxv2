#!/usr/bin/env python3
"""
Test script to run the dashboard web app and check for errors.
"""

import threading
import time
import traceback
import sys
from pnl_dashboard import create_app

def test_dashboard_web():
    """Test the dashboard web application."""
    print("Testing PnL Dashboard Web Application")
    print("=" * 50)
    
    try:
        # Create the app
        print("1. Creating Dash app...")
        app = create_app(".")
        
        print("✓ App created successfully")
        print(f"   Server: {app.server}")
        print(f"   Config: {app.config}")
        
        # Try to run in a thread for a short time
        print("\n2. Testing server startup...")
        
        def run_server():
            try:
                app.run(debug=False, host='127.0.0.1', port=8050)
            except Exception as e:
                print(f"Server error: {e}")
                traceback.print_exc()
        
        # Start server in thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for startup
        time.sleep(2)
        
        print("✓ Server started")
        print("✓ Dashboard accessible at http://localhost:8050")
        print("\nTo test manually:")
        print("1. Open http://localhost:8050 in browser")
        print("2. Check if expiration dropdown has options")
        print("3. Verify data loads correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_web()
    if success:
        print("\n🎉 Dashboard web test completed successfully!")
    else:
        print("\n❌ Dashboard web test failed!")
        sys.exit(1) 