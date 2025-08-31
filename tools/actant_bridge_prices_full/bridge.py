from __future__ import annotations

import logging
import pickle
import time
from typing import Optional

import pyarrow as pa
import redis

from .actant_client import ActantMultiRowClient
from .config import (
    DRY_RUN,
    MAX_ROWS_PER_UPDATE,
    REDIS_CHANNEL,
    REDIS_HOST,
    REDIS_PORT,
    UNDERLYING_BASE,
    ACTANT_ALLOWED_EXPIRY_TOKENS,
)
from .formatting import compute_underlying_price, transform_batch


logger = logging.getLogger(__name__)


class ActantCLIBridgeService:
    def __init__(self) -> None:
        self._redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        self._client = ActantMultiRowClient()

    def _send_in_chunks(self, scope_keys, field_names, value_types, values):
        n = len(scope_keys)
        if n == 0:
            return
        step = max(1, int(MAX_ROWS_PER_UPDATE))
        for i in range(0, n, step):
            ks = scope_keys[i : i + step]
            vals = values[i : i + step]
            self._client.send_batch(ks, field_names, value_types, vals)

    def run_forever(self) -> None:
        logger.info(f"ActantCLIBridgeService subscribing to {REDIS_CHANNEL} at {REDIS_HOST}:{REDIS_PORT}")
        ps = self._redis.pubsub()
        ps.subscribe(REDIS_CHANNEL)
        for msg in ps.listen():
            if msg.get("type") != "message":
                continue
            now = time.time()
            payload = pickle.loads(msg["data"])  # {'data': arrow-bytes, 'publish_timestamp': float, ...}
            pub_ts = float(payload.get("publish_timestamp", now))
            reader = pa.ipc.open_stream(payload["data"])  # Arrow IPC stream
            table = reader.read_all()
            df = table.to_pandas()
            logger.info(f"Batch received: rows={len(df)} latency={now - pub_ts:.3f}s")

            und = compute_underlying_price(df, underlying_base=UNDERLYING_BASE)
            if und is None:
                logger.warning("No underlying price derived for this batch; PI6 will be set to 0.0")

            scope_keys, field_names, value_types, values = transform_batch(
                df,
                und,
                allowed_expiry_tokens=ACTANT_ALLOWED_EXPIRY_TOKENS,
            )
            logger.info(
                f"Transformed: options={len(scope_keys)} fields={field_names} sample_scope={scope_keys[:1]} sample_values={values[:1]}"
            )

            self._send_in_chunks(scope_keys, field_names, value_types, values)

