from __future__ import annotations

import asyncio
import importlib
import logging
import sys
import threading
import time
from typing import List

from .config import (
    ACTANT_CALL_TIMEOUT_S,
    ACTANT_IP,
    ACTANT_PASSWORD,
    ACTANT_PORT,
    ACTANT_RETRY,
    ACTANT_SCRIPTS_PATH,
    ACTANT_USER,
    DRY_RUN,
)


logger = logging.getLogger(__name__)


def ensure_actant_path() -> None:
    if ACTANT_SCRIPTS_PATH not in sys.path:
        sys.path.append(ACTANT_SCRIPTS_PATH)
        logger.info(f"Added Actant scripts path: {ACTANT_SCRIPTS_PATH}")


class AsyncLoopManager:
    """Owns a background event loop for running async coroutines safely."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name="ActantAsyncLoop",
            daemon=True,
        )
        self._thread.start()
        logger.info("Started background asyncio event loop for Actant calls.")

    def run_coro(self, coro, timeout_s: int) -> None:
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        fut.result(timeout=timeout_s)


class ActantMultiRowClient:
    """Thin wrapper to call Actant's push_vol_surface_multi_row module."""

    def __init__(self) -> None:
        self._module = None
        self._loop_mgr = AsyncLoopManager()

    def _load(self):
        if self._module is None:
            ensure_actant_path()
            self._module = importlib.import_module("push_vol_surface_multi_row")
            logger.info("Loaded push_vol_surface_multi_row module.")

    def _to_str_matrix(self, values: List[List[float]]) -> List[List[str]]:
        out: List[List[str]] = []
        for row in values:
            out.append([str(v) if v is not None else "" for v in row])
        return out

    def send_batch(
        self,
        scope_keys: List[str],
        field_names: List[str],
        value_types: List[str],
        values: List[List[float]],
    ) -> None:
        if DRY_RUN:
            logger.info(
                f"DRY_RUN: would send to Actant: rows={len(scope_keys)} fields={field_names} sample={values[:1]}"
            )
            return
        if not scope_keys:
            return
        self._load()
        if not hasattr(self._module, "run"):
            raise RuntimeError("push_vol_surface_multi_row module does not expose 'run' function")

        # Convert to the string matrix the script expects
        str_values = self._to_str_matrix(values)

        attempt = 0
        while True:
            attempt += 1
            try:
                coro = self._module.run(
                    ip=ACTANT_IP,
                    port=ACTANT_PORT,
                    user=ACTANT_USER,
                    password=ACTANT_PASSWORD,
                    scope_keys=scope_keys,
                    field_names=field_names,
                    value_types=value_types,
                    values=str_values,
                )
                self._loop_mgr.run_coro(coro, timeout_s=ACTANT_CALL_TIMEOUT_S)
                logger.info(f"Sent {len(scope_keys)} rows to Actant.")
                return
            except Exception as e:
                if attempt > max(1, ACTANT_RETRY + 1):
                    logger.error(f"Actant call failed after retries: {e}", exc_info=True)
                    raise
                logger.warning(f"Actant call failed (attempt {attempt}), retrying: {e}")
                time.sleep(0.5)

