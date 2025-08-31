"""
Pricing Monkey integration for automated trading data collection.

This package exposes multiple submodules (automation, retrieval, processors,
and runners). To avoid heavy imports and environment-specific dependencies
when the package is imported for a single utility (e.g. a runner), we keep
the top-level ``__init__`` lightweight and avoid eager imports.

Import concrete APIs directly from their submodules, for example:

    from trading.pricing_monkey.playwright_basic_runner import PMBasicRunner
    from trading.pricing_monkey.retrieval import get_simple_data

"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
	"automation",
	"retrieval",
	"processors",
	"playwright_basic_runner",
]


def __getattr__(name: str) -> Any:
	# Lazy access to common subpackages if referenced as attributes
	if name in {"automation", "retrieval", "processors", "playwright_basic_runner"}:
		return importlib.import_module(__name__ + "." + name)
	raise AttributeError(name)
