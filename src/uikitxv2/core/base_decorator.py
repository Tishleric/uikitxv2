from __future__ import annotations

import functools
import time
from abc import ABC, abstractmethod
from typing import Callable, ParamSpec, TypeVar, cast

from .logger_protocol import LoggerProtocol

P = ParamSpec("P")
R = TypeVar("R")


class BaseDecorator(ABC):
    """Shared scaffolding for all decorators (perf, data, movement)."""

    def __init__(self, logger: LoggerProtocol) -> None:
        self._logger = logger

    @abstractmethod
    def __call__(self, fn: Callable[P, R]) -> Callable[P, R]: ...


class TimingDecorator(BaseDecorator):
    """Utility: measures wall-time and writes `duration_ms`."""

    def __call__(self, fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def _wrapped(*args: P.args, **kw: P.kwargs) -> R:  # noqa: ANN001 – generic
            t0 = time.perf_counter()
            try:
                return fn(*args, **kw)
            finally:
                delta = (time.perf_counter() - t0) * 1_000
                self._logger.write("perf", fn.__qualname__, {}, duration_ms=delta)
        return cast(Callable[P, R], _wrapped)
