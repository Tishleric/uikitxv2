"""Trading utilities and components for UIKitXv2.

Avoid importing heavy subpackages at module import time to prevent circular
imports and environment-specific dependency issues. Access subpackages via
attribute (lazy import) or import explicit submodules, e.g.::

    from trading.bond_future_options import pricing_engine

"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
	"bond_future_options",
]


def __getattr__(name: str) -> Any:
	if name == "bond_future_options":
		return importlib.import_module(__name__ + ".bond_future_options")
	raise AttributeError(name)
