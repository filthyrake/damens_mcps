# Path-Specific Instructions: TrueNAS MCP Server

**Path:** `truenas-mcp/`

## Project Overview

The TrueNAS MCP server provides storage and NAS management capabilities through the Model Context Protocol. It allows AI assistants to manage TrueNAS systems programmatically.

## Key Characteristics

- **Architecture**: MCP Library-Based (uses official `mcp` Python library)
- **Transport**: HTTP server with FastAPI or stdio
- **Canonical Server**: `src/http_cli.py` with HTTP server mode
- **Configuration**: Environment variables via `.env` file

## Critical Requirements

### Server Implementation

- **ONLY use** `src/http_cli.py` as the canonical implementation
- Server supports both HTTP and stdio transports
- Start HTTP server: `python -m src.http_cli serve`
- Health check: `python -m src.http_cli health`
- Authentication via API keys (preferred) or username/password

### Storage Operations

Storage operations are **data-critical** and require thorough validation:

```python
# Dataset operations can result in data loss
# Pool operations affect system availability
# Share operations impact data access
```

### Dangerous Operations

These operations can cause **permanent data loss**:

- Deleting datasets (cannot be undone)
- Destroying pools (removes all data)
- Deleting snapshots (cannot be recovered)
- Modifying share permissions (can lock out users)

**ALWAYS:**
- Validate dataset/pool names thoroughly
- Prevent deletion of system datasets
- Log all destructive operations
- Consider requiring explicit confirmation flags

## Configuration

### Environment Variables

```bash
# Required
TRUENAS_HOST=192.168.1.100        # TrueNAS hostname or IP
TRUENAS_API_KEY=your-api-key      # API key (preferred)
# OR
TRUENAS_USERNAME=admin
TRUENAS_PASSWORD=your-password

# Optional
TRUENAS_PORT=443                  # API port (default: 443)
SSL_VERIFY=true                   # Verify SSL certificates
API_TIMEOUT=30                    # Request timeout in seconds
SERVER_HOST=0.0.0.0              # HTTP server bind address
SERVER_PORT=8000                  # HTTP server port
```

### Configuration File Location

- Primary: `.env` file in `truenas-mcp/` directory
- Example: `env.example` (copy to `.env`)
- **NEVER commit** `.env` file

## Testing

### Running Tests

```bash
cd truenas-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Key Test Files

- `tests/test_validation.py` - Input validation (critical)
- `tests/test_client.py` - API client tests
- `tests/test_server.py` - MCP server tests
- `tests/test_resources/` - Resource handler tests

### Testing Focus

- Dataset/pool name validation is **critical**
- Test edge cases for storage configurations
- Mock TrueNAS API responses
- Validate data safety checks
- Test permission handling

## Development Commands

```bash
# Start HTTP server
python -m src.http_cli serve

# Start with custom port
python -m src.http_cli serve --port 8080

# Health check
python -m src.http_cli health
curl http://localhost:8000/health

# Run in stdio mode (for Claude Desktop integration)
python -m src.http_cli

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

### Adding a New Storage Tool

1. Define tool in `src/http_cli.py` tool list
2. Implement handler in appropriate resource class (e.g., `src/resources/storage.py`)
3. Add comprehensive input validation
4. Add safety checks for destructive operations
5. Add tests for the new tool
6. Update API documentation
7. Consider data loss implications

### Working with Datasets

```python
# Validate dataset names
# - No spaces or special characters
# - Follow ZFS naming conventions
# - Check for system dataset prefixes

# Prevent system dataset operations
PROTECTED_PREFIXES = ['boot-pool', 'freenas-boot', '.system']

def validate_dataset_name(name: str) -> bool:
    """Validate dataset name."""
    if any(name.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        raise ValueError("Cannot operate on system datasets")
    # Additional validation...
```

### Working with Pools

```python
# Pool operations affect entire storage infrastructure
# Validate pool exists before operations
# Check pool health before destructive operations
# Log all pool modifications
```

## Security Considerations

### API Key Management

- Use API keys instead of username/password
- Generate keys with minimum required permissions
- Rotate keys regularly
- Store in `.env` file, never in code
- Set appropriate permissions: `chmod 600 .env`

### Storage Access Control

- Validate share permissions thoroughly
- Check user/group permissions
- Prevent overly permissive shares
- Log permission changes
- Monitor access patterns

### Data Protection

- Implement snapshots before destructive operations (when possible)
- Validate dataset deletion requests
- Log all data modifications
- Prevent accidental system dataset operations
- Consider implementing dry-run mode

## Dependencies

### Core Dependencies

- `mcp>=1.0.0` - MCP protocol library
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment loading
- `typer` - CLI framework

### Development Dependencies

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking

## Docker Deployment

TrueNAS MCP supports containerized deployment:

```bash
# Build image
cd truenas-mcp
docker build -f docker/Dockerfile -t truenas-mcp .

# Run container
docker run -p 8000:8000 --env-file .env truenas-mcp

# Using Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes Deployment

```bash
# Apply manifests
cd truenas-mcp
kubectl apply -f k8s/

# Check deployment
kubectl get pods -l app=truenas-mcp
kubectl logs -f deployment/truenas-mcp
```

## Troubleshooting

### Cannot Connect to TrueNAS

1. Verify TrueNAS is reachable: `ping $TRUENAS_HOST`
2. Check API is enabled in TrueNAS settings
3. Verify firewall rules allow API access
4. Check API credentials are correct
5. Ensure SSL_VERIFY setting is appropriate
6. Check TrueNAS version compatibility

### Dataset Operations Failing

1. Verify dataset name is valid (ZFS naming rules)
2. Check parent pool exists and is healthy
3. Verify sufficient storage space
4. Check for name conflicts
5. Review TrueNAS system logs

### Authentication Failures

1. Verify API key is correct and not expired
2. Check key has appropriate permissions
3. Ensure API service is running
4. Try regenerating the API key
5. Check for IP-based restrictions
6. Verify TrueNAS user account is active

### Permission Issues

1. Check API key permissions in TrueNAS
2. Verify dataset/share ACLs
3. Check user/group ownership
4. Review TrueNAS audit logs
5. Ensure user has required roles

## TrueNAS API Specifics

### API Versioning

- TrueNAS CORE and SCALE have different APIs
- Check TrueNAS version: `/api/v2.0/system/info`
- Some features are version-specific
- Test with your TrueNAS version

### Rate Limiting

- TrueNAS API has rate limits
- Implement exponential backoff
- Cache results when appropriate
- Batch operations when possible

### WebSocket Support

- TrueNAS supports WebSocket for real-time updates
- Subscribe to dataset/pool events
- Handle connection drops gracefully
- Reconnect with exponential backoff

## Related Documentation

- [TrueNAS MCP README](../truenas-mcp/README.md)
- [TrueNAS MCP SECURITY](../truenas-mcp/SECURITY.md)
- [TrueNAS Documentation](https://www.truenas.com/docs/)
- [TrueNAS API Documentation](https://www.truenas.com/docs/api/)
- [Main Repository README](../README.md)

## Notes

- This manages critical storage infrastructure - test thoroughly
- Dataset deletion is permanent - implement safety checks
- Pool operations affect system availability
- Always have backup access method
- Keep API keys secure and rotate regularly
- Monitor storage capacity and pool health
- Test disaster recovery procedures
