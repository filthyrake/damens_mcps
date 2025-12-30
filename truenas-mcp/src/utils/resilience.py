"""
Resilience utilities for retry logic and circuit breaker patterns.

This module provides decorators and utilities for implementing retry logic
with exponential backoff and circuit breaker patterns to handle transient
failures and prevent cascading failures.

Also includes TTL-based caching for static data like version/system info
that rarely changes (Issue #173).
"""

import asyncio
import functools
import time
from typing import Any, Callable, Generic, Optional, Type, Tuple, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryCallState,
    before_sleep_log,
    after_log
)
import pybreaker

try:
    from .logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# Type variable for generic caching
T = TypeVar('T')


class CachedResponse(Generic[T]):
    """
    TTL-based cache for API responses.
    
    Useful for caching static data like version/system info that rarely changes.
    This reduces unnecessary API calls and improves performance.
    
    Example usage:
        # In client __init__:
        self._version_cache: Optional[CachedResponse[Dict[str, Any]]] = None
        
        # In get_version method:
        if self._version_cache and self._version_cache.is_valid():
            return self._version_cache.data
        
        result = await self._make_request("GET", "system/version")
        self._version_cache = CachedResponse(result, ttl_seconds=300)
        return result
    
    Attributes:
        data: The cached data
        ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        created_at: Timestamp when cache was created
    """
    
    def __init__(self, data: T, ttl_seconds: int = 300):
        """
        Initialize cached response.
        
        Args:
            data: Data to cache
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.data = data
        self.ttl_seconds = ttl_seconds
        self.created_at = time.time()
    
    def is_valid(self) -> bool:
        """
        Check if cache is still valid (not expired).
        
        Returns:
            True if cache is valid, False if expired
        """
        return (time.time() - self.created_at) < self.ttl_seconds
    
    def time_remaining(self) -> float:
        """
        Get remaining time before cache expires.
        
        Returns:
            Remaining seconds, or 0 if expired
        """
        remaining = self.ttl_seconds - (time.time() - self.created_at)
        return max(0.0, remaining)
    
    def invalidate(self) -> None:
        """
        Manually invalidate the cache.
        
        Useful when you know the underlying data has changed
        (e.g., after a system update/reboot).
        """
        self.created_at = 0  # Set to epoch to make is_valid() return False


# Default cache TTL for static data (5 minutes)
DEFAULT_CACHE_TTL_SECONDS = 300


# Default retry configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_MIN_WAIT = 1.0  # seconds
DEFAULT_RETRY_MAX_WAIT = 10.0  # seconds
DEFAULT_RETRY_MULTIPLIER = 1.0  # exponential backoff multiplier

# Default circuit breaker configuration
DEFAULT_CIRCUIT_BREAKER_FAILURES = 5
DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 60  # seconds


def create_retry_decorator(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_RETRY_MIN_WAIT,
    max_wait: float = DEFAULT_RETRY_MAX_WAIT,
    multiplier: float = DEFAULT_RETRY_MULTIPLIER,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None
) -> Callable:
    """
    Create a retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Exponential backoff multiplier
        retry_exceptions: Tuple of exception types to retry on
        
    Returns:
        Retry decorator
    """
    if retry_exceptions is None:
        # Default exceptions to retry on
        import aiohttp
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            aiohttp.ClientError,
            aiohttp.ServerTimeoutError,
            aiohttp.ClientConnectorError,
        )
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        before_sleep=before_sleep_log(logger, logger.level),
        after=after_log(logger, logger.level),
        reraise=True
    )


def _normalize_exception_types(exceptions):
    """
    Normalize exception types to a tuple for isinstance() checking.
    
    Args:
        exceptions: Exception type(s) - can be None, single type, list, or tuple
        
    Returns:
        Tuple of exception types, or None if input is None/empty
    """
    if not exceptions:
        return None
    if isinstance(exceptions, list):
        return tuple(exceptions)
    elif not isinstance(exceptions, tuple):
        return (exceptions,)
    return exceptions


def create_circuit_breaker(
    fail_max: int = DEFAULT_CIRCUIT_BREAKER_FAILURES,
    timeout_duration: int = DEFAULT_CIRCUIT_BREAKER_TIMEOUT,
    exclude: Optional[Tuple[Type[Exception], ...]] = None,
    name: Optional[str] = None
) -> pybreaker.CircuitBreaker:
    """
    Create a circuit breaker.
    
    Args:
        fail_max: Number of failures before opening circuit
        timeout_duration: Timeout duration in seconds before attempting to close circuit
        exclude: Tuple of exception types to exclude from circuit breaker
        name: Optional name for the circuit breaker
        
    Returns:
        Circuit breaker instance
    """
    if exclude is None:
        # Don't count validation errors as circuit breaker failures
        exclude = (ValueError, TypeError)
    
    # Create listeners for logging
    def on_open(breaker: pybreaker.CircuitBreaker, *args, **kwargs):
        """Called when circuit opens."""
        logger.warning(f"Circuit breaker '{breaker.name}' opened after {breaker.fail_counter} failures")
    
    def on_close(breaker: pybreaker.CircuitBreaker, *args, **kwargs):
        """Called when circuit closes."""
        logger.info(f"Circuit breaker '{breaker.name}' closed")
    
    def on_half_open(breaker: pybreaker.CircuitBreaker, *args, **kwargs):
        """Called when circuit moves to half-open state."""
        logger.info(f"Circuit breaker '{breaker.name}' half-open, testing connection")
    
    breaker = pybreaker.CircuitBreaker(
        fail_max=fail_max,
        reset_timeout=timeout_duration,
        exclude=exclude,
        name=name or "default"
    )
    
    # Add listeners
    breaker.add_listener(on_open)
    breaker.add_listener(on_close)
    breaker.add_listener(on_half_open)
    
    return breaker


async def call_with_circuit_breaker_async(
    breaker: pybreaker.CircuitBreaker,
    func: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Call an async function with circuit breaker protection.
    
    This is a public wrapper since pybreaker's call_async has compatibility issues.
    Use this function to manually apply circuit breaker protection to async functions.
    
    Args:
        breaker: CircuitBreaker instance
        func: Async function to call
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result from the async function
        
    Raises:
        CircuitBreakerError: If circuit is open
        Exception: Any exception raised by func
    """
    if breaker.current_state == 'open':
        # Circuit is open, raise error immediately
        raise pybreaker.CircuitBreakerError(breaker)
    
    try:
        result = await func(*args, **kwargs)
        # Success - notify the breaker (it will close if in half-open state)
        # NOTE: Direct access to _lock and _state is required due to pybreaker's
        # incomplete async support. The call_async method has compatibility issues
        # with modern asyncio. Tested with pybreaker>=1.0.0,<2.0.0.
        try:
            with breaker._lock:
                breaker._state.on_success()
        except AttributeError as attr_err:
            logger.warning(f"pybreaker internal API changed: {attr_err}. Circuit breaker state update failed.")
        return result
    except Exception as e:
        # Check if exception should be excluded
        excluded = _normalize_exception_types(breaker._excluded_exceptions)
        if excluded and isinstance(e, excluded):
            raise
        # Failure - notify the breaker
        # NOTE: Direct access to _lock and _state is required due to pybreaker's
        # incomplete async support. Tested with pybreaker>=1.0.0,<2.0.0.
        try:
            with breaker._lock:
                breaker._state.on_failure(e)
        except AttributeError as attr_err:
            logger.warning(f"pybreaker internal API changed: {attr_err}. Circuit breaker state update failed.")
        raise


def retry_with_circuit_breaker(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_RETRY_MIN_WAIT,
    max_wait: float = DEFAULT_RETRY_MAX_WAIT,
    multiplier: float = DEFAULT_RETRY_MULTIPLIER,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    circuit_breaker: Optional[pybreaker.CircuitBreaker] = None,
    circuit_fail_max: int = DEFAULT_CIRCUIT_BREAKER_FAILURES,
    circuit_timeout: int = DEFAULT_CIRCUIT_BREAKER_TIMEOUT,
    circuit_exclude: Optional[Tuple[Type[Exception], ...]] = None,
    circuit_name: Optional[str] = None
) -> Callable:
    """
    Create a decorator that combines retry logic with circuit breaker.
    
    This decorator first wraps the function with retry logic, then applies
    a circuit breaker on top. This ensures retries happen before the circuit
    breaker is triggered.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Exponential backoff multiplier
        retry_exceptions: Tuple of exception types to retry on
        circuit_breaker: Existing circuit breaker instance (optional)
        circuit_fail_max: Number of failures before opening circuit
        circuit_timeout: Timeout duration in seconds before attempting to close circuit
        circuit_exclude: Tuple of exception types to exclude from circuit breaker
        circuit_name: Optional name for the circuit breaker
        
    Returns:
        Combined decorator function
    """
    # Create retry decorator
    retry_decorator = create_retry_decorator(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        multiplier=multiplier,
        retry_exceptions=retry_exceptions
    )
    
    # Create or use provided circuit breaker
    if circuit_breaker is None:
        circuit_breaker = create_circuit_breaker(
            fail_max=circuit_fail_max,
            timeout_duration=circuit_timeout,
            exclude=circuit_exclude,
            name=circuit_name
        )
    
    def decorator(func: Callable) -> Callable:
        """Decorator that combines retry and circuit breaker."""
        # First apply retry decorator
        retried_func = retry_decorator(func)
        
        # Then apply circuit breaker
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await call_with_circuit_breaker_async(
                    circuit_breaker, retried_func, *args, **kwargs
                )
            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return circuit_breaker.call(retried_func, *args, **kwargs)
            return wrapper
    
    return decorator


def get_retry_metrics(retry_state: RetryCallState) -> dict:
    """
    Extract metrics from a retry state.
    
    Args:
        retry_state: Retry call state
        
    Returns:
        Dictionary containing retry metrics
    """
    return {
        "attempt_number": retry_state.attempt_number,
        "outcome": str(retry_state.outcome),
        "next_action": str(retry_state.next_action),
        "idle_for": retry_state.idle_for,
        "seconds_since_start": retry_state.seconds_since_start
    }


def get_circuit_breaker_metrics(breaker: pybreaker.CircuitBreaker) -> dict:
    """
    Get current metrics from a circuit breaker.
    
    Args:
        breaker: Circuit breaker instance
        
    Returns:
        Dictionary containing circuit breaker metrics
    """
    return {
        "name": breaker.name,
        "state": breaker.current_state,
        "fail_counter": breaker.fail_counter,
        "success_counter": breaker._success_counter if hasattr(breaker, '_success_counter') else 0,
        "last_failure": str(breaker._last_failure) if hasattr(breaker, '_last_failure') else None,
        "opened_at": str(breaker._opened_at) if hasattr(breaker, '_opened_at') else None,
    }
