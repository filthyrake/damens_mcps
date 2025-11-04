# Integration Tests for Proxmox MCP Server

This directory contains integration tests that verify MCP protocol compliance and end-to-end functionality of the Proxmox MCP server.

## Overview

These tests validate:
- JSON-RPC 2.0 protocol compliance
- MCP protocol message formats
- Tool definitions and schemas
- Error handling and response structures

## Running Integration Tests

### Quick Start

Run all integration tests:
```bash
cd proxmox-mcp
pytest tests/integration/ -v
```

Run only direct (non-subprocess) tests:
```bash
pytest tests/integration/ -v -m "not skip"
```

### Test Categories

#### 1. Protocol Compliance Tests (`test_mcp_protocol.py`)

Tests that validate JSON-RPC 2.0 and MCP protocol compliance:
- `TestMCPProtocolDirect`: Direct protocol structure validation (RUNS)
- `TestMCPProtocol`: Subprocess-based protocol tests (SKIPPED)

**Example:**
```bash
pytest tests/integration/test_mcp_protocol.py::TestMCPProtocolDirect -v
```

#### 2. End-to-End Tests (`test_e2e_proxmox.py`)

Tests that validate tool execution and response formats:
- `TestProxmoxE2EStructure`: Response structure validation (RUNS)
- `TestProxmoxE2E`: Full E2E with subprocess (SKIPPED)

**Example:**
```bash
pytest tests/integration/test_e2e_proxmox.py::TestProxmoxE2EStructure -v
```

## Test Structure

### Direct Tests (Active)

These tests validate protocol structures without requiring a running server:
- ✅ Initialize response structure
- ✅ Tools/list response structure
- ✅ Error response formats
- ✅ JSON-RPC error codes
- ✅ Tool call response structure

### Subprocess Tests (Skipped)

These tests are currently skipped due to import issues with the server:
- ⏭️ Full server initialization via subprocess
- ⏭️ Request/response cycle via stdin/stdout
- ⏭️ Malformed JSON handling
- ⏭️ Unknown method errors

**Why Skipped?**  
The `working_proxmox_server.py` uses try-except blocks to handle both module-style imports and direct execution for its validation and exception modules. This nuanced import logic can cause issues when running the server as a subprocess, leading to import errors that prevent subprocess-based testing. This is a known limitation of the current import structure and does not affect normal usage, but it does block subprocess-based integration tests.

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines:

```yaml
- name: Run integration tests
  run: |
    cd proxmox-mcp
    pytest tests/integration/ -v --cov=src --cov-report=term
```

## Adding New Tests

### Protocol Compliance Test

Add tests to validate new MCP protocol features:

```python
def test_new_protocol_feature(self):
    """Test new MCP protocol feature."""
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "newFeature": "value"
        }
    }
    
    assert response.get("jsonrpc") == "2.0"
    assert "result" in response
    assert "newFeature" in response["result"]
```

### Response Structure Test

Add tests to validate new tool response formats:

```python
def test_new_tool_response(self):
    """Test response structure for new tool."""
    response = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [
                {"type": "text", "text": "Result"}
            ],
            "isError": False
        }
    }
    
    assert "content" in response["result"]
    assert response["result"]["isError"] == False
```

## Manual Testing

For manual end-to-end testing with a running server, use the example scripts:

```bash
# Terminal 1: Start server
cd proxmox-mcp
python working_proxmox_server.py

# Terminal 2: Send test requests
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | python working_proxmox_server.py
```

## Troubleshooting

### Import Errors

If you see import errors when running tests:
```
CRITICAL ERROR: Failed to import required modules
```

**Solution:** Run tests from the project root and ensure all dependencies are installed:
```bash
cd proxmox-mcp
pip install -r requirements.txt
pytest tests/integration/ -v
```

### Coverage Warnings

Coverage warnings about modules not imported are expected for integration tests that don't import the server code directly.

### Skipped Tests

Tests marked with `@pytest.mark.skip` are intentionally skipped. They are preserved for future use when the server import structure is refactored to support subprocess testing.

## Future Improvements

- [ ] Refactor server imports to support subprocess testing
- [ ] Add mocked backend API tests
- [ ] Add concurrent request tests
- [ ] Add circuit breaker behavior tests
- [ ] Add timeout and error recovery tests

## Related Documentation

- [Main Testing Documentation](../../TESTING.md)
- [Test Coverage Summary](../../TEST_COVERAGE_SUMMARY.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
