from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


EXCLUDE_DIR_NAMES = {".git", "__pycache__", ".pytest_cache"}
DEFAULT_OUTPUT = Path("memory-bank/index/manifest.jsonl")


def iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place for efficiency
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for name in filenames:
            yield Path(dirpath) / name


def is_binary_file(path: Path, probe_bytes: int = 1024) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(probe_bytes)
        return b"\x00" in chunk
    except Exception:
        return True


def sha1_file(path: Path, buf_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            b = f.read(buf_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> None:
    """Scan the repository and write a JSONL manifest of all files (excl. hidden caches)."""
    root = Path(".").resolve()
    out_path = DEFAULT_OUTPUT
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out:
        for fpath in iter_files(root):
            try:
                stat = fpath.stat()
                record = {
                    "path": str(fpath.as_posix()),
                    "size_bytes": stat.st_size,
                    "mtime_iso": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "ext": fpath.suffix,
                    "is_binary": is_binary_file(fpath),
                    "sha1": sha1_file(fpath),
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                err = {"path": str(fpath.as_posix()), "error": repr(e)}
                out.write(json.dumps(err, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

