# GitHub Copilot Instructions

This file provides instructions for GitHub Copilot coding agent when working with this repository.

## Project Overview

This is a collection of **Model Context Protocol (MCP) servers** for managing infrastructure components. Each MCP server provides AI assistants with direct API access to different platforms through standardized MCP interfaces.

### Repository Structure

```
damens_mcps/
├── pfsense-mcp/      # Firewall and network management for pfSense
├── truenas-mcp/      # Storage and NAS management for TrueNAS
├── idrac-mcp/        # Dell server management via iDRAC
└── proxmox-mcp/      # Virtualization platform management for Proxmox VE
```

### Project Status

- **pfSense MCP**: ✅ Production-ready - Comprehensive firewall management with 20+ tools
- **TrueNAS MCP**: ✅ Production-ready - Storage and NAS management with HTTP/CLI interface
- **iDRAC MCP**: ✅ Stable - Dell server power management with 8 tools for multi-server fleets
- **Proxmox MCP**: ✅ Stable - Virtualization management with 21 tools for VMs and containers

## Development Environment Setup

### Python Virtual Environment (REQUIRED)

**ALWAYS use virtual environments** for Python development. Never install packages globally.

```bash
# Navigate to project directory
cd <project-name>

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Each project uses different configuration methods:

**TrueNAS & pfSense:**
```bash
cp env.example .env
# Edit .env with actual credentials
```

**iDRAC & Proxmox:**
```bash
cp config.example.json config.json
# Edit config.json with actual credentials
```

## Coding Conventions

### General Standards

1. **Python Version**: Python 3.8+ required
2. **Code Style**: Follow PEP 8 standards
3. **Type Hints**: Use type annotations for function parameters and returns
4. **Async/Await**: Use async functions for I/O operations
5. **Error Handling**: Comprehensive exception handling with meaningful messages

### Project Architecture Patterns

The repository uses **two distinct MCP implementation patterns**:

#### 1. MCP Library-Based (TrueNAS, pfSense)
- Uses official `mcp` Python library
- Implements `Server` class with stdio or HTTP transport
- Uses structured types from `mcp.types`

#### 2. Pure JSON-RPC (iDRAC, Proxmox)
- Direct JSON-RPC implementation without MCP library
- Reads from stdin, writes to stdout
- Manual protocol implementation for maximum compatibility

### File Organization

Each project follows this structure:
```
project-name/
├── src/
│   ├── auth.py              # Authentication logic
│   ├── client.py            # API client implementation
│   ├── server.py            # MCP server (or working_*_server.py)
│   ├── resources/           # Resource handlers by functionality
│   │   ├── system.py
│   │   ├── storage.py
│   │   ├── network.py
│   │   └── ...
│   └── utils/
│       ├── validation.py    # Input validation
│       └── logging.py       # Logging configuration
├── tests/                   # Test files
├── examples/                # Usage examples
├── requirements.txt         # Dependencies
└── README.md               # Project documentation
```

## Build & Test Instructions

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests for a project
cd <project-name>
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v
```

### Test Coverage Requirements

- All projects have test infrastructure with CI/CD automation
- Input validation tests are critical (high coverage)
- Integration tests require actual system configuration
- Mock tests for unit testing without dependencies

### Starting Servers

Use the **canonical implementation** for each project:

```bash
# TrueNAS MCP
python -m src.http_cli serve

# pfSense MCP
python -m src.http_pfsense_server

# iDRAC MCP (ONLY use this implementation)
python working_mcp_server.py

# Proxmox MCP (ONLY use this implementation)
python working_proxmox_server.py
```

### Health Checks

```bash
# TrueNAS
python -m src.http_cli health

# Check server endpoints (if HTTP-based)
curl http://localhost:8000/health
```

## Security Requirements

### Critical Security Rules

1. **NEVER commit credentials** - No `.env`, `config.json`, or files with passwords
2. **Use .gitignore** - All sensitive files must be in `.gitignore`
3. **File permissions** - Set `chmod 600` on config files with credentials
4. **API keys preferred** - Use API keys over passwords when possible
5. **SSL verification** - Use `SSL_VERIFY=true` in production

### Project-Specific Security

Each project has a `SECURITY.md` file with detailed guidance:
- **pfSense**: API key management, firewall rules
- **TrueNAS**: API key management, storage access controls
- **iDRAC**: Credential encryption options, fleet management
- **Proxmox**: VM management security, ticket-based auth

### Input Validation

- All tool inputs MUST be validated before execution
- Type checking and sanitization in resource handlers
- Parameter validation in client methods
- Dangerous operations (power off, delete) require special handling

## Pull Request Validation

### Pre-Commit Checklist

- [ ] Code follows PEP 8 standards
- [ ] All functions have type hints
- [ ] Input validation added for new parameters
- [ ] Error handling implemented
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] No credentials or sensitive data in commits
- [ ] Virtual environment used (not global packages)

### Testing Requirements

- Run `pytest tests/ -v` and ensure all tests pass
- Add tests for new functionality
- Update existing tests if behavior changes
- Integration tests are optional (require system access)

### Code Review Points

1. **Security**: Check for credential leaks or security issues
2. **Error Handling**: Verify comprehensive exception handling
3. **Input Validation**: Ensure all inputs are validated
4. **Documentation**: Verify README/docstrings are updated
5. **Testing**: Confirm appropriate test coverage

## Common Development Tasks

### Adding a New Tool

1. **Define the tool** in server's tool list:
```python
Tool(
    name="platform_resource_action",
    description="Clear description of what the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
        },
        "required": ["param1"]
    }
)
```

2. **Implement the handler** in appropriate resource class:
```python
async def new_action(self, param1: str) -> Dict[str, Any]:
    # Validate input
    # Perform action
    # Return result
    return {"status": "success", "data": result}
```

3. **Add routing** in server's `_call_tool()` method
4. **Add tests** in `tests/` directory
5. **Update documentation** in README.md

### Debugging MCP Servers

**For JSON-RPC servers (iDRAC, Proxmox):**
```python
def debug_print(message: str):
    """Print to stderr to avoid interfering with stdin/stdout protocol"""
    print(f"DEBUG: {message}", file=sys.stderr)
```

**For library-based servers:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Connection Issues

1. Verify network connectivity: `ping <host>`
2. Check port access: `telnet <host> <port>`
3. Test API directly: `curl -k https://<host>/api/endpoint`
4. Verify credentials in config
5. Confirm API is enabled on target platform
6. Check SSL verification settings

## Dependencies

### Core Dependencies (Common to All Projects)

- `requests` - HTTP client for API calls
- `urllib3` - HTTP library with SSL support
- `python-dotenv` - Environment variable loading (TrueNAS/pfSense)

### MCP Library Stack (TrueNAS, pfSense)

- `mcp>=1.0.0` - Official MCP protocol implementation
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-jose` - JWT token handling

### Testing & Development

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities

## Important Notes

### Canonical Implementations

Each project has a **canonical server implementation** - the definitive version to use:
- TrueNAS: `src/http_cli.py` with HTTP server
- pfSense: `src/http_pfsense_server.py`
- iDRAC: `working_mcp_server.py` (NOT other server files)
- Proxmox: `working_proxmox_server.py` (NOT other server files)

Other server files may exist for historical reasons but should NOT be used or modified.

### Dangerous Operations

Some tools perform destructive actions. Handle with care:
- Power off/restart servers (iDRAC)
- Delete VMs/containers (Proxmox)
- Remove firewall rules (pfSense)
- Delete datasets (TrueNAS)

Always validate parameters and consider user confirmation for destructive operations.

### API Rate Limiting

Be mindful of API call frequency:
- Cache results when appropriate
- Batch operations when possible
- Use health checks before heavy operations

### Logging Best Practices

- **JSON-RPC servers**: Log to stderr (stdout is for protocol)
- **HTTP servers**: Standard logging to stdout
- Use Python `logging` module for structured logging
- Debug mode available via environment variables

## Documentation Files

### Repository Documentation

- **CLAUDE.md** - Comprehensive guide for Claude Code (claude.ai/code) when working with this repository
- **README.md** - Main repository overview and quick start
- **SETUP_GUIDE.md** - Detailed setup instructions
- **TESTING.md** - Testing guide and best practices
- **TEST_COVERAGE_SUMMARY.md** - Test coverage details
- **SECURITY_SUMMARY.md** - Security overview across projects

### Project-Specific Documentation

Each project directory contains:
- **README.md** - Project-specific documentation
- **SECURITY.md** - Security best practices
- **CONTRIBUTING.md** - Contribution guidelines
- **examples/** - Usage examples
- **tests/** - Test files

## MCP Protocol Implementation

### Tool Response Format

```python
# Success response
{
    "content": [{"type": "text", "text": "Result data"}],
    "isError": False
}

# Error response
{
    "content": [{"type": "text", "text": "Error message"}],
    "isError": True
}
```

### Common MCP Methods

- `tools/list` - List all available tools
- `tools/call` - Execute a specific tool
- `initialize` - Initialize MCP connection
- `ping` - Health check

## Additional Resources

### Platform Documentation

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [pfSense Documentation](https://docs.netgate.com/)
- [TrueNAS Documentation](https://www.truenas.com/docs/)
- [Dell iDRAC Documentation](https://www.dell.com/support/manuals/)
- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/)

### Internal References

When making changes, always review:
1. The project-specific README.md
2. The SECURITY.md for security considerations
3. Existing tests for patterns and examples
4. Example scripts for usage patterns

---

**Remember**: This is infrastructure management software. Security and reliability are paramount. Always test thoroughly and follow security best practices.
