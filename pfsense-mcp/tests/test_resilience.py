"""Tests for resilience utilities (retry logic and circuit breaker)."""

import pytest
import aiohttp

from src.utils.resilience import (
    create_retry_decorator,
    create_circuit_breaker,
    retry_with_circuit_breaker,
    get_circuit_breaker_metrics,
    call_with_circuit_breaker_async,
)


class TestRetryDecorator:
    """Tests for retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Test that retry decorator retries on transient failures."""
        # Create a mock function that fails twice then succeeds
        call_count = 0
        
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise aiohttp.ClientError("Transient failure")
            return {"success": True}
        
        # Apply retry decorator
        retry_decorator = create_retry_decorator(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.5,
            retry_exceptions=(aiohttp.ClientError,)
        )
        retried_function = retry_decorator(flaky_function)
        
        # Should succeed after 3 attempts
        result = await retried_function()
        assert result == {"success": True}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_gives_up_after_max_attempts(self):
        """Test that retry decorator gives up after max attempts."""
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise aiohttp.ClientError("Permanent failure")
        
        # Apply retry decorator with 2 max attempts
        retry_decorator = create_retry_decorator(
            max_attempts=2,
            min_wait=0.1,
            max_wait=0.5,
            retry_exceptions=(aiohttp.ClientError,)
        )
        retried_function = retry_decorator(always_fails)
        
        # Should fail after 2 attempts
        with pytest.raises(aiohttp.ClientError):
            await retried_function()
        
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_does_not_retry_on_non_transient_error(self):
        """Test that retry decorator does not retry on non-transient errors."""
        call_count = 0
        
        async def validation_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Validation error")
        
        # Apply retry decorator (ValueError not in retry_exceptions)
        retry_decorator = create_retry_decorator(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.5,
            retry_exceptions=(aiohttp.ClientError,)
        )
        retried_function = retry_decorator(validation_error)
        
        # Should fail immediately without retry
        with pytest.raises(ValueError):
            await retried_function()
        
        assert call_count == 1


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after reaching failure threshold."""
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise aiohttp.ClientError("Failure")
        
        # Create circuit breaker with fail_max=3
        breaker = create_circuit_breaker(
            fail_max=3,
            timeout_duration=60,
            name="test_breaker"
        )
        
        # First 3 calls should fail and be counted
        for i in range(3):
            with pytest.raises(aiohttp.ClientError):
                await call_with_circuit_breaker_async(breaker, always_fails)
        
        assert call_count == 3
        
        # Circuit should now be open, 4th call should fail immediately
        # without calling the function
        import pybreaker
        call_count_before = call_count
        with pytest.raises(pybreaker.CircuitBreakerError):
            await call_with_circuit_breaker_async(breaker, always_fails)
        
        # Function was not called during the 4th attempt
        assert call_count == call_count_before

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_on_success(self):
        """Test that circuit breaker closes after successful calls."""
        call_count = 0
        
        async def succeeds():
            nonlocal call_count
            call_count += 1
            return {"success": True}
        
        # Create circuit breaker
        breaker = create_circuit_breaker(
            fail_max=5,
            timeout_duration=60,
            name="test_breaker"
        )
        
        # Successful calls should keep circuit closed
        for i in range(5):
            result = await call_with_circuit_breaker_async(breaker, succeeds)
            assert result == {"success": True}
        
        assert call_count == 5
        
        # Get metrics
        metrics = get_circuit_breaker_metrics(breaker)
        assert metrics["fail_counter"] == 0
        assert metrics["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_excludes_validation_errors(self):
        """Test that circuit breaker excludes validation errors from failure count."""
        call_count = 0
        
        async def validation_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Validation error")
        
        # Create circuit breaker with ValueError excluded
        breaker = create_circuit_breaker(
            fail_max=3,
            timeout_duration=60,
            exclude=(ValueError,),
            name="test_breaker"
        )
        
        # Multiple ValueError failures should not open circuit
        for i in range(5):
            with pytest.raises(ValueError):
                await call_with_circuit_breaker_async(breaker, validation_fails)
        
        assert call_count == 5
        
        # Get metrics - circuit should still be closed
        metrics = get_circuit_breaker_metrics(breaker)
        assert metrics["state"] == "closed"


class TestCombinedRetryAndCircuitBreaker:
    """Tests for combined retry and circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_retry_then_circuit_breaker(self):
        """Test that retry happens before circuit breaker is triggered."""
        call_count = 0
        
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            # Fail first 2 times, succeed on 3rd
            if call_count < 3:
                raise aiohttp.ClientError("Transient failure")
            return {"success": True}
        
        # Create combined decorator
        decorator = retry_with_circuit_breaker(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.5,
            circuit_fail_max=5,
            circuit_timeout=60,
            circuit_name="test_combined"
        )
        
        wrapped_function = decorator(flaky_function)
        
        # Should succeed after retries
        result = await wrapped_function()
        assert result == {"success": True}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_retries_when_open(self):
        """Test that circuit breaker prevents retries when open."""
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise aiohttp.ClientError("Failure")
        
        # Create circuit breaker
        breaker = create_circuit_breaker(
            fail_max=2,
            timeout_duration=60,
            name="test_breaker"
        )
        
        # Create retry decorator
        retry_decorator = create_retry_decorator(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.5,
            retry_exceptions=(aiohttp.ClientError,)
        )
        
        # Apply retry first, then circuit breaker
        retried_function = retry_decorator(always_fails)
        
        # First call: retries 3 times (call_count = 3)
        with pytest.raises(aiohttp.ClientError):
            await call_with_circuit_breaker_async(breaker, retried_function)
        assert call_count == 3
        
        # Second call: retries 3 times (call_count = 6)
        with pytest.raises(aiohttp.ClientError):
            await call_with_circuit_breaker_async(breaker, retried_function)
        assert call_count == 6
        
        # Circuit should now be open
        # Third call should fail immediately without calling function
        import pybreaker
        with pytest.raises(pybreaker.CircuitBreakerError):
            await call_with_circuit_breaker_async(breaker, retried_function)
        
        # Function was not called (still 6)
        assert call_count == 6
