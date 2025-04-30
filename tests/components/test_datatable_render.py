import pytest

# Assuming your project structure allows importing from src like this
# Adjust if necessary based on your pytest setup (e.g., conftest.py sys.path modification)
from components.datatable import DataTable
from utils.colour_palette import default_theme

# Sample data for testing
SAMPLE_COLUMNS = [
    {"name": "Column A", "id": "col_a"},
    {"name": "Column B", "id": "col_b"},
]
SAMPLE_DATA = [
    {"col_a": 1, "col_b": "Apple"},
    {"col_a": 2, "col_b": "Banana"},
]

def test_datatable_render_defaults():
    """Tests rendering DataTable with default settings."""
    dt_wrapper = DataTable(data=SAMPLE_DATA, columns=SAMPLE_COLUMNS)
    dt = dt_wrapper.render() # Get the underlying dash_table.DataTable

    # Check basic properties
    assert dt.id.startswith("datatable-")
    assert dt.data == SAMPLE_DATA
    assert dt.columns == SAMPLE_COLUMNS
    assert dt.page_size == 15 # Default page size
    assert dt.sort_action == "native"
    assert dt.filter_action == "native"
    assert dt.page_action == "native"
    assert dt.style_as_list_view is True

    # Check theme styling application (spot checks)
    assert dt.style_header["backgroundColor"] == default_theme.panel_bg
    assert dt.style_header["color"] == default_theme.primary
    assert dt.style_cell["color"] == default_theme.text_light
    assert dt.style_cell["border"] == f"1px solid {default_theme.secondary}"
    # Check conditional style for striped rows
    assert len(dt.style_data_conditional) > 0
    assert dt.style_data_conditional[0]["if"] == {'row_index': 'odd'}
    assert dt.style_data_conditional[0]["backgroundColor"] == default_theme.base_bg
    # Check filter style
    assert dt.style_filter["backgroundColor"] == default_theme.base_bg
    assert dt.style_filter["color"] == default_theme.text_light

def test_datatable_render_custom_args():
    """Tests rendering DataTable with custom arguments overriding defaults."""
    custom_id = "my-custom-table"
    custom_page_size = 5
    # Example of overriding a style argument
    custom_style_cell = {"padding": "10px", "color": "red"} # Intentionally override theme color

    dt_wrapper = DataTable(
        id=custom_id,
        data=SAMPLE_DATA,
        columns=SAMPLE_COLUMNS,
        page_size=custom_page_size,
        sort_action="none",
        style_cell=custom_style_cell # Pass a custom style
    )
    dt = dt_wrapper.render()

    # Check custom properties
    assert dt.id == custom_id
    assert dt.page_size == custom_page_size
    assert dt.sort_action == "none"

    # Check that the custom style_cell overrides the theme default
    assert dt.style_cell["padding"] == "10px"
    assert dt.style_cell["color"] == "red" # Overrode theme color
    # Ensure other theme styles that weren't overridden are still applied
    assert dt.style_header["backgroundColor"] == default_theme.panel_bg

def test_datatable_render_empty():
    """Tests rendering DataTable with no data or columns initially."""
    dt_wrapper = DataTable() # No data/columns passed
    dt = dt_wrapper.render()

    assert dt.id.startswith("datatable-")
    assert dt.data == []
    assert dt.columns == []
    # Check that styling is still applied even when empty
    assert dt.style_header["backgroundColor"] == default_theme.panel_bg

