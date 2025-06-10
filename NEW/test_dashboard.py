"""
Test script for PnL Dashboard frontend.
"""

import sys
from pathlib import Path

# Add the lib directory to the path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        # Test dash imports
        import dash
        from dash import html, dcc, Input, Output, State
        print("✓ Dash imports successful")
        
        # Test plotly imports
        import plotly.graph_objects as go
        print("✓ Plotly imports successful")
        
        # Test our components
        from components import Container, Grid, Button, DataTable, Graph, Loading
        from components.themes import default_theme
        print("✓ UIKitXv2 component imports successful")
        
        # Test data modules
        from csv_parser import load_latest_data
        from pnl_calculations import PnLCalculator
        from data_formatter import PnLDataFormatter
        print("✓ Data module imports successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_dashboard_creation():
    """Test dashboard creation without running the server."""
    print("\nTesting dashboard creation...")
    
    try:
        from pnl_dashboard import PnLDashboard, create_app
        
        # Create dashboard instance
        dashboard = PnLDashboard(".")
        print("✓ Dashboard instance created")
        
        # Test component creation methods
        header = dashboard.create_header()
        print("✓ Header component created")
        
        controls = dashboard.create_controls()
        print("✓ Controls component created")
        
        content = dashboard.create_content_area()
        print("✓ Content area created")
        
        summary = dashboard.create_summary_panel()
        print("✓ Summary panel created")
        
        layout = dashboard.create_layout()
        print("✓ Complete layout created")
        
        # Test app creation
        app = create_app(".")
        print("✓ Dash app created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_rendering():
    """Test that wrapped components render properly."""
    print("\nTesting component rendering...")
    
    try:
        from components import Button, Container, Grid, DataTable, Graph
        from components.themes import default_theme
        
        # Test Button
        btn = Button(id="test-btn", label="Test Button", theme=default_theme)
        rendered_btn = btn.render()
        print("✓ Button renders successfully")
        
        # Test Container
        container = Container(id="test-container", children=[rendered_btn], theme=default_theme)
        rendered_container = container.render()
        print("✓ Container renders successfully")
        
        # Test Grid
        grid = Grid(id="test-grid", children=[btn], theme=default_theme)
        rendered_grid = grid.render()
        print("✓ Grid renders successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Component rendering error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all frontend tests."""
    print("PnL Dashboard Frontend Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_dashboard_creation,
        test_component_rendering
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✓ All tests passed! Frontend is ready.")
        return True
    else:
        print("✗ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\nTo run the dashboard:")
        print("python pnl_dashboard.py")
        print("Then open http://localhost:8050 in your browser")
    
    sys.exit(0 if success else 1) 