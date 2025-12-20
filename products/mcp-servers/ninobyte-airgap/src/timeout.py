"""
Timeout Enforcement Module

Provides timeout context manager with frequent check capability.

Cross-platform: Uses monotonic time checking (no signals) for portability.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


class TimeoutExpired(Exception):
    """Raised when a timeout expires."""
    pass


@dataclass
class TimeoutContext:
    """
    Timeout context for long-running operations.

    Designed for frequent checking in loops (per-file, per-line).
    Uses monotonic time for accuracy and thread safety.
    """

    timeout_seconds: float
    _start_time: float = 0.0
    _expired: bool = False

    def __post_init__(self) -> None:
        self._start_time = time.monotonic()

    def check(self) -> None:
        """
        Check if timeout has expired. Raises TimeoutExpired if so.

        Call this frequently in loops to ensure timely termination.
        """
        if self._expired:
            raise TimeoutExpired("operation timed out")

        elapsed = time.monotonic() - self._start_time
        if elapsed >= self.timeout_seconds:
            self._expired = True
            raise TimeoutExpired(f"operation timed out after {elapsed:.2f}s")

    def is_expired(self) -> bool:
        """Check if timeout has expired without raising."""
        if self._expired:
            return True

        elapsed = time.monotonic() - self._start_time
        if elapsed >= self.timeout_seconds:
            self._expired = True
            return True
        return False

    def remaining(self) -> float:
        """Get remaining time in seconds."""
        if self._expired:
            return 0.0
        elapsed = time.monotonic() - self._start_time
        remaining = self.timeout_seconds - elapsed
        return max(0.0, remaining)

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.monotonic() - self._start_time


@contextmanager
def timeout_context(timeout_seconds: float) -> Generator[TimeoutContext, None, None]:
    """
    Context manager for timeout enforcement.

    Usage:
        with timeout_context(30.0) as ctx:
            for item in items:
                ctx.check()  # Raises TimeoutExpired if expired
                process(item)
    """
    ctx = TimeoutContext(timeout_seconds=timeout_seconds)
    yield ctx
