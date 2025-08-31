"""Snapshot Service Protocol

Defines a minimal interface for long-running snapshot services that execute
periodic data collection and output emission. This mirrors the archiver
interface used elsewhere in the codebase to keep orchestration consistent.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Dict, Any


@runtime_checkable
class SnapshotServiceProtocol(Protocol):
    """Protocol for snapshot services.

    Implementations should perform a single snapshot operation in `run_once`
    and a perpetual loop in `run_forever` with internal scheduling/sleep.
    """

    def run_once(self, config: Dict[str, Any]) -> None:
        """Perform one snapshot cycle using the provided configuration."""
        ...

    def run_forever(self, config: Dict[str, Any]) -> None:
        """Run the snapshot service in a perpetual loop until interrupted."""
        ...

