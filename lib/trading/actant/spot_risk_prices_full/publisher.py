import logging
import pickle
import time
from typing import Dict, Any, List

import pyarrow as pa
import redis

from core.price_streams import PriceBatchPublisher


logger = logging.getLogger(__name__)


class PriceOnlyResultPublisher(PriceBatchPublisher):
    """Publishes consolidated price batches to Redis as Arrow-in-pickle envelopes."""

    def __init__(self, channel: str = "spot_risk:prices_full", host: str = "127.0.0.1", port: int = 6379):
        self.redis_client = redis.Redis(host=host, port=port)
        self.redis_channel = channel
        logger.info(f"PriceOnlyResultPublisher initialized for channel '{self.redis_channel}'.")

    def publish(self, batch_id: str, arrow_table: pa.Table) -> None:
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, arrow_table.schema) as writer:
            writer.write_table(arrow_table)
        buffer = sink.getvalue()

        payload: Dict[str, Any] = {
            "batch_id": batch_id,
            "publish_timestamp": time.time(),
            "format": "arrow",
            "data": buffer,
        }
        pickled_payload = pickle.dumps(payload)

        num = self.redis_client.publish(self.redis_channel, pickled_payload)
        logger.info(
            f"Published prices_full batch '{batch_id}' ({len(pickled_payload)/(1024*1024):.2f} MB) to '{self.redis_channel}' → subscribers: {num}"
        )

