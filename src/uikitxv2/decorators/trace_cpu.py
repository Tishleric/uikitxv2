from __future__ import annotations

# Bridge module: keeps the import path uikitxv2.decorators.trace_cpu
# while the real implementation lives in decorators.performance.cpu
from .performance.cpu import trace_cpu  # noqa: F401

__all__ = ["trace_cpu"]
