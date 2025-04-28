from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from uikitxv2.core.logger_protocol import LoggerProtocol

from .models import Base, TraceLog

_DB_ENV = "UIKITX_DB_PATH"
_DEFAULT_PATH = Path.home() / ".uikitx" / "traces.db"

# --------------------------------------------------------------------------- #
#   Engine cache keyed by database path
# --------------------------------------------------------------------------- #
_ENGINE_CACHE: Dict[Path, sessionmaker[Session]] = {}   # ★ add generics


def _get_db_path() -> Path:
    return Path(os.getenv(_DB_ENV, _DEFAULT_PATH)).expanduser()


def _sessionmaker_for(path: Path) -> sessionmaker[Session]:          # ★
    """Return a sessionmaker bound to an engine for *path*, caching per path."""
    if path not in _ENGINE_CACHE:
        engine = create_engine(f"sqlite:///{path}", future=True, echo=False)
        Base.metadata.create_all(engine)
        _ENGINE_CACHE[path] = sessionmaker(bind=engine, autoflush=False, future=True)
    return _ENGINE_CACHE[path]


# --------------------------------------------------------------------------- #
#   Public helpers
# --------------------------------------------------------------------------- #
@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session bound to the *current* UIKITX_DB_PATH."""
    sm = _sessionmaker_for(_get_db_path())
    session: Session = sm()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


class SQLiteLogger(LoggerProtocol):
    """Concrete Logger writing TraceLog rows to SQLite."""

    def write(
        self,
        log_type: str,
        name: str,
        data: dict[str, Any],                   # ★ explicit key/value types
        *,
        ts: datetime | None = None,             # ★ annotate ts
        duration_ms: float | None = None,
    ) -> None:
        with get_session() as s:
            s.add(
                TraceLog(
                    ts=ts,
                    log_type=log_type,
                    name=name,
                    duration_ms=duration_ms,
                    payload_json=data,
                )
            )
