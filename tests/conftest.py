"""
Global pytest fixtures for the uikitxv2 test-suite.

• Exposes the bundled chromedriver.exe to Selenium / dash_duo and
  disables webdriver-manager downloads, so integration tests work
  offline and on CI.
"""
from __future__ import annotations

import os
from pathlib import Path

import chromedriver_binary  # noqa: F401  – importing unpacks the wheel


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
