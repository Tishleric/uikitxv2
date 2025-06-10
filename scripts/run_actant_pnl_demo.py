"""
Demo runner for PnL Dashboard with sample data.
"""

import sys
from pathlib import Path
import time

# Fix path for our lib components
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

def run_demo():
    """Run the dashboard demo with sample data."""
    print("Starting PnL Dashboard Demo...")
    print("=" * 40)
    
    try:
        from pnl_dashboard import create_app
        
        # Create the app
        app = create_app(".")
        
        print("✓ Dashboard created successfully")
        print()
        print("Features implemented:")
        print("  • Toggle buttons for Graph/Table view")
        print("  • Toggle buttons for Call/Put options")
        print("  • Responsive grid layout with Bootstrap")
        print("  • Dark theme consistent with UIKitXv2")
        print("  • Loading indicators")
        print("  • Summary statistics panel")
        print("  • Sample data visualization")
        print()
        print("Starting server on http://localhost:8050")
        print("Press Ctrl+C to stop")
        print()
        
        # Run the server
        app.run(debug=True, port=8050, dev_tools_hot_reload=False)
        
    except Exception as e:
        print(f"✗ Error starting demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_demo() 