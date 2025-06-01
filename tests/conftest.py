"""
Global pytest fixtures for the uikitxv2 test-suite.

• Exposes the bundled chromedriver.exe to Selenium / dash_duo and
  disables webdriver-manager downloads, so integration tests work
  offline and on CI.
"""
from __future__ import annotations

import os
import pytest
import sys
from pathlib import Path

import chromedriver_binary  # noqa: F401  – importing unpacks the wheel

# Add project root to Python path for testing
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# --------------------------------------------------------------------------- #
#  Selenium / dash_duo bootstrap
# --------------------------------------------------------------------------- #
def pytest_configure() -> None:
    """
    Runs once, before test collection.

    1 Prepend the folder that contains chromedriver(.exe) to PATH so
        Selenium can find it instead of trying to download another copy.
    2 Tell webdriver-manager to skip network downloads entirely.
    """
    driver_dir = Path(chromedriver_binary.chromedriver_filename).parent
    os.environ["PATH"] = f"{driver_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    os.environ["WDM_SKIP_DOWNLOAD"] = "1"


@pytest.fixture
def sample_theme():
    """Provide a sample theme for component testing."""
    from components.themes import Theme
    
    return Theme(
        base_bg="#ffffff",
        panel_bg="#f5f5f5",
        primary="#1976d2",
        secondary="#dc004e",
        accent="#9c27b0",
        text_light="#333333",
        text_subtle="#666666",
        danger="#f44336",
        success="#4caf50"
    )


@pytest.fixture
def sample_dataframe():
    """Provide a sample pandas DataFrame for testing."""
    import pandas as pd
    
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100.5, 200.3, 150.7]
    })


@pytest.fixture
def sample_plotly_figure():
    """Provide a sample plotly figure for testing."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[1, 2, 3, 4],
        y=[10, 11, 12, 13],
        mode='lines+markers',
        name='test trace'
    ))
    return fig
