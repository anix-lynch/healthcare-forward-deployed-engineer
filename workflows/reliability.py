"""Retry, timeout, and idempotency decorators for tool calls.

Titan JD signal: "retries, timeouts, checkpointing, idempotency — safe failure modes"

Usage:
    @retry(max_attempts=3, backoff="exponential")
    @idempotent(key_fn=lambda args, kwargs: kwargs.get("case_id", "anon"))
    def call_external_tool(...): ...
"""
from __future__ import annotations

import functools
import hashlib
import json
import logging
import time
from typing import Any, Callable

_log = logging.getLogger(__name__)

# In-process idempotency store — swap for Redis in multi-instance deploy
_IDEMPOTENCY_STORE: dict[str, Any] = {}


def retry(
    max_attempts: int = 3,
    backoff: str = "exponential",
    exceptions: tuple = (Exception,),
    on_retry: Callable | None = None,
):
    """Retry decorator with exponential or linear backoff.

    Args:
        max_attempts: Total attempts including first try.
        backoff: "exponential" (1s, 2s, 4s...) or "linear" (1s, 1s, 1s...).
        exceptions: Only retry on these exception types.
        on_retry: Optional callback(attempt, exc, wait_s) for observability.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        _log.error(
                            "retry_exhausted fn=%s attempts=%d exc=%s",
                            fn.__name__, max_attempts, exc,
                        )
                        raise
                    wait = (2 ** (attempt - 1)) if backoff == "exponential" else 1.0
                    _log.warning(
                        "retry fn=%s attempt=%d/%d wait=%.1fs exc=%s",
                        fn.__name__, attempt, max_attempts, wait, exc,
                    )
                    if on_retry:
                        on_retry(attempt, exc, wait)
                    time.sleep(wait)
            raise last_exc  # unreachable but satisfies type checkers
        return wrapper
    return decorator


def idempotent(key_fn: Callable[..., str] | None = None, ttl_s: int = 300):
    """Cache tool call results by idempotency key to prevent duplicate side effects.

    Args:
        key_fn: Callable(*args, **kwargs) → string key. Defaults to hash of args.
        ttl_s: Seconds before cached result expires (default 5 min).
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if key_fn:
                raw_key = key_fn(*args, **kwargs)
            else:
                raw_key = json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True)
            idem_key = f"{fn.__name__}:{hashlib.sha256(raw_key.encode()).hexdigest()[:16]}"

            entry = _IDEMPOTENCY_STORE.get(idem_key)
            if entry and (time.time() - entry["ts"]) < ttl_s:
                _log.debug("idempotency_hit key=%s fn=%s", idem_key, fn.__name__)
                return entry["result"]

            result = fn(*args, **kwargs)
            _IDEMPOTENCY_STORE[idem_key] = {"result": result, "ts": time.time()}
            return result
        return wrapper
    return decorator


def with_timeout(seconds: float):
    """Decorator that raises TimeoutError if fn exceeds wall-clock limit.

    Uses threading.Timer — safe for I/O-bound calls. Not suitable for
    CPU-bound work (use multiprocessing instead).
    """
    import threading

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result_box: list = []
            exc_box: list = []

            def target():
                try:
                    result_box.append(fn(*args, **kwargs))
                except Exception as e:
                    exc_box.append(e)

            t = threading.Thread(target=target, daemon=True)
            t.start()
            t.join(timeout=seconds)
            if t.is_alive():
                raise TimeoutError(f"{fn.__name__} exceeded {seconds}s timeout")
            if exc_box:
                raise exc_box[0]
            return result_box[0]
        return wrapper
    return decorator
