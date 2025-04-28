from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
_DB_ENV = "UIKITX_DB_PATH"
_DEFAULT_PATH = Path.home() / ".uikitx" / "traces.db"

# -----------------------------------------------------------------------------
# Caches (keyed by absolute DB-path)
# -----------------------------------------------------------------------------
_engine_cache: Dict[str, Engine] = {}
_sessionmaker_cache: Dict[str, sessionmaker[Session]] = {}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _current_db_path() -> Path:
    """Resolve the active DB file (env-overridable, then default)."""
    return Path(os.getenv(_DB_ENV, _DEFAULT_PATH)).expanduser()


def get_engine() -> Engine:
    """Return a cached SQLAlchemy Engine for the current DB path."""
    key = str(_current_db_path())
    if key not in _engine_cache:
        eng = create_engine(f"sqlite:///{key}", future=True, echo=False)
        Base.metadata.create_all(eng)           # create tables once
        _engine_cache[key] = eng
    return _engine_cache[key]


def _get_sessionmaker() -> sessionmaker[Session]:
    """Return (or create) a sessionmaker bound to the current engine."""
    key = str(_current_db_path())
    if key not in _sessionmaker_cache:
        _sessionmaker_cache[key] = sessionmaker(
            bind=get_engine(), autoflush=False, future=True
        )
    return _sessionmaker_cache[key]


# -----------------------------------------------------------------------------
# Public context-manager
# -----------------------------------------------------------------------------
@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional SQLAlchemy session for the current DB."""
    sm = _get_sessionmaker()
    session: Session = sm()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()
