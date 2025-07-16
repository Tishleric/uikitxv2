#!/usr/bin/env python3
"""Test script for P&L Dashboard V2 UI framework."""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pnl_v2_ui():
    """Test the P&L V2 UI components."""
    
    try:
        # Test 1: Import the layout
        logger.info("Test 1: Importing P&L V2 layout...")
        from apps.dashboards.pnl_v2 import create_pnl_v2_layout
        logger.info("✓ Layout import successful")
        
        # Test 2: Create the layout
        logger.info("\nTest 2: Creating P&L V2 layout...")
        layout = create_pnl_v2_layout()
        logger.info("✓ Layout created successfully")
        
        # Test 3: Check layout structure
        logger.info("\nTest 3: Checking layout structure...")
        if hasattr(layout, 'children'):
            logger.info(f"✓ Layout has {len(layout.children)} children")
        else:
            logger.error("✗ Layout missing children attribute")
            
        # Test 4: Import callbacks
        logger.info("\nTest 4: Importing callbacks...")
        from apps.dashboards.pnl_v2.callbacks import register_pnl_v2_callbacks
        logger.info("✓ Callbacks import successful")
        
        # Test 5: Import controller
        logger.info("\nTest 5: Testing controller...")
        from apps.dashboards.pnl_v2.controller import PnLDashboardController
        
        # Create controller instance (singleton)
        controller = PnLDashboardController()
        logger.info("✓ Controller initialized")
        
        # Test 6: Test controller methods
        logger.info("\nTest 6: Testing controller methods...")
        
        # Get summary metrics
        metrics = controller.get_summary_metrics()
        logger.info(f"✓ Summary metrics: {metrics}")
        
        # Get positions data
        positions = controller.get_positions_data()
        logger.info(f"✓ Positions data: {positions['count']} positions")
        
        # Get trades data
        trades = controller.get_trades_data(limit=5)
        logger.info(f"✓ Trades data: {len(trades)} trades")
        
        # Get daily P&L data
        daily_pnl = controller.get_daily_pnl_data()
        logger.info(f"✓ Daily P&L data: {len(daily_pnl)} days")
        
        # Get chart data
        chart_data = controller.get_chart_data()
        logger.info(f"✓ Chart data: {len(chart_data['dates'])} data points")
        
        # Test 7: Stop controller
        logger.info("\nTest 7: Stopping controller...")
        controller.stop()
        logger.info("✓ Controller stopped successfully")
        
        logger.info("\n=== All tests passed! P&L V2 UI framework is working ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_pnl_v2_ui()
    sys.exit(0 if success else 1) 