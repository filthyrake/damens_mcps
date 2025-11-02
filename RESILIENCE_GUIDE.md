# Resilience and Fault Tolerance Guide

This guide explains the retry logic and circuit breaker patterns implemented across all MCP servers to handle transient failures and prevent cascading failures.

## Overview

All MCP servers (pfSense, TrueNAS, iDRAC, Proxmox) now implement:

1. **Retry Logic with Exponential Backoff**: Automatically retries transient failures
2. **Circuit Breaker Pattern**: Prevents cascading failures by fail-fast behavior
3. **Timeout Configuration**: Configurable request timeouts
4. **Connection Pooling**: Optimized connection management (async clients)

## Features

### Retry Logic

Automatically retries failed requests with exponential backoff:

- **Max Attempts**: Configurable number of retry attempts (default: 3)
- **Exponential Backoff**: Wait time doubles between retries
- **Min/Max Wait**: Configurable wait times (default: 1-10 seconds)
- **Selective Retry**: Only retries transient failures (connection errors, timeouts)
- **No Retry on Validation**: Validation errors fail immediately

**Retried Exceptions:**
- `ConnectionError`
- `TimeoutError`
- `aiohttp.ClientError` (async clients)
- `aiohttp.ServerTimeoutError` (async clients)
- `aiohttp.ClientConnectorError` (async clients)
- `requests.exceptions.ConnectionError` (sync clients)
- `requests.exceptions.Timeout` (sync clients)

### Circuit Breaker

Protects against cascading failures by opening the circuit after repeated failures:

- **Failure Threshold**: Opens circuit after N failures (default: 5)
- **Reset Timeout**: Attempts to close after N seconds (default: 60)
- **Excluded Errors**: Validation errors don't count as failures
- **State Logging**: Logs state transitions (closed → open → half-open → closed)
- **Per-Client**: Each client has its own circuit breaker

**Circuit States:**
1. **Closed**: Normal operation, requests pass through
2. **Open**: Circuit is open, requests fail immediately
3. **Half-Open**: Testing if service recovered, one request allowed

### Connection Management

**Async Clients (pfSense, TrueNAS, iDRAC):**
- Connection pooling (100 total connections, 30 per host)
- DNS caching (300 second TTL)
- Configurable timeouts

**Sync Clients (Proxmox):**
- Session reuse
- Configurable timeouts

## Configuration

All resilience features are configurable per client. Default values provide good protection with minimal overhead.

### pfSense Configuration

```python
from src.pfsense_client import HTTPPfSenseClient

config = {
    "host": "192.168.1.1",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",
    
    # Retry configuration
    "retry_max_attempts": 3,
    "retry_min_wait": 1,      # seconds
    "retry_max_wait": 10,     # seconds
    
    # Circuit breaker configuration
    "circuit_breaker_enabled": True,
    "circuit_breaker_fail_max": 5,
    "circuit_breaker_timeout": 60,  # seconds
    
    # Timeout and connection pooling
    "timeout": 30,            # seconds
    "connector_limit": 100,   # total connections
    "connector_limit_per_host": 30,
}

client = HTTPPfSenseClient(config)
```

### TrueNAS Configuration

```python
from src.truenas_client import TrueNASClient
from src.auth import AuthManager

config = {
    "host": "truenas.local",
    "api_key": "your-api-key",
    
    # Retry configuration
    "retry_max_attempts": 3,
    "retry_min_wait": 1,
    "retry_max_wait": 10,
    
    # Circuit breaker configuration
    "circuit_breaker_enabled": True,
    "circuit_breaker_fail_max": 5,
    "circuit_breaker_timeout": 60,
    
    # Timeout and connection pooling
    "timeout": 30,
    "connector_limit": 100,
    "connector_limit_per_host": 30,
}

auth_manager = AuthManager(config)
client = TrueNASClient(config, auth_manager)
```

### iDRAC Configuration

```python
from src.idrac_client import IDracClient

config = {
    "host": "idrac.server.local",
    "port": 443,
    "protocol": "https",
    "username": "root",
    "password": "password",
    "ssl_verify": False,
    
    # Retry configuration
    "retry_max_attempts": 3,
    "retry_min_wait": 1,
    "retry_max_wait": 10,
    
    # Circuit breaker configuration
    "circuit_breaker_enabled": True,
    "circuit_breaker_fail_max": 5,
    "circuit_breaker_timeout": 60,
    
    # Timeout and connection pooling
    "timeout": 30,
    "connector_limit": 100,
    "connector_limit_per_host": 30,
}

client = IDracClient(config)
```

### Proxmox Configuration

```python
from src.proxmox_client import ProxmoxClient

# Proxmox client uses fixed defaults (not Pydantic config)
# Defaults are: timeout=30, retry_attempts=3, circuit_fail_max=5

client = ProxmoxClient(
    host="proxmox.local",
    port=8006,
    protocol="https",
    username="root",
    password="password",
    ssl_verify=False
)
```

## Configuration Parameters

### Retry Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retry_max_attempts` | int | 3 | Maximum number of retry attempts |
| `retry_min_wait` | int | 1 | Minimum wait between retries (seconds) |
| `retry_max_wait` | int | 10 | Maximum wait between retries (seconds) |

**Exponential Backoff Formula:** `wait = min(retry_max_wait, max(retry_min_wait, multiplier * 2^attempt))`

where `multiplier` defaults to 1. The min/max constraints are applied after the exponential calculation.

### Circuit Breaker Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `circuit_breaker_enabled` | bool | True | Enable/disable circuit breaker |
| `circuit_breaker_fail_max` | int | 5 | Failures before opening circuit |
| `circuit_breaker_timeout` | int | 60 | Timeout before attempting to close (seconds) |

### Connection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | int | 30 | Request timeout (seconds) |
| `connector_limit` | int | 100 | Total connection pool size (async only) |
| `connector_limit_per_host` | int | 30 | Per-host connection limit (async only) |

## Monitoring

### Logging

All retry attempts and circuit breaker state changes are logged:

```python
# Retry attempt log
WARNING: Retry attempt 2/3 failed: Connection error, retrying in 2s...

# Circuit breaker logs
WARNING: Circuit breaker 'pfsense_api' opened after 5 failures
INFO: Circuit breaker 'pfsense_api' half-open, testing connection
INFO: Circuit breaker 'pfsense_api' closed
```

### Metrics

Get circuit breaker metrics programmatically:

```python
from src.utils.resilience import get_circuit_breaker_metrics

# Get metrics from client's circuit breaker
metrics = get_circuit_breaker_metrics(client.circuit_breaker)
print(metrics)
# {
#     "name": "pfsense_api",
#     "state": "closed",
#     "fail_counter": 2,
#     "success_counter": 10,
#     "last_failure": "2024-01-01 12:00:00",
#     "opened_at": None
# }
```

## Best Practices

### 1. Use Default Values for Production

The default values provide good protection:
- 3 retry attempts with exponential backoff
- Circuit opens after 5 failures
- 30 second timeout

### 2. Adjust for Specific Use Cases

**High-latency networks:**
```python
config = {
    "timeout": 60,  # Increase timeout
    "retry_max_wait": 30,  # Longer max wait
}
```

**Critical operations:**
```python
config = {
    "retry_max_attempts": 5,  # More retries
    "circuit_breaker_fail_max": 10,  # More lenient
}
```

**Development/testing:**
```python
config = {
    "circuit_breaker_enabled": False,  # Disable for testing
    "retry_max_attempts": 1,  # Fail fast
}
```

### 3. Monitor Circuit Breaker State

Check circuit breaker state before critical operations:

```python
if client.circuit_breaker and client.circuit_breaker.current_state == 'open':
    logger.warning("Circuit breaker is open, waiting for recovery")
    # Handle gracefully (e.g., use cached data, notify user)
```

### 4. Handle Circuit Breaker Errors

```python
import pybreaker

try:
    result = await client.get_system_info()
except pybreaker.CircuitBreakerError as e:
    logger.error(f"Circuit breaker is open: {e}")
    # Provide fallback or degraded service
```

## Implementation Details

### Retry Decorator

Uses the `tenacity` library for robust retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(ConnectionError)
)
async def make_api_call():
    # Your API call here
    pass
```

### Circuit Breaker

Uses the `pybreaker` library with custom async wrapper:

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=(ValueError, TypeError)
)

# Our custom async wrapper
result = await _call_with_circuit_breaker_async(
    breaker, your_function, *args, **kwargs
)
```

## Testing

Test files are available for validation:
- `pfsense-mcp/tests/test_resilience.py`
- `truenas-mcp/tests/test_resilience.py`

Run tests:
```bash
cd pfsense-mcp
pytest tests/test_resilience.py -v
```

## Security Considerations

1. **Timeout Protection**: Prevents indefinite waits
2. **Resource Protection**: Circuit breaker prevents resource exhaustion
3. **Validation Errors**: Not retried, prevent brute force
4. **Logging**: All failures logged for security monitoring

## Troubleshooting

### Issue: Too Many Retries

**Symptom:** Requests take too long to fail

**Solution:** Reduce max attempts or adjust wait times
```python
config = {
    "retry_max_attempts": 2,
    "retry_max_wait": 5,
}
```

### Issue: Circuit Opens Too Quickly

**Symptom:** Circuit breaker opens during temporary glitches

**Solution:** Increase failure threshold
```python
config = {
    "circuit_breaker_fail_max": 10,
}
```

### Issue: Circuit Stays Open Too Long

**Symptom:** Service recovered but circuit still open

**Solution:** Reduce reset timeout
```python
config = {
    "circuit_breaker_timeout": 30,
}
```

## Performance Impact

The resilience features have minimal performance impact:

- **Retry Logic**: Only activates on failure (no overhead on success)
- **Circuit Breaker**: Minimal state checking (< 1ms overhead)
- **Connection Pooling**: Improves performance by reusing connections

**Benchmarks:**
- Success path: < 1% overhead
- Failure path: Adds retry delays (expected)
- Circuit open: Fails immediately (faster than timeout)

## References

- [Tenacity Documentation](https://tenacity.readthedocs.io/)
- [PyBreaker Documentation](https://github.com/danielfm/pybreaker)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
