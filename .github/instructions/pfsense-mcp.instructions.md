# Path-Specific Instructions: pfSense MCP Server

**Path:** `pfsense-mcp/`

## Project Overview

The pfSense MCP server provides firewall and network management capabilities through the Model Context Protocol. It allows AI assistants to manage pfSense firewalls programmatically.

## Key Characteristics

- **Architecture**: MCP Library-Based (uses official `mcp` Python library)
- **Transport**: HTTP server with FastAPI
- **Canonical Server**: `src/http_pfsense_server.py`
- **Configuration**: Environment variables via `.env` file

## Critical Requirements

### Server Implementation

- **ONLY use** `src/http_pfsense_server.py` as the canonical implementation
- Do not modify or use other server files (legacy files may exist)
- Server uses FastAPI for HTTP transport
- Authentication via API keys (preferred) or username/password

### Firewall Rule Validation

Firewall rules are **security-critical** and require thorough validation:

```python
# Required fields for firewall rules
required_fields = ["type", "interface", "protocol", "src", "dst"]

# Valid rule types
valid_types = ["pass", "block", "reject"]

# Rule order matters - validate dependencies
```

### Dangerous Operations

These operations can disrupt network connectivity:

- Creating/modifying firewall rules (can block access)
- Deleting firewall rules (can open security holes)
- Changing interface configurations (can lose connectivity)
- Modifying NAT rules (can break port forwarding)

Always validate thoroughly and log changes.

## Configuration

### Environment Variables

```bash
# Required
PFSENSE_HOST=192.168.1.1          # pfSense hostname or IP
PFSENSE_API_KEY=your-api-key      # API key (preferred)
# OR
PFSENSE_USERNAME=admin
PFSENSE_PASSWORD=your-password

# Optional
PFSENSE_PORT=443                  # API port (default: 443)
SSL_VERIFY=true                   # Verify SSL certificates
API_TIMEOUT=30                    # Request timeout in seconds
```

### Configuration File Location

- Primary: `.env` file in `pfsense-mcp/` directory
- Example: `env.example` (copy to `.env`)
- **NEVER commit** `.env` file

## Testing

### Running Tests

```bash
cd pfsense-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Key Test Files

- `tests/test_validation.py` - Input validation (critical, 49% coverage)
- `tests/test_client.py` - API client tests
- `tests/test_server.py` - MCP server tests

### Testing Focus

- Firewall rule validation is **critical**
- Test edge cases for network configurations
- Mock pfSense API responses
- Validate security implications

## Development Commands

```bash
# Start the server
python -m src.http_pfsense_server

# Run with specific config
python -m src.http_pfsense_server --config config.json

# Health check
curl http://localhost:8000/health

# Format code
black src/ tests/ --line-length=120
isort src/ tests/ --profile black

# Run linting
flake8 src/ tests/ --max-line-length=120
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ -ll
```

## Common Tasks

### Adding a New Firewall Tool

1. Define tool in `src/http_pfsense_server.py` tool list
2. Implement handler in appropriate resource class
3. Add comprehensive input validation
4. Add tests for the new tool
5. Update API documentation
6. Consider security implications

### Modifying Existing Rules

When modifying firewall rule handling:
- Maintain backward compatibility
- Update validation logic
- Test with various rule types
- Document any breaking changes

## Security Considerations

### API Key Management

- Use API keys instead of username/password
- Rotate keys regularly
- Store in `.env` file, never in code
- Set appropriate permissions: `chmod 600 .env`

### Firewall Rule Security

- Validate source/destination addresses
- Check for overly permissive rules (e.g., `any` to `any`)
- Log all rule changes with details
- Consider rule order and conflicts
- Prevent rules that lock out admins

### Network Security

- Use HTTPS for all API calls
- Verify SSL certificates in production
- Implement rate limiting
- Log authentication failures
- Monitor for suspicious activity

## Dependencies

### Core Dependencies

- `mcp>=1.0.0` - MCP protocol library
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment loading

### Development Dependencies

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking

## Troubleshooting

### Cannot Connect to pfSense

1. Verify pfSense is reachable: `ping $PFSENSE_HOST`
2. Check API is enabled in pfSense settings
3. Verify firewall rules allow API access
4. Check API credentials are correct
5. Ensure SSL_VERIFY setting is appropriate

### Firewall Rules Not Working

1. Check rule order (rules processed top to bottom)
2. Verify interface is correct
3. Check for conflicting rules
4. Review pfSense logs for blocks
5. Ensure rule is enabled (not disabled)

### Authentication Failures

1. Verify API key is correct
2. Check key has appropriate permissions
3. Ensure API access is enabled
4. Try regenerating the API key
5. Check for IP-based restrictions

## Related Documentation

- [pfSense MCP README](../pfsense-mcp/README.md)
- [pfSense MCP SECURITY](../pfsense-mcp/SECURITY.md)
- [pfSense Documentation](https://docs.netgate.com/)
- [Main Repository README](../README.md)

## Notes

- This is infrastructure management software - test thoroughly
- Firewall changes can lock you out - always have backup access
- Rule order matters - understand pfSense rule processing
- Keep API keys secure and rotate regularly
