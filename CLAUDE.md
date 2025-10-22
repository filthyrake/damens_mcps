# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of **Model Context Protocol (MCP) servers** for managing infrastructure components. Each MCP server provides AI assistants with direct API access to different platforms (pfSense, TrueNAS, iDRAC, Proxmox).

**Status**: All four MCP servers are production-ready and have been tested with real systems.

## Project Structure

```
damens_mcps/
├── pfsense-mcp/      # Firewall and network management
├── truenas-mcp/      # Storage and NAS management
├── idrac-mcp/        # Dell server management via iDRAC
└── proxmox-mcp/      # Virtualization platform management
```

Each project follows a similar structure:
- `src/` - Core implementation (client, server, resources, authentication)
- `examples/` or `tests/` - Usage examples and tests
- `config.example.json` or `env.example` - Configuration templates
- `requirements.txt` - Python dependencies

## Development Commands

### Setting Up a Project

```bash
# Navigate to any project directory
cd <project-name>

# Create and activate virtual environment (ALWAYS use virtual environments)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env  # For truenas-mcp and pfsense-mcp
# OR
cp config.example.json config.json  # For idrac-mcp and proxmox-mcp

# Edit configuration with actual credentials
nano .env  # or config.json
```

### Starting Servers

```bash
# TrueNAS MCP
python -m src.http_cli serve
# OR
python -m src.server

# pfSense MCP
python -m src.http_pfsense_server
# OR
python src/production_server.py

# iDRAC MCP
python working_mcp_server.py

# Proxmox MCP
python working_proxmox_server.py
# OR
python -m src.http_server
```

### Testing

```bash
# TrueNAS
python -m src.http_cli health
python examples/basic_usage.py

# pfSense
python examples/basic_usage.py

# iDRAC
python test_server.py

# Proxmox
python test_server.py
.venv/bin/python test_server.py
```

### Testing Single Tools
```bash
# Example for testing a specific MCP tool
python -m src.http_cli call-tool <tool_name>
```

## Architecture Overview

### Two MCP Implementation Patterns

The repository contains two distinct MCP server implementation patterns:

1. **MCP Library-Based** (TrueNAS, pfSense):
   - Uses the official `mcp` Python library
   - Implements `Server` class with stdio or HTTP transport
   - Uses structured types from `mcp.types` (Tool, CallToolResult, etc.)
   - More structured but requires MCP library compatibility

2. **Pure JSON-RPC** (iDRAC, Proxmox):
   - Direct JSON-RPC implementation without MCP library
   - Reads from stdin, writes to stdout
   - Manual protocol implementation for maximum compatibility
   - Better for avoiding library version conflicts

### Common Components Across Projects

**Client Classes** (e.g., `TrueNASClient`, `PfSenseClient`, `ProxmoxClient`):
- Handle API authentication (API keys, username/password, tokens)
- Make HTTP requests to target platform APIs
- Implement platform-specific API methods
- Handle connection pooling and SSL verification

**Resource Handlers** (`src/resources/`):
- Modular organization by functionality (system, storage, network, users, services)
- Inherit from base resource class
- Implement specific operations for each resource type
- Examples: `SystemResource`, `StorageResource`, `NetworkResource`

**Authentication** (`src/auth.py`):
- JWT token management for MCP client authentication
- Platform-specific auth (API keys, basic auth, ticket-based)
- Token refresh and expiration handling

**Utilities** (`src/utils/`):
- Input validation (`validation.py`)
- Logging configuration (`logging.py`)
- Common helper functions

### Configuration Patterns

**Environment Variables** (TrueNAS, pfSense):
```bash
HOST=192.168.1.100
API_KEY=your-api-key
USERNAME=admin
PASSWORD=your-password
SECRET_KEY=your-jwt-secret
SSL_VERIFY=true/false
```

**JSON Config Files** (iDRAC, Proxmox):
```json
{
  "host": "192.168.1.100",
  "username": "root",
  "password": "your-password",
  "port": 443,
  "ssl_verify": false
}
```

**Multi-Server Support** (iDRAC):
```json
{
  "idrac_servers": {
    "server1": {...},
    "server2": {...}
  },
  "default_server": "server1"
}
```

## Security Practices

### Credential Management
- **NEVER commit** `.env` files, `config.json`, or any files containing credentials
- Use `config.example.json` and `env.example` as templates
- All sensitive files are in `.gitignore`
- Store credentials in environment variables or secure config files

### SSL/TLS
- Production should use `SSL_VERIFY=true` or `ssl_verify: true`
- Self-signed certificates can use `SSL_VERIFY=false` (dev/test only)
- Custom CA certificates supported via configuration

### Input Validation
- All tool inputs are validated before execution
- Type checking and sanitization in resource handlers
- Parameter validation in client methods

## MCP Protocol Implementation

### Tool Definition Structure
```python
{
    "name": "platform_resource_action",
    "description": "Description of what the tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "description": "..."}
        },
        "required": ["param1"]
    }
}
```

### Response Format (JSON-RPC)
```python
# Success
{
    "content": [{"type": "text", "text": "Result data"}],
    "isError": False
}

# Error
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

## Common Development Tasks

### Adding a New Tool

1. **Define the tool** in server's tool list:
   ```python
   Tool(
       name="platform_new_action",
       description="What it does",
       inputSchema={...}
   )
   ```

2. **Implement the handler** in appropriate resource class:
   ```python
   async def new_action(self, param1: str, param2: int) -> Dict[str, Any]:
       # Implementation
       return result
   ```

3. **Add routing** in server's `_call_tool()` method

4. **Update documentation** in README.md

### Debugging MCP Servers

**JSON-RPC servers** (iDRAC, Proxmox):
```python
def debug_print(message: str):
    """Print to stderr to avoid interfering with stdin/stdout protocol"""
    print(f"DEBUG: {message}", file=sys.stderr)
```

**Library-based servers**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Connection Issues

1. Check network connectivity: `ping <host>`
2. Verify port access: `telnet <host> <port>`
3. Test API directly: `curl -k https://<host>/api/endpoint`
4. Check credentials in config
5. Verify API is enabled on target platform
6. Check SSL verification settings

## Platform-Specific Notes

### TrueNAS
- Requires TrueNAS SCALE 22.02+ or CORE 13+
- API key OR username/password authentication
- HTTP-based MCP server with FastAPI
- CLI tool: `python -m src.http_cli`

### pfSense
- Requires pfSense 2.5+ with REST API enabled
- Must enable API access in System → API
- Multiple server implementations (use `production_server.py` or `http_pfsense_server.py`)
- Comprehensive firewall rule management

### iDRAC
- Supports Dell PowerEdge servers with iDRAC 8+
- Uses Redfish API standard
- Multi-server fleet management support
- Pure JSON-RPC implementation for reliability

### Proxmox
- Requires Proxmox VE 7.0+
- Ticket-based authentication (PVE realm)
- 21 tools covering VMs, containers, storage, snapshots
- Auto VMID assignment for new VMs

## Dependencies

### Core Dependencies (Common)
- `requests` - HTTP client for API calls
- `urllib3` - HTTP library with SSL support
- `python-dotenv` - Environment variable loading

### MCP Library Stack (TrueNAS, pfSense)
- `mcp>=1.0.0` - Official MCP protocol implementation
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-jose` - JWT token handling

### Testing & Development
- `pytest` - Testing framework
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking

## Important Notes

### Virtual Environments
**ALWAYS use virtual environments** for Python projects (per user's global instructions). Never install packages globally.

### API Rate Limiting
Be mindful of API call frequency. Most platforms have rate limits:
- Cache results when appropriate
- Batch operations when possible
- Use health checks before heavy operations

### Dangerous Operations
Some tools perform destructive actions:
- Power off/restart servers (iDRAC)
- Delete VMs/containers (Proxmox)
- Remove firewall rules (pfSense)
- Delete datasets (TrueNAS)

Always validate parameters and consider confirmation prompts.

### Configuration Priority
Most projects follow this priority:
1. Command-line arguments (if applicable)
2. Environment variables
3. Configuration files
4. Default values

### Logging
- Log to stderr for JSON-RPC servers (stdout is for protocol)
- Use Python `logging` module for structured logging
- Debug mode available via environment variables or config
