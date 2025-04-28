from __future__ import annotations

import os
import uuid
from contextvars import ContextVar
from typing import Callable

# env-var switches
_ENABLED = os.getenv("UIKITX_TRACE_ENABLED", "1") != "0"
_SAMPLE = float(os.getenv("UIKITX_TRACE_SAMPLE", "1"))
_PROCESS_UUID = uuid.uuid4().hex

def _default_session_factory() -> str:
    return _PROCESS_UUID

_session_factory: Callable[[], str] = _default_session_factory

_current_session: ContextVar[str] = ContextVar("session_id", default=_PROCESS_UUID)

def get_session_id() -> str:
    return _current_session.get()

def set_session_factory(factory: Callable[[], str]) -> None:
    global _session_factory
    _session_factory = factory

def new_session() -> str:
    sid = _session_factory()
    _current_session.set(sid)
    return sid

def is_enabled() -> bool:
    return _ENABLED
