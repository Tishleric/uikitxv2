"""Test that all imports work correctly from the reorganized package structure."""

import pytest


class TestComponentImports:
    """Test importing UI components."""
    
    def test_import_all_components(self):
        """Test importing all components from the main components module."""
        from components import (
            Button, Checkbox, ComboBox, Container, DataTable, 
            Graph, Grid, ListBox, Mermaid, RadioButton, 
            RangeSlider, Tabs, Toggle
        )
        
        # Verify all components are imported
        assert Button is not None
        assert Checkbox is not None
        assert ComboBox is not None
        assert Container is not None
        assert DataTable is not None
        assert Graph is not None
        assert Grid is not None
        assert ListBox is not None
        assert Mermaid is not None
        assert RadioButton is not None
        assert RangeSlider is not None
        assert Tabs is not None
        assert Toggle is not None
    
    def test_import_themes(self):
        """Test importing theme utilities."""
        from components.themes import Theme, default_theme
        
        assert Theme is not None
        assert default_theme is not None
        assert isinstance(default_theme, Theme)
    
    def test_import_core(self):
        """Test importing core classes and protocols."""
        from components.core import BaseComponent, DataServiceProtocol, MermaidProtocol
        
        assert BaseComponent is not None
        assert DataServiceProtocol is not None
        assert MermaidProtocol is not None


class TestMonitoringImports:
    """Test importing monitoring and logging utilities."""
    
    def test_import_decorators(self):
        """Test importing all decorators."""
        from monitoring.decorators import (
            TraceTime, TraceCpu, TraceMemory, TraceCloser
        )
        
        assert TraceTime is not None
        assert TraceCpu is not None
        assert TraceMemory is not None
        assert TraceCloser is not None
    
    def test_import_logging(self):
        """Test importing logging utilities."""
        from monitoring.logging import setup_logging, SQLiteHandler
        
        assert setup_logging is not None
        assert SQLiteHandler is not None


class TestTradingImports:
    """Test importing trading utilities."""
    
    def test_import_common_utilities(self):
        """Test importing common trading utilities."""
        from trading.common import (
            decimal_to_tt_bond_format,
            tt_bond_format_to_decimal,
            parse_treasury_price,
            format_treasury_price,
            parse_and_convert_pm_price,
            format_shock_value_for_display,
            convert_percentage_to_decimal,
            get_monthly_expiry_code,
            get_third_friday,
            get_futures_expiry_date,
            parse_expiry_date,
            get_trading_days_between,
            is_trading_day
        )
        
        # Price parsing functions
        assert decimal_to_tt_bond_format is not None
        assert tt_bond_format_to_decimal is not None
        assert parse_treasury_price is not None
        assert format_treasury_price is not None
        assert parse_and_convert_pm_price is not None
        assert format_shock_value_for_display is not None
        assert convert_percentage_to_decimal is not None
        
        # Date utilities
        assert get_monthly_expiry_code is not None
        assert get_third_friday is not None
        assert get_futures_expiry_date is not None
        assert parse_expiry_date is not None
        assert get_trading_days_between is not None
        assert is_trading_day is not None
    
    def test_import_actant_eod(self):
        """Test importing Actant EOD modules."""
        from trading.actant.eod import (
            ActantDataService,
            get_most_recent_json_file,
            get_json_file_metadata
        )
        
        assert ActantDataService is not None
        assert get_most_recent_json_file is not None
        assert get_json_file_metadata is not None
    
    def test_import_pricing_monkey(self):
        """Test importing Pricing Monkey modules."""
        from trading.pricing_monkey.retrieval import get_extended_pm_data, PMRetrievalError
        from trading.pricing_monkey.processors import process_pm_for_separate_table, validate_pm_data
        
        assert get_extended_pm_data is not None
        assert PMRetrievalError is not None
        assert process_pm_for_separate_table is not None
        assert validate_pm_data is not None
    
    def test_import_tt_api(self):
        """Test importing TT API modules."""
        from trading.tt_api import (
            TTTokenManager,
            generate_guid,
            create_request_id,
            sanitize_request_id_part,
            format_bearer_token,
            is_valid_guid,
            APP_NAME,
            COMPANY_NAME,
            ENVIRONMENT,
            TOKEN_FILE
        )
        
        # Classes and functions
        assert TTTokenManager is not None
        assert generate_guid is not None
        assert create_request_id is not None
        assert sanitize_request_id_part is not None
        assert format_bearer_token is not None
        assert is_valid_guid is not None
        
        # Configuration values
        assert APP_NAME is not None
        assert COMPANY_NAME is not None
        assert ENVIRONMENT is not None
        assert TOKEN_FILE is not None


class TestFunctionality:
    """Test basic functionality of imported modules."""
    
    def test_theme_creation(self):
        """Test creating a theme instance."""
        from components.themes import Theme
        
        theme = Theme(
            base_bg="#000000",
            panel_bg="#111111",
            primary="#2196f3",
            secondary="#f50057",
            accent="#651fff",
            text_light="#ffffff",
            text_subtle="#cccccc",
            danger="#ff5252",
            success="#69f0ae"
        )
        
        assert theme.base_bg == "#000000"
        assert theme.primary == "#2196f3"
    
    def test_price_parsing(self):
        """Test price parsing functions work correctly."""
        from trading.common import decimal_to_tt_bond_format, tt_bond_format_to_decimal
        
        # Test conversion to TT format
        tt_format = decimal_to_tt_bond_format(110.15625)
        assert tt_format == "110'050"
        
        # Test parsing from TT format
        decimal_price = tt_bond_format_to_decimal("110'050")
        assert decimal_price == 110.15625
    
    def test_expiry_code(self):
        """Test expiry code generation."""
        from trading.common import get_monthly_expiry_code
        
        assert get_monthly_expiry_code(1) == 'F'  # January
        assert get_monthly_expiry_code(3) == 'H'  # March
        assert get_monthly_expiry_code(12) == 'Z'  # December
    
    def test_shock_value_formatting(self):
        """Test shock value formatting."""
        from trading.common import format_shock_value_for_display
        
        # Percentage formatting (no + sign for positive values)
        assert format_shock_value_for_display(0.025, "percentage") == "2.5%"
        assert format_shock_value_for_display(-0.1, "percentage") == "-10%"
        
        # Absolute USD formatting ($ prefix, but no + sign)
        assert format_shock_value_for_display(5.0, "absolute_usd") == "$5.00"
        assert format_shock_value_for_display(-2.5, "absolute_usd") == "-$2.50" 