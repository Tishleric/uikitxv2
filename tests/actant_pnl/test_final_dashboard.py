#!/usr/bin/env python3
"""
Final comprehensive test of the dashboard functionality.
"""

import time
import threading
from pathlib import Path
from pnl_dashboard import create_app

def test_dashboard_comprehensive():
    """Comprehensive test of dashboard functionality."""
    print("🔍 Final Dashboard Comprehensive Test")
    print("=" * 50)
    
    # 1. Verify data files exist
    print("1. Verifying data files...")
    csv_files = list(Path(".").glob("GE_*.csv"))
    if not csv_files:
        print("❌ No CSV files found in current directory!")
        return False
    print(f"✅ Found CSV file: {csv_files[0]}")
    
    # 2. Test app creation
    print("\n2. Creating Dash application...")
    try:
        app = create_app(".")
        print("✅ Dash app created successfully")
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Test server startup
    print("\n3. Testing server startup...")
    server_started = False
    server_error = None
    
    def run_server():
        nonlocal server_started, server_error
        try:
            # Start the server
            print("   Starting server on http://localhost:8051...")
            app.run(debug=False, host='127.0.0.1', port=8051, use_reloader=False)
        except Exception as e:
            server_error = e
            print(f"   Server error: {e}")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for startup
    time.sleep(3)
    
    if server_error:
        print(f"❌ Server startup failed: {server_error}")
        return False
    
    print("✅ Server started successfully")
    
    # 4. Verify app functionality
    print("\n4. Verifying app components...")
    
    # Test that we can access the dashboard instance
    try:
        from pnl_dashboard import PnLDashboard
        dashboard = PnLDashboard(".")
        
        print(f"   ✅ Data directory: {dashboard.data_dir}")
        print(f"   ✅ Available expirations: {dashboard.available_expirations}")
        print(f"   ✅ Loaded greeks for: {list(dashboard.all_greeks.keys())}")
        
        if not dashboard.available_expirations:
            print("   ❌ No expirations available!")
            return False
            
        # Test controls creation
        controls = dashboard.create_controls()
        print("   ✅ Controls component created")
        
        # Test layout creation
        layout = dashboard.create_layout()
        print("   ✅ Layout created")
        
    except Exception as e:
        print(f"   ❌ Component verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Test data access
    print("\n5. Testing data access...")
    try:
        # Get first expiration
        first_exp = dashboard.available_expirations[0]
        greeks = dashboard.all_greeks[first_exp]
        
        print(f"   ✅ Expiration: {first_exp}")
        print(f"   ✅ Underlying price: ${greeks.underlying_price:.3f}")
        print(f"   ✅ Shock points: {len(greeks.shocks)}")
        print(f"   ✅ ATM call price: ${greeks.call_prices[greeks.atm_index]:.2f}")
        
    except Exception as e:
        print(f"   ❌ Data access failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("\nTo test the dashboard manually:")
    print("1. Open http://localhost:8051 in your browser")
    print("2. Check that the Expiration dropdown shows: ['XCME.ZN', '13JUN25']")
    print("3. Select an expiration and verify the graph/table displays")
    print("4. Toggle between Call/Put and Graph/Table views")
    print("\nPress Ctrl+C to stop the server when done testing.")
    
    # Keep server running for manual testing
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Test complete!")
    
    return True

if __name__ == "__main__":
    success = test_dashboard_comprehensive()
    if not success:
        print("\n❌ Dashboard test failed!")
        exit(1) 