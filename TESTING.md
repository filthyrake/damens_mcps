# Testing Guide

This document explains how to run tests for the MCP servers in this repository.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Running Tests

### All Projects

Each project has its own test suite. Follow these steps for any project:

```bash
# Navigate to the project directory
cd <project-name>

# Create and activate virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v

# Run specific test
pytest tests/test_validation.py::TestClassName::test_method_name -v
```

### pfSense MCP

```bash
cd pfsense-mcp
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run validation tests only
pytest tests/test_validation.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Test Structure:**
- `tests/test_validation.py` - Input validation tests (14 tests)
- `tests/test_client.py` - Client functionality tests
- `tests/conftest.py` - Shared fixtures

### TrueNAS MCP

```bash
cd truenas-mcp
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run basic tests
pytest tests/test_basic.py -v

# Run resource tests
pytest tests/test_resources.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Test Structure:**
- `tests/test_basic.py` - Basic functionality tests
- `tests/test_resources.py` - Resource handler tests (async)
- `tests/test_validation_security.py` - Security validation tests
- `tests/conftest.py` - Shared fixtures

### iDRAC MCP

```bash
cd idrac-mcp
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run basic tests
pytest tests/test_basic.py -v

# Run multi-server tests
pytest tests/test_multi_server.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Test Structure:**
- `tests/test_basic.py` - Basic functionality tests (15 tests)
- `tests/test_multi_server.py` - Multi-server fleet management tests
- `tests/conftest.py` - Shared fixtures

### Proxmox MCP

```bash
cd proxmox-mcp
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run unit tests
pytest tests/test_unit.py -v

# Run validation tests
pytest tests/test_validation_security.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Test Structure:**
- `tests/test_unit.py` - Unit tests with mocking (18 tests)
- `tests/test_validation_security.py` - Security validation tests
- `tests/test_basic.py` - Legacy basic tests (for reference)
- `tests/conftest.py` - Shared fixtures

## Continuous Integration

Tests are automatically run on every push and pull request via GitHub Actions.

View test results at: https://github.com/filthyrake/damens_mcps/actions

## Coverage Reports

After running tests with coverage, view the HTML report:

```bash
# Open the coverage report in your browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Coverage Goals

- **Minimum**: 70% code coverage per project
- **Goal**: 80%+ code coverage
- **Critical paths**: 100% coverage for validation and security code

## Current Coverage Status

| Project | Coverage | Status |
|---------|----------|--------|
| pfSense MCP | ~6% | 🟡 Baseline established |
| TrueNAS MCP | TBD | 🟡 Tests in progress |
| iDRAC MCP | TBD | 🟡 Tests in progress |
| Proxmox MCP | ~11% | 🟡 Baseline established |

## Writing Tests

### Test Fixtures

Each project has a `conftest.py` file with reusable fixtures:

```python
import pytest

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "host": "192.168.1.100",
        "port": 443,
        "username": "test",
        "password": "test"
    }

def test_something(mock_config):
    """Use the fixture in your test."""
    assert mock_config["host"] == "192.168.1.100"
```

### Mocking API Calls

Use `unittest.mock` to mock external API calls:

```python
from unittest.mock import patch, Mock

@patch('src.client.requests.get')
def test_api_call(mock_get):
    """Test API call with mocking."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "success"}
    
    # Your test code here
```

### Async Tests

For async functions, use `pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result == expected_value
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running tests from the project directory with `pythonpath` set:

```bash
# In pytest.ini
[pytest]
pythonpath = .
```

### Async Test Warnings

If you see warnings about async tests, install `pytest-asyncio`:

```bash
pip install pytest-asyncio
```

### Coverage Not Found

If coverage reports show 0%, make sure you're using the correct coverage options:

```bash
pytest --cov=src --cov-report=term-missing
```

## Best Practices

1. **Use fixtures** for reusable test data
2. **Mock external dependencies** (API calls, file I/O)
3. **Test edge cases** and error conditions
4. **Keep tests fast** - mock slow operations
5. **Use descriptive test names** - `test_validates_invalid_ip_address`
6. **One assertion per test** when possible
7. **Test validation thoroughly** - security is critical

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass locally
3. Check coverage doesn't decrease
4. Add docstrings to test functions
5. Update this guide if needed
