"""
Global pytest fixtures for the uikitxv2 test-suite.
Creates an isolated SQLite file via UIKITX_DB_PATH for each session.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():

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