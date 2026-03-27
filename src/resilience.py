"""Resilience utilities — circuit breaker, retry, and input validation.

Provides:
- CircuitBreaker: trips after N failures, serves cached/fallback data while open.
- retry_with_backoff: exponential backoff wrapper for external API calls.
- VALID_ASSETS: whitelist for input validation.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.logging import get_logger

log = get_logger()

# Asset whitelist — reject anything not on this list
VALID_ASSETS: set[str] = {
    "XAUUSD", "gold", "XAGUSD", "silver",
    "CL1", "oil",
    "DXY",
    "SPX", "NDX",
    "TLT",
    "BTC",
    "EUR", "GBP", "JPY", "CNY",
}

VALID_HORIZONS: set[str] = {"7d", "14d", "30d", "60d", "90d", "180d", "1y"}


def validate_asset(asset: str) -> str | None:
    """Validate an asset symbol. Returns error message or None."""
    if asset not in VALID_ASSETS:
        return f"Unknown asset '{asset}'. Valid: {sorted(VALID_ASSETS)}"
    return None


def validate_horizon(horizon: str) -> str | None:
    """Validate a horizon string. Returns error message or None."""
    if horizon not in VALID_HORIZONS:
        return f"Invalid horizon '{horizon}'. Valid: {sorted(VALID_HORIZONS)}"
    return None


@dataclass
class CircuitBreaker:
    """Circuit breaker for external service calls.

    States:
        closed  — normal operation, calls go through
        open    — too many failures, calls are rejected / return fallback
        half_open — after recovery_timeout, allow one probe call
    """

    name: str
    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds

    _failure_count: int = field(default=0, init=False, repr=False)
    _last_failure_time: float = field(default=0.0, init=False, repr=False)
    _state: str = field(default="closed", init=False)

    @property
    def state(self) -> str:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time > self.recovery_timeout:
                self._state = "half_open"
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            log.warning(
                "circuit_breaker_opened",
                breaker=self.name,
                failures=self._failure_count,
            )

    def is_open(self) -> bool:
        return self.state == "open"


# Global circuit breakers for each data source
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name)
    return _breakers[name]


async def retry_with_backoff(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 2,
    base_delay: float = 1.0,
    breaker_name: str | None = None,
    **kwargs: Any,
) -> Any:
    """Call fn with exponential backoff and optional circuit breaker.

    Args:
        fn: The function to call (sync or async).
        max_retries: Maximum retry attempts.
        base_delay: Initial delay in seconds (doubles each retry).
        breaker_name: If set, checks/updates the named circuit breaker.
    """
    breaker = get_breaker(breaker_name) if breaker_name else None

    if breaker and breaker.is_open():
        log.warning("circuit_breaker_rejected", breaker=breaker_name)
        raise RuntimeError(f"Circuit breaker '{breaker_name}' is open — service unavailable")

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)

            if breaker:
                breaker.record_success()
            return result

        except Exception as e:
            last_error = e
            if breaker:
                breaker.record_failure()

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                log.warning(
                    "retry_attempt",
                    function=fn.__name__,
                    attempt=attempt + 1,
                    delay=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)

    raise last_error  # type: ignore[misc]


@dataclass
class TokenUsage:
    """Track token consumption for a single run."""

    run_id: str
    agent_tokens: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, agent_id: str, phase: str, prompt_tokens: int, completion_tokens: int) -> None:
        key = f"{agent_id}:{phase}"
        self.agent_tokens[key] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    @property
    def total_tokens(self) -> int:
        return sum(v["total_tokens"] for v in self.agent_tokens.values())

    @property
    def estimated_cost_usd(self) -> float:
        """Rough cost estimate for GPT-4.1 pricing ($2/1M input, $8/1M output)."""
        prompt = sum(v["prompt_tokens"] for v in self.agent_tokens.values())
        completion = sum(v["completion_tokens"] for v in self.agent_tokens.values())
        return (prompt * 2 + completion * 8) / 1_000_000

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "per_agent": self.agent_tokens,
        }
