"""
Global pytest fixtures for the uikitxv2 test-suite.

• Spins up an isolated SQLite file via UIKITX_DB_PATH for every test.
• Exposes the bundled chromedriver.exe to Selenium / dash_duo and
  disables webdriver-manager downloads, so integration tests work
  offline and on CI.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import chromedriver_binary  # noqa: F401  – importing unpacks the wheel
import pytest
import sqlalchemy as sa

from uikitxv2.db.session import get_engine  # existing helper


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


# --------------------------------------------------------------------------- #
#  Per-test temporary SQLite database
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Each test gets its own throw-away SQLite file."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)  # we only need the path; SQLAlchemy will open the file

    old_db_path = os.environ.get("UIKITX_DB_PATH")
    os.environ["UIKITX_DB_PATH"] = temp_db_path
    try:
        yield
    finally:
        Path(temp_db_path).unlink(missing_ok=True)
        if old_db_path is not None:
            os.environ["UIKITX_DB_PATH"] = old_db_path
        else:
            os.environ.pop("UIKITX_DB_PATH", None)

# --------------------------------------------------------------------------- #
# Create TraceLog table in the temp database
# --------------------------------------------------------------------------- #

_DDL_PATH = Path("src/uikitxv2/db/migrations/0001_trace_log.sql")

@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    with get_engine().begin() as conn:
        conn.execute(sa.text(_DDL_PATH.read_text()))