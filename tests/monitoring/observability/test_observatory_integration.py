"""Integration tests for Observatory Dashboard"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from apps.dashboards.observatory.app import app
from apps.dashboards.observatory.callbacks import register_callbacks
from apps.dashboards.observatory import (
    ObservatoryDataService,
    MetricsAggregator,
    TraceAnalyzer,
    ObservatoryViews
)
from lib.monitoring.decorators.monitor import monitor, start_observability_writer, stop_observability_writer


class TestObservatoryIntegration:
    """Test Observatory dashboard integration"""
    
    def test_app_creation(self):
        """Test that the Dash app is created successfully"""
        assert app is not None
        assert app.layout is not None
        
        # Check that layout contains expected components
        layout_str = str(app.layout)
        assert "observatory-dashboard" in layout_str
        assert "overview-interval" in layout_str
        assert "traces-interval" in layout_str
    
    def test_callback_registration(self):
        """Test that callbacks can be registered"""
        # Create mock services
        mock_data_service = MagicMock(spec=ObservatoryDataService)
        mock_metrics = MagicMock(spec=MetricsAggregator)
        mock_analyzer = MagicMock(spec=TraceAnalyzer)
        
        # Create a test app
        from dash import Dash
        test_app = Dash(__name__)
        
        # Register callbacks should not raise errors
        try:
            register_callbacks(test_app, mock_data_service, mock_metrics, mock_analyzer)
        except Exception as e:
            pytest.fail(f"Callback registration failed: {e}")
    
    def test_data_flow_integration(self, tmp_path):
        """Test data flow from @monitor to dashboard"""
        # Use temporary database
        db_path = str(tmp_path / "test_observatory.db")
        
        # Start writer with temporary database
        writer = start_observability_writer(db_path=db_path)
        
        try:
            # Generate some test data
            @monitor(process_group="test.integration")
            def test_function(x, y):
                return x + y
            
            # Call function multiple times
            for i in range(5):
                result = test_function(i, i + 1)
                assert result == 2 * i + 1
            
            # Give writer time to flush
            time.sleep(0.5)
            
            # Create data service with test database
            data_service = ObservatoryDataService(db_path=db_path)
            
            # Verify data is available
            stats = data_service.get_system_stats()
            assert stats['total_traces'] >= 5
            
            # Verify trace data
            df, total = data_service.get_trace_data()
            assert total >= 10  # At least 5 calls * 2 data points (args + result)
            
            # Verify process metrics
            metrics_df = data_service.get_process_metrics(hours=1)
            assert not metrics_df.empty
            assert 'test.integration.test_function' in metrics_df['process'].values
            
        finally:
            stop_observability_writer()
    
    def test_views_render_with_data(self, tmp_path):
        """Test that views render correctly with actual data"""
        # Create test database with data
        db_path = str(tmp_path / "test_views.db")
        writer = start_observability_writer(db_path=db_path)
        
        try:
            # Generate test data
            @monitor(process_group="ui.test")
            def sample_function():
                return "test"
            
            sample_function()
            time.sleep(0.5)  # Wait for write
            
            # Create services
            data_service = ObservatoryDataService(db_path=db_path)
            views = ObservatoryViews()
            
            # Test that views can be created without errors
            header = views.create_header()
            assert header is not None
            
            tabs = views.create_tabs()
            assert tabs is not None
            
            layout = views.create_layout()
            assert layout is not None
            
        finally:
            stop_observability_writer()
    
    def test_error_handling(self, tmp_path):
        """Test dashboard handles errors gracefully"""
        # Create data service with non-existent database
        data_service = ObservatoryDataService(db_path=str(tmp_path / "nonexistent.db"))
        
        # Should handle gracefully
        stats = data_service.get_system_stats()
        assert stats['total_traces'] == 0
        assert stats['total_data_points'] == 0
        
        df, total = data_service.get_trace_data()
        assert df.empty
        assert total == 0
        
        metrics_df = data_service.get_process_metrics(hours=1)
        assert metrics_df.empty
    
    def test_main_dashboard_integration(self):
        """Test that Observatory integrates correctly with main dashboard"""
        # Try importing the main dashboard app
        try:
            from apps.dashboards.main.app import app as main_app
            
            # Check that Observatory callbacks were registered
            assert hasattr(main_app, '_observatory_callbacks_registered')
            assert main_app._observatory_callbacks_registered is True
            
            # Verify the navigation contains Observatory
            layout = str(main_app.layout)
            assert "Observatory" in layout or "observatory" in layout
            
        except ImportError as e:
            pytest.skip(f"Main dashboard not available: {e}")
    
    def test_observatory_database_path(self):
        """Test that Observatory uses the correct database path"""
        # Should use logs/observatory.db, not logs/observability.db
        data_service = ObservatoryDataService()
        assert data_service.db_path == "logs/observatory.db"
        assert "observability.db" not in data_service.db_path 