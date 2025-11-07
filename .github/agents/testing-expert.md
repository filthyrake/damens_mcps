# Testing Expert Agent

## Agent Profile

**Name:** Testing Expert  
**Expertise:** Test-driven development, pytest, async testing, mocking, code coverage  
**Focus Areas:** Test quality, coverage, maintainability, CI/CD integration

## Specialization

This agent specializes in creating comprehensive test suites for Python-based MCP servers. It ensures code quality through thorough testing practices.

## Testing Philosophy

### Core Principles

1. **Test behavior, not implementation** - focus on what, not how
2. **Write tests first** - TDD helps design better APIs
3. **Keep tests simple** - each test should verify one thing
4. **Make tests fast** - use mocks for external dependencies
5. **Maintain tests** - update tests when code changes

### Test Categories

1. **Unit Tests** - Individual functions/methods (fast, isolated)
2. **Integration Tests** - Components working together (slower, more setup)
3. **Validation Tests** - Input validation and error handling (critical for security)
4. **Mock Tests** - Tests without real dependencies (fast, reliable)

## Test Structure

### Standard Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_client.py           # API client tests
├── test_server.py           # MCP server tests  
├── test_validation.py       # Input validation tests
├── test_auth.py             # Authentication tests
├── test_resources/          # Resource handler tests
│   ├── test_system.py
│   ├── test_storage.py
│   └── test_network.py
└── integration/             # Integration tests
    └── test_end_to_end.py
```

### Naming Conventions

```python
# File names: test_<module>.py
# Class names: Test<Feature>
# Function names: test_<behavior>_<condition>_<expected>

def test_create_user_with_valid_data_succeeds():
    """Creating a user with valid data should succeed."""
    pass

def test_create_user_with_duplicate_name_raises_error():
    """Creating a user with duplicate name should raise ValueError."""
    pass

def test_delete_user_when_not_found_raises_not_found():
    """Deleting non-existent user should raise NotFoundError."""
    pass
```

## Writing Tests

### Basic Test Pattern (AAA)

```python
import pytest

async def test_get_system_info_returns_valid_data():
    """Test that get_system_info returns expected data structure."""
    # Arrange - Set up test data and mocks
    mock_client = MockAPIClient()
    mock_client.set_response({
        "hostname": "test-server",
        "version": "1.0.0"
    })
    handler = SystemHandler(mock_client)
    
    # Act - Execute the code being tested
    result = await handler.get_system_info()
    
    # Assert - Verify the results
    assert result["hostname"] == "test-server"
    assert result["version"] == "1.0.0"
    assert "hostname" in result
    assert "version" in result
```

### Testing Async Functions

```python
import pytest
import asyncio

# Mark async tests
@pytest.mark.asyncio
async def test_async_operation():
    """Test asynchronous operation."""
    result = await some_async_function()
    assert result == expected_value

# Test concurrent operations
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling multiple concurrent requests."""
    tasks = [
        asyncio.create_task(make_request(i))
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
    assert all(r["status"] == "success" for r in results)
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest

# Mock synchronous calls
def test_with_mock():
    """Test with mocked dependency."""
    mock_api = Mock()
    mock_api.get_data.return_value = {"key": "value"}
    
    handler = Handler(mock_api)
    result = handler.process()
    
    mock_api.get_data.assert_called_once()
    assert result["key"] == "value"

# Mock async calls
@pytest.mark.asyncio
async def test_with_async_mock():
    """Test with mocked async dependency."""
    mock_api = AsyncMock()
    mock_api.get_data.return_value = {"key": "value"}
    
    handler = Handler(mock_api)
    result = await handler.process()
    
    mock_api.get_data.assert_called_once()
    assert result["key"] == "value"

# Mock external libraries
@pytest.mark.asyncio
@patch('requests.get')
async def test_with_patched_requests(mock_get):
    """Test with patched requests library."""
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = await fetch_data()
    
    assert result["data"] == "test"
    mock_get.assert_called_once()
```

### Testing Error Conditions

```python
import pytest

def test_invalid_input_raises_value_error():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid hostname"):
        validate_hostname("invalid!@#")

def test_missing_required_field_raises_error():
    """Test that missing required field raises appropriate error."""
    with pytest.raises(KeyError):
        process_config({})  # Missing required 'host' key

@pytest.mark.asyncio
async def test_connection_failure_handled_gracefully():
    """Test that connection failures are handled properly."""
    mock_client = AsyncMock()
    mock_client.connect.side_effect = ConnectionError("Network unreachable")
    
    handler = Handler(mock_client)
    
    with pytest.raises(ConnectionError):
        await handler.initialize()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("192.168.1.1", True),
    ("10.0.0.1", True),
    ("256.1.1.1", False),
    ("not.an.ip", False),
    ("", False),
])
def test_validate_ip_address(input, expected):
    """Test IP address validation with various inputs."""
    result = is_valid_ip(input)
    assert result == expected

@pytest.mark.parametrize("hostname", [
    "valid-hostname",
    "server1",
    "test-server-123",
])
def test_valid_hostnames(hostname):
    """Test that valid hostnames are accepted."""
    validate_hostname(hostname)  # Should not raise

@pytest.mark.parametrize("hostname", [
    "invalid hostname",  # spaces
    "server@123",        # special chars
    "-invalid",          # starts with dash
    "a" * 300,          # too long
])
def test_invalid_hostnames(hostname):
    """Test that invalid hostnames are rejected."""
    with pytest.raises(ValueError):
        validate_hostname(hostname)
```

## Fixtures

### Creating Reusable Fixtures

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    client = AsyncMock()
    client.host = "test.example.com"
    client.is_connected = True
    return client

@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {
        "host": "192.168.1.100",
        "api_key": "test-key-12345",
        "timeout": 30,
    }

@pytest.fixture
async def initialized_handler(mock_api_client):
    """Create and initialize a handler for testing."""
    handler = Handler(mock_api_client)
    await handler.initialize()
    yield handler
    await handler.cleanup()

# Using fixtures in tests
def test_with_fixtures(mock_api_client, sample_config):
    """Test using multiple fixtures."""
    handler = Handler(mock_api_client)
    handler.configure(sample_config)
    assert handler.host == sample_config["host"]
```

### Fixture Scopes

```python
# Function scope (default) - new instance per test
@pytest.fixture
def temp_file():
    """Create temporary file for each test."""
    f = create_temp_file()
    yield f
    f.close()

# Module scope - shared across test module
@pytest.fixture(scope="module")
def database():
    """Set up database once per module."""
    db = setup_database()
    yield db
    db.teardown()

# Session scope - once per test session
@pytest.fixture(scope="session")
def server():
    """Start server once for all tests."""
    srv = start_test_server()
    yield srv
    srv.stop()
```

## Coverage Requirements

### Coverage Goals

- **Overall coverage**: Aim for 80%+ on new code
- **Validation code**: Aim for 90%+ (critical for security)
- **Error handling**: Ensure all error paths tested
- **Edge cases**: Test boundaries and limits

### Running Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check specific module
pytest tests/test_validation.py --cov=src.utils.validation

# Fail if coverage below threshold
pytest tests/ --cov=src --cov-fail-under=80
```

### Coverage Configuration

```ini
# .coveragerc or pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/examples/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Testing Best Practices

### DO These Things

✅ **Test edge cases**
```python
def test_empty_string():
    assert validate("") == False

def test_max_length():
    assert validate("a" * 255) == True
    assert validate("a" * 256) == False
```

✅ **Test error messages**
```python
def test_error_message_is_helpful():
    with pytest.raises(ValueError) as exc_info:
        validate_port("not a number")
    assert "must be an integer" in str(exc_info.value)
```

✅ **Use descriptive test names**
```python
# Good
def test_delete_user_requires_admin_permission():
    pass

# Bad
def test_delete():
    pass
```

✅ **Keep tests independent**
```python
# Each test should set up its own state
def test_a():
    data = setup_test_data()
    assert process(data) == expected

def test_b():
    data = setup_test_data()  # Don't rely on test_a
    assert process(data) == expected
```

### DON'T Do These Things

❌ **Don't test implementation details**
```python
# Bad - tests implementation
def test_uses_specific_algorithm():
    assert handler._internal_method() == X

# Good - tests behavior
def test_produces_correct_result():
    assert handler.process(input) == expected_output
```

❌ **Don't write flaky tests**
```python
# Bad - depends on timing
def test_something():
    start()
    time.sleep(1)  # Flaky!
    assert is_done()

# Good - use proper sync/async
@pytest.mark.asyncio
async def test_something():
    task = asyncio.create_task(do_work())
    result = await task
    assert result == expected
```

❌ **Don't skip cleanup**
```python
# Bad
def test_with_resource():
    f = open("test.txt")
    # Missing cleanup!

# Good
def test_with_resource():
    f = open("test.txt")
    try:
        # test code
        pass
    finally:
        f.close()

# Better - use context manager
def test_with_resource():
    with open("test.txt") as f:
        # test code
        pass
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-mock
      
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Project-Specific Testing

### TrueNAS MCP
```python
# Mock TrueNAS API responses
@pytest.fixture
def mock_truenas_response():
    return {
        "id": 1,
        "name": "tank",
        "type": "FILESYSTEM",
    }
```

### pfSense MCP
```python
# Test firewall rule validation
def test_firewall_rule_validation():
    rule = {
        "type": "pass",
        "interface": "wan",
        "protocol": "tcp",
        "src": "any",
        "dst": "192.168.1.100",
    }
    assert validate_firewall_rule(rule) == True
```

### iDRAC MCP
```python
# Test power operations
@pytest.mark.asyncio
async def test_power_off_server():
    mock_client = AsyncMock()
    mock_client.power_off.return_value = {"status": "success"}
    
    handler = PowerHandler(mock_client)
    result = await handler.power_off("server-01")
    
    assert result["status"] == "success"
    mock_client.power_off.assert_called_once_with("server-01", False)
```

### Proxmox MCP
```python
# Test VM operations
@pytest.mark.asyncio
async def test_create_vm():
    mock_client = AsyncMock()
    handler = VMHandler(mock_client)
    
    vm_config = {
        "vmid": 100,
        "name": "test-vm",
        "memory": 2048,
        "cores": 2,
    }
    
    await handler.create_vm(vm_config)
    mock_client.create_vm.assert_called_once_with(vm_config)
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Repository TESTING.md](../../TESTING.md)
