"""
Monitor Spot Risk Redis Channel (read-only)

Usage (on Actant machine):
  python monitor_spotrisk.py

Notes:
- No Redis server needed locally; only Python client libs.
- Configure HOST/PORT below if needed.
- Prints per-batch latency and row counts; no side effects.
"""

import pickle
import time
from typing import Optional

import pyarrow as pa  # pip install pyarrow
import pyarrow.compute as pc
import redis  # pip install redis


# Configuration (edit if needed)
HOST: str = "100.83.215.91"  # Producer Tailscale IP
PORT: int = 6379
CHANNEL: str = "spot_risk:prices_full"
USERNAME: Optional[str] = None  # e.g., "actant" if ACL enabled
PASSWORD: Optional[str] = None  # e.g., "STRONG_LONG_PASSWORD"


def _count_futures_rows(table: pa.Table) -> int:
    if "itype" not in table.column_names:
        return 0
    arr = table.column("itype").combine_chunks().cast(pa.string())
    is_f = pc.equal(pc.utf8_upper(arr), pc.scalar("F"))
    return int(pc.sum(pc.cast(is_f, pa.int64())).as_py())


def main() -> None:
    client = redis.Redis(host=HOST, port=PORT, username=USERNAME, password=PASSWORD)
    pubsub = client.pubsub()
    pubsub.subscribe(CHANNEL)
    print(f"Subscribed to '{CHANNEL}' on {HOST}:{PORT}. Waiting for messages... (Ctrl+C to stop)")

    try:
        for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            now = time.time()
            payload = pickle.loads(message["data"])  # {'data': <arrow-bytes>, 'publish_timestamp': float, ...}
            pub_ts = float(payload.get("publish_timestamp", now))
            reader = pa.ipc.open_stream(payload["data"])  # Arrow IPC stream
            table = reader.read_all()
            n_rows = table.num_rows
            n_fut = _count_futures_rows(table)
            print(f"latency={now - pub_ts:.3f}s rows={n_rows} futures={n_fut}")
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

