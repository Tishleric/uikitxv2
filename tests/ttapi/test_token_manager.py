# tests/ttapi/test_token_manager.py

"""Unit tests for :mod:`TTRestAPI.token_manager`."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from trading.tt_api.token_manager import TTTokenManager


@pytest.fixture()
def tmp_token_path(tmp_path: Path) -> Path:
    """Return path for storing temporary token files."""
    return tmp_path / "token.json"


@pytest.fixture()
def bare_manager(tmp_token_path: Path) -> TTTokenManager:
    """Create a token manager using fake config and no preload."""

    fake_cfg = SimpleNamespace(
        APP_NAME="TestApp",
        COMPANY_NAME="TestCo",
        TT_API_KEY="k",
        TT_API_SECRET="s",
        TT_SIM_API_KEY="sk",
        TT_SIM_API_SECRET="ss",
        ENVIRONMENT="SIM",
        TOKEN_FILE="token.json",
        AUTO_REFRESH=True,
        REFRESH_BUFFER_SECONDS=1,
    )

    with patch.object(TTTokenManager, "_load_token"):
        mgr = TTTokenManager(
            api_key="k",
            api_secret="s",
            app_name="TestApp",
            company_name="TestCo",
            environment="SIM",
            token_file_base="token.json",
            refresh_buffer_seconds=1,
            config_module=fake_cfg,
        )
    mgr.token_file = str(tmp_token_path)
    return mgr


def test_token_acquisition_saves_file(bare_manager: TTTokenManager, tmp_token_path: Path) -> None:
    """Token is acquired and stored on disk."""
    token_data = {
        "access_token": "abc",
        "token_type": "bearer",
        "seconds_until_expiry": 3600,
    }

    mock_response = MagicMock(status_code=200, json=lambda: token_data)

    with patch("requests.post", return_value=mock_response):
        token = bare_manager.get_token(force_refresh=True)

    assert token == "abc"
    assert bare_manager.token_type == "bearer"
    assert bare_manager.expiry_time is not None
    saved = json.loads(tmp_token_path.read_text())
    assert saved["access_token"] == "abc"


def test_auto_refresh_uses_acquire(bare_manager: TTTokenManager) -> None:
    """`get_token` refreshes when expiry is near."""
    bare_manager.token = "old"
    bare_manager.expiry_time = datetime.now() + timedelta(seconds=0)

    with patch.object(bare_manager, "_acquire_token", return_value=True) as acquire:
        bare_manager.token = "new"
        token = bare_manager.get_token()

    acquire.assert_called_once()
    assert token == "new"


def test_get_auth_header(bare_manager: TTTokenManager) -> None:
    """Returned header wraps token in bearer format."""
    with patch.object(bare_manager, "get_token", return_value="tok"):
        header = bare_manager.get_auth_header()

    assert header == {"Authorization": "Bearer tok"}

    with patch.object(bare_manager, "get_token", return_value=None):
        header = bare_manager.get_auth_header()

    assert header == {}
