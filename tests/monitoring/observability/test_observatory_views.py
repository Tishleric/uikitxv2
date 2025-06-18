"""Test Observatory dashboard views"""

import pytest
from dash import html

from apps.dashboards.observatory.views import ObservatoryViews
from components.themes import default_theme


class TestObservatoryViews:
    """Test Observatory UI views"""
    
    def test_observatory_views_init(self):
        """Test ObservatoryViews initialization"""
        views = ObservatoryViews()
        assert views.theme == default_theme
        
        # Test with custom theme
        custom_theme = default_theme
        views = ObservatoryViews(theme=custom_theme)
        assert views.theme == custom_theme
    
    def test_create_header(self):
        """Test header creation"""
        views = ObservatoryViews()
        header = views.create_header()
        
        # Check it's a Dash component
        assert hasattr(header, 'children')
        assert header.id == "observatory-header"
        
        # Check it contains the title
        header_str = str(header)
        assert "Observatory Dashboard" in header_str
    
    def test_create_tabs(self):
        """Test tabs creation"""
        views = ObservatoryViews()
        tabs = views.create_tabs()
        
        # Check it's a Dash component
        assert hasattr(tabs, 'children')
        assert tabs.id == "observatory-tabs"
        
        # Check it has the expected tabs
        assert hasattr(tabs, 'active_tab')
        assert tabs.active_tab == "observatory-tabs-tab-0"  # First tab is active
    
    def test_create_layout(self):
        """Test complete layout creation"""
        views = ObservatoryViews()
        layout = views.create_layout()
        
        # Check it's a Dash component
        assert hasattr(layout, 'children')
        assert layout.id == "observatory-dashboard"
        
        # Check it contains header and tabs
        assert len(layout.children) == 2
    
    def test_metric_card_creation(self):
        """Test metric card creation"""
        views = ObservatoryViews()
        card = views._create_metric_card("Test Title", "42", "test-card")
        
        # Check structure
        assert hasattr(card, 'children')
        assert card.id == "test-card-container"
        
        # Check it contains title and value
        card_str = str(card)
        assert "Test Title" in card_str
        assert "42" in card_str
    
    def test_tab_content_creation(self):
        """Test that all tabs can be created without errors"""
        views = ObservatoryViews()
        
        tab_ids = ["overview", "trace-explorer", "code-inspector", "alerts", "settings"]
        
        for tab_id in tab_ids:
            content = views._create_tab_content(tab_id)
            assert content is not None
            assert hasattr(content, 'children')
            # Each tab should have a unique ID
            assert content.id == f"{tab_id}-content"
    
    def test_overview_tab_components(self):
        """Test overview tab has expected components"""
        views = ObservatoryViews()
        overview = views._create_overview_tab()
        
        # Check it has metrics grid, top processes, and recent errors
        overview_str = str(overview)
        assert "overview-metrics-grid" in overview_str
        assert "top-processes-table" in overview_str
        assert "recent-errors-table" in overview_str
    
    def test_trace_explorer_tab_components(self):
        """Test trace explorer tab has expected components"""
        views = ObservatoryViews()
        trace_explorer = views._create_trace_explorer_tab()
        
        # Check it has filters, table, and pagination
        explorer_str = str(trace_explorer)
        assert "trace-process-filter" in explorer_str
        assert "trace-status-filter" in explorer_str
        assert "trace-explorer-table" in explorer_str
        assert "trace-pagination" in explorer_str
    
    def test_no_raw_dash_components(self):
        """Test that views only use wrapped components"""
        views = ObservatoryViews()
        layout = views.create_layout()
        
        # Convert to string and check for dash imports
        layout_str = str(layout)
        
        # Should not contain direct dash component references
        assert "dcc." not in layout_str
        assert "dbc." not in layout_str
        assert "html.Div" not in layout_str
        
        # Should use our wrapped components
        assert views.__module__ == "apps.dashboards.observatory.views" 