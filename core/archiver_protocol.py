"""Archiver service protocol.

Defines the minimal interface required for any long-running file archiver
service used in this repository. New archiver implementations should conform
to this protocol to enable consistent orchestration and testing.

This module intentionally contains no implementation details.
"""

from __future__ import annotations

from typing import Protocol


class ArchiverService(Protocol):

	def run_once(self) -> None:
		"""Execute a single archive cycle.

		Implementations should scan for eligible items and perform moves
		atomically where possible. This method must be idempotent and safe to
		retry; partial failures should be logged and retried on subsequent calls.
		"""

	def run_forever(self) -> None:
		"""Run the service loop until interrupted.

		Implementations should handle sleep intervals, jitter, and single-instance
		guards internally. Interruptions must not corrupt state.
		"""

