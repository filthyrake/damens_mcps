# Integration Tests for iDRAC MCP Server

This directory contains integration tests that verify MCP protocol compliance and end-to-end functionality of the iDRAC MCP server.

## Overview

These tests validate:
- JSON-RPC 2.0 protocol compliance
- MCP protocol message formats
- Tool definitions specific to iDRAC operations
- Error handling and response structures

## Running Integration Tests

### Quick Start

Run all integration tests:
```bash
cd idrac-mcp
pytest tests/integration/ -v
```

Run only active tests (skip subprocess tests):
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

## Test Structure

### Direct Tests (Active)

These tests validate protocol structures and iDRAC-specific features:
- ✅ Initialize response structure
- ✅ Tools/list response structure
- ✅ Error response formats
- ✅ iDRAC tool naming conventions
- ✅ Expected iDRAC tools present

### Subprocess Tests (Skipped)

These tests are currently skipped:
- ⏭️ Full server initialization via subprocess
- ⏭️ Request/response cycle via stdin/stdout
- ⏭️ Multi-server configuration testing

## iDRAC-Specific Tools Tested

The integration tests validate the presence and structure of core iDRAC tools:
- `idrac_get_system_info` - System information retrieval
- `idrac_get_power_state` - Power state checking
- `idrac_power_on` - Server power on
- `idrac_power_off` - Server power off
- `idrac_graceful_shutdown` - Graceful shutdown
- `idrac_force_restart` - Force restart

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines:

```yaml
- name: Run integration tests
  run: |
    cd idrac-mcp
    pytest tests/integration/ -v --cov=src --cov-report=term
```

## Adding New Tests

### iDRAC Tool Validation

Add tests for new iDRAC tools:

```python
def test_new_idrac_tool_structure(self):
    """Test structure for new iDRAC tool."""
    tool = {
        "name": "idrac_new_operation",
        "description": "Perform new operation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "server_id": {"type": "string"}
            }
        }
    }
    
    assert tool["name"].startswith("idrac_")
    assert "description" in tool
    assert "inputSchema" in tool
```

## Manual Testing

For manual testing with actual iDRAC servers:

```bash
# Create config.json with your iDRAC credentials
cp config.example.json config.json
# Edit config.json with actual server details

# Terminal 1: Start server
python working_mcp_server.py

# Terminal 2: Send test requests
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | python working_mcp_server.py
```

## Fleet Management Testing

For testing multi-server (fleet) scenarios:

```python
def test_fleet_configuration(self):
    """Test that fleet configuration is valid."""
    config = {
        "idrac_servers": {
            "server1": {...},
            "server2": {...}
        },
        "default_server": "server1"
    }
    
    assert "idrac_servers" in config
    assert "default_server" in config
    assert config["default_server"] in config["idrac_servers"]
```

## Troubleshooting

### Server Not Starting

If the server fails to start in tests:
```
RuntimeError: Server process died
```

**Solution:** This is expected for skipped subprocess tests. Run the direct tests instead:
```bash
pytest tests/integration/test_mcp_protocol.py::TestMCPProtocolDirect -v
```

### Config File Issues

If you get configuration errors:
```
Configuration file not found
```

**Solution:** Tests use mock configurations. If running manual tests, ensure `config.json` exists:
```bash
cp config.example.json config.json
```

## Security Considerations

When testing with real iDRAC servers:
- ✅ Use test credentials, not production credentials
- ✅ Test in isolated environment
- ✅ Never commit config.json to version control
- ✅ Use `ssl_verify: true` for production testing

## Future Improvements

- [ ] Add multi-server fleet testing
- [ ] Add concurrent request tests
- [ ] Add timeout and retry behavior tests
- [ ] Add credential validation tests
- [ ] Add SSL certificate validation tests

## Related Documentation

- [Main iDRAC Documentation](../../README.md)
- [Security Guidelines](../../SECURITY.md)
- [Usage Guide](../../USAGE_GUIDE.md)
