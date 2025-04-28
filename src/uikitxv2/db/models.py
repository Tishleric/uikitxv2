from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ------------------------------------------------------------------ Base
class Base(DeclarativeBase): 
    """Declarative base class."""
    pass


# ------------------------------------------------------------------ TraceLog
class TraceLog(Base):
    """Unified table for all decorator events."""

    __tablename__ = "trace_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    log_type: Mapped[str] = mapped_column(String(8))          # 'perf' | 'data' | 'move'
    name: Mapped[str] = mapped_column(String(255))
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(
    MutableDict.as_mutable(SQLiteJSON), default=dict
)