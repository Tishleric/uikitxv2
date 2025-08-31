from __future__ import annotations

import pytest


def test_app_builds_without_error():
    from apps.dashboards.aggregated_explorer.app import create_app

    app = create_app()
    assert app is not None


