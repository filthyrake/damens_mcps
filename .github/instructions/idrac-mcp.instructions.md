# Path-Specific Instructions: iDRAC MCP Server

**Path:** `idrac-mcp/`

## Project Overview

The iDRAC MCP server provides Dell PowerEdge server management capabilities through the Model Context Protocol. It allows AI assistants to manage Dell servers via iDRAC (Integrated Dell Remote Access Controller).

## Key Characteristics

- **Architecture**: Pure JSON-RPC (no MCP library)
- **Transport**: stdin/stdout JSON-RPC protocol
- **Canonical Server**: `working_mcp_server.py` **ONLY**
- **Configuration**: JSON configuration file (`config.json`)
- **Fleet Support**: Manages multiple servers simultaneously

## Critical Requirements

### Server Implementation

- **ONLY use** `working_mcp_server.py` as the canonical implementation
- **DO NOT use or modify** other server files (they exist for historical reasons)
- Server reads JSON-RPC from stdin, writes to stdout
- Use stderr for debugging: `print(message, file=sys.stderr)`
- Multiple server fleet support built-in

### Power Operations

Power operations are **extremely dangerous** and can cause:
- Production downtime
- Data loss if systems aren't shut down gracefully
- Service interruption
- Hardware issues if done improperly

**ALWAYS:**
- Validate server IDs carefully
- Log all power operations with details
- Consider graceful shutdown before power off
- Implement confirmation for forced operations
- Check server status before operations

### Dangerous Operations

These operations can cause significant problems:

- **Power off/on/reset** - Immediate downtime
- **Force power off** - Can cause data corruption
- **BIOS configuration changes** - Can brick servers
- **Firmware updates** - Can fail and brick hardware

## Configuration

### Configuration File Format

```json
{
  "servers": [
    {
      "id": "server-01",
      "host": "192.168.1.10",
      "username": "root",
      "password": "calvin",
      "verify_ssl": false
    },
    {
      "id": "server-02",
      "host": "192.168.1.11",
      "username": "root",
      "password": "calvin",
      "verify_ssl": false
    }
  ],
  "defaults": {
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 5
  }
}
```

### Configuration File Location

- Primary: `config.json` in `idrac-mcp/` directory
- Example: `config.example.json` (copy to `config.json`)
- **NEVER commit** `config.json` file
- Set permissions: `chmod 600 config.json`

### Server IDs

- Each server must have unique ID
- IDs used to target specific servers
- Validate server IDs before operations
- Support for "all" to target all servers (use with extreme caution)

## Testing

### Running Tests

```bash
cd idrac-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Key Test Files

- `tests/test_validation.py` - Input validation (critical, 91% coverage)
- `tests/test_client.py` - iDRAC API client tests
- `tests/test_server.py` - MCP server tests

### Testing Focus

- Server ID validation is **critical**
- Test power operation safety checks
- Mock iDRAC Redfish API responses
- Validate fleet operations
- Test error handling for unreachable servers

## Development Commands

```bash
# Start the server (stdin/stdout mode)
python working_mcp_server.py

# Test with sample input
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python working_mcp_server.py

# Debug mode (prints to stderr)
DEBUG=1 python working_mcp_server.py

# Format code
black working_mcp_server.py tests/ --line-length=120
isort working_mcp_server.py tests/ --profile black

# Run linting
flake8 working_mcp_server.py tests/ --max-line-length=120
mypy working_mcp_server.py --ignore-missing-imports

# Security scan
bandit -r . -ll
```

## Common Tasks

### Adding a New iDRAC Tool

1. Define tool in `working_mcp_server.py` tool list
2. Add tool handler function
3. Implement iDRAC Redfish API call
4. Add comprehensive input validation
5. Add tests for the new tool
6. Update documentation
7. Consider fleet operation support

### Working with Redfish API

```python
# iDRAC uses Redfish API standard
BASE_URL = f"https://{host}/redfish/v1"

# Common endpoints
SYSTEM_ENDPOINT = f"{BASE_URL}/Systems/System.Embedded.1"
MANAGER_ENDPOINT = f"{BASE_URL}/Managers/iDRAC.Embedded.1"

# Power operations
POWER_ACTIONS = {
    "on": "On",
    "off": "ForceOff",
    "graceful_off": "GracefulShutdown",
    "reset": "ForceRestart",
    "graceful_reset": "GracefulRestart"
}
```

### Fleet Operations

```python
# Operating on multiple servers
# - Iterate through server list
# - Handle partial failures
# - Collect results from all servers
# - Log operations per server
# - Implement proper error aggregation

def fleet_operation(operation_func):
    """Execute operation on all servers."""
    results = {}
    for server in servers:
        try:
            results[server["id"]] = operation_func(server)
        except Exception as e:
            results[server["id"]] = {"error": str(e)}
    return results
```

## Security Considerations

### Credential Management

- Store credentials in `config.json`, never in code
- Use strong passwords for iDRAC
- Consider using SSH keys where supported
- Rotate credentials regularly
- Set file permissions: `chmod 600 config.json`

### Network Security

- iDRAC is typically on management network
- Restrict access to management network
- Use VPN for remote access
- Consider enabling 2FA on iDRAC
- Monitor iDRAC access logs

### Power Operation Safety

```python
def safe_power_off(server_id: str, force: bool = False):
    """Safely power off server with validation."""
    # Validate server exists
    server = get_server_by_id(server_id)
    if not server:
        raise ValueError(f"Server {server_id} not found")
    
    # Check current state
    state = get_power_state(server)
    if state == "Off":
        return {"status": "already_off"}
    
    # Log the operation
    logger.warning(f"Power off {server_id}, force={force}")
    
    # Use graceful shutdown unless force specified
    action = "ForceOff" if force else "GracefulShutdown"
    
    return power_action(server, action)
```

## Dependencies

### Core Dependencies

- `requests` - HTTP client for Redfish API
- `urllib3` - HTTP library
- No MCP library (pure JSON-RPC implementation)

### Development Dependencies

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking

## Protocol Implementation

### JSON-RPC Message Format

```python
# Request
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_power_status",
        "arguments": {"server_id": "server-01"}
    },
    "id": 1
}

# Success Response
{
    "jsonrpc": "2.0",
    "result": {
        "content": [
            {"type": "text", "text": '{"power_state": "On"}'}
        ]
    },
    "id": 1
}

# Error Response
{
    "jsonrpc": "2.0",
    "error": {
        "code": -32602,
        "message": "Invalid params"
    },
    "id": 1
}
```

### Debugging Tips

```python
# Use stderr for debug output (stdout is for protocol)
import sys

def debug_print(message):
    """Print debug message to stderr."""
    print(f"DEBUG: {message}", file=sys.stderr)

# Example usage
debug_print(f"Processing request: {request}")
debug_print(f"Server config: {server}")
```

## Troubleshooting

### Cannot Connect to iDRAC

1. Verify iDRAC is reachable: `ping $IDRAC_HOST`
2. Check iDRAC web interface is accessible
3. Verify credentials are correct
4. Check network routing to management network
5. Ensure iDRAC is enabled and licensed
6. Check SSL certificate (use verify_ssl: false for self-signed)

### Power Operations Failing

1. Check server current power state
2. Verify iDRAC has power control permissions
3. Check for active sessions blocking operations
4. Review iDRAC system logs
5. Ensure no BIOS operations in progress
6. Check for hardware faults

### Authentication Failures

1. Verify username/password in config.json
2. Check account is not locked
3. Ensure account has Administrator role
4. Verify iDRAC firmware version compatibility
5. Check for expired passwords
6. Review iDRAC security settings

### Multiple Server Issues

1. Validate server IDs are unique
2. Check network connectivity to all servers
3. Verify each server's credentials
4. Check for mixed iDRAC firmware versions
5. Review timeout settings
6. Check for DNS resolution issues

## iDRAC API Specifics

### Redfish API Standard

- iDRAC implements Redfish API standard
- Version support varies by firmware
- Check compatibility: `GET /redfish/v1`
- Some features require specific firmware versions

### Power State Transitions

- Valid states: On, Off, PoweringOn, PoweringOff
- Some transitions take time (wait for completion)
- Forced operations bypass graceful shutdown
- Check state before and after operations

### System Information

```python
# Get comprehensive system info
system_info = {
    "model": "PowerEdge R640",
    "service_tag": "ABC1234",
    "bios_version": "2.10.0",
    "idrac_version": "4.40.00.00",
    "power_state": "On",
    "health": "OK"
}
```

## Related Documentation

- [iDRAC MCP README](../idrac-mcp/README.md)
- [iDRAC MCP SECURITY](../idrac-mcp/SECURITY.md)
- [Dell iDRAC Documentation](https://www.dell.com/support/kbdoc/en-us/000177080/idrac)
- [Redfish API Specification](https://www.dmtf.org/standards/redfish)
- [Main Repository README](../README.md)

## Notes

- This controls physical server hardware - be extremely careful
- Power operations can cause production outages
- Test with non-production servers first
- Always have out-of-band access (console, KVM)
- Keep firmware updated for security and compatibility
- Document your server inventory
- Implement change management for production servers
