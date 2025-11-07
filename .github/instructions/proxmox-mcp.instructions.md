# Path-Specific Instructions: Proxmox MCP Server

**Path:** `proxmox-mcp/`

## Project Overview

The Proxmox MCP server provides virtualization platform management capabilities through the Model Context Protocol. It allows AI assistants to manage Proxmox VE (Virtual Environment) clusters, VMs, and containers.

## Key Characteristics

- **Architecture**: Pure JSON-RPC (no MCP library)
- **Transport**: stdin/stdout JSON-RPC protocol
- **Canonical Server**: `working_proxmox_server.py` **ONLY**
- **Configuration**: JSON configuration file (`config.json`)
- **Authentication**: Ticket-based authentication

## Critical Requirements

### Server Implementation

- **ONLY use** `working_proxmox_server.py` as the canonical implementation
- **DO NOT use or modify** other server files (they exist for historical reasons)
- Server reads JSON-RPC from stdin, writes to stdout
- Use stderr for debugging: `print(message, file=sys.stderr)`
- Supports cluster and multi-node operations

### VM and Container Operations

VM/Container operations are **production-critical** and can cause:
- Service interruption
- Data loss
- Resource exhaustion
- Network connectivity issues

**ALWAYS:**
- Validate VM/Container IDs (VMIDs)
- Check resource availability before creation
- Verify node has capacity
- Log all operations with details
- Implement safety checks for destructive operations

### Dangerous Operations

These operations can cause significant problems:

- **VM/CT deletion** - Permanent data loss
- **Snapshot deletion** - Cannot recover data
- **Resource allocation changes** - Can affect performance
- **Network configuration** - Can break connectivity
- **Cluster operations** - Can affect entire infrastructure

## Configuration

### Configuration File Format

```json
{
  "host": "192.168.1.50",
  "port": 8006,
  "username": "root@pam",
  "password": "your-password",
  "verify_ssl": false,
  "timeout": 30,
  "node": "pve-node1",
  "realm": "pam"
}
```

### Configuration File Location

- Primary: `config.json` in `proxmox-mcp/` directory
- Example: `config.example.json` (copy to `config.json`)
- **NEVER commit** `config.json` file
- Set permissions: `chmod 600 config.json`

### Authentication

Proxmox uses ticket-based authentication:
- Initial authentication creates ticket and CSRF token
- Ticket has limited lifetime (default 2 hours)
- Re-authenticate when ticket expires
- Store ticket securely during session

## Testing

### Running Tests

```bash
cd proxmox-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock

pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Key Test Files

- `tests/test_validation.py` - Input validation (critical, 72% coverage)
- `tests/test_client.py` - Proxmox API client tests
- `tests/test_server.py` - MCP server tests

### Testing Focus

- VMID validation is **critical**
- Test resource allocation limits
- Mock Proxmox API responses
- Validate destructive operation safety
- Test cluster operations
- Verify snapshot handling

## Development Commands

```bash
# Start the server (stdin/stdout mode)
python working_proxmox_server.py

# Test with sample input
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python working_proxmox_server.py

# Debug mode (prints to stderr)
DEBUG=1 python working_proxmox_server.py

# Format code
black working_proxmox_server.py tests/ --line-length=120
isort working_proxmox_server.py tests/ --profile black

# Run linting
flake8 working_proxmox_server.py tests/ --max-line-length=120
mypy working_proxmox_server.py --ignore-missing-imports

# Security scan
bandit -r . -ll
```

## Common Tasks

### Adding a New Proxmox Tool

1. Define tool in `working_proxmox_server.py` tool list
2. Add tool handler function
3. Implement Proxmox API call
4. Add comprehensive input validation
5. Add tests for the new tool
6. Update documentation
7. Consider cluster-aware operations

### Working with VMs

```python
# VM operations require:
# - Valid VMID (100-999999999)
# - Valid node name
# - Sufficient resources
# - Proper permissions

def create_vm(vmid: int, config: dict) -> dict:
    """
    Create a new VM.
    
    Required config:
    - name: VM name
    - memory: RAM in MB
    - cores: CPU cores
    - disk: Disk size
    - network: Network configuration
    """
    # Validate VMID
    if not (100 <= vmid <= 999999999):
        raise ValueError("VMID must be between 100 and 999999999")
    
    # Check VMID not in use
    if vmid_exists(vmid):
        raise ValueError(f"VMID {vmid} already exists")
    
    # Validate resources available
    validate_resources(config)
    
    # Create VM
    return api.create_vm(node, vmid, config)
```

### Working with Containers (LXC)

```python
# Container operations similar to VMs but with:
# - Container templates instead of ISOs
# - Shared kernel with host
# - Different resource model
# - Unprivileged vs privileged containers

def create_container(vmid: int, config: dict) -> dict:
    """Create LXC container."""
    # Validate template exists
    if not template_exists(config["ostemplate"]):
        raise ValueError("Template not found")
    
    # Check for privileged container security
    if config.get("unprivileged", True) == False:
        logger.warning(f"Creating PRIVILEGED container {vmid}")
    
    return api.create_container(node, vmid, config)
```

### Snapshot Management

```python
# Snapshots are critical for:
# - Backup and recovery
# - Testing changes safely
# - Point-in-time recovery

def create_snapshot(vmid: int, name: str, description: str = "") -> dict:
    """Create VM/CT snapshot."""
    # Validate snapshot name
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Invalid snapshot name")
    
    # Check snapshot doesn't exist
    if snapshot_exists(vmid, name):
        raise ValueError(f"Snapshot {name} already exists")
    
    logger.info(f"Creating snapshot {name} for VMID {vmid}")
    return api.create_snapshot(node, vmid, name, description)
```

## Security Considerations

### Credential Management

- Store credentials in `config.json`, never in code
- Use API tokens instead of passwords (Proxmox 7.0+)
- Rotate credentials regularly
- Set file permissions: `chmod 600 config.json`
- Consider using Proxmox ACLs for granular permissions

### VM/Container Security

- Validate all resource allocations
- Check for resource exhaustion attacks
- Monitor unusual creation patterns
- Log all destructive operations
- Implement rate limiting for operations

### Network Security

```python
# Validate network configurations
# - Check VLAN tags are valid
# - Verify bridge exists
# - Prevent network isolation attacks
# - Validate firewall rules

def validate_network_config(config: dict) -> bool:
    """Validate network configuration."""
    if "bridge" in config:
        if not bridge_exists(config["bridge"]):
            raise ValueError("Bridge not found")
    
    if "tag" in config:
        if not (1 <= config["tag"] <= 4094):
            raise ValueError("Invalid VLAN tag")
    
    return True
```

## Dependencies

### Core Dependencies

- `requests` - HTTP client for Proxmox API
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

## Docker & Kubernetes Deployment

Proxmox MCP supports containerized deployment:

```bash
# Build image
cd proxmox-mcp
docker build -f docker/Dockerfile -t proxmox-mcp .

# Run container
docker run -v $(pwd)/config.json:/app/config.json proxmox-mcp

# Using Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Kubernetes
kubectl apply -f k8s/
kubectl get pods -l app=proxmox-mcp
```

## Protocol Implementation

### JSON-RPC Message Format

```python
# Request
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_vm_status",
        "arguments": {"vmid": 100}
    },
    "id": 1
}

# Success Response
{
    "jsonrpc": "2.0",
    "result": {
        "content": [
            {"type": "text", "text": '{"status": "running", "uptime": 86400}'}
        ]
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

# Log API calls
debug_print(f"API call: {method} {endpoint}")
debug_print(f"Response: {response.status_code}")
```

## Troubleshooting

### Cannot Connect to Proxmox

1. Verify Proxmox is reachable: `ping $PROXMOX_HOST`
2. Check Proxmox web interface is accessible
3. Verify credentials are correct
4. Check port 8006 is open
5. Ensure SSL certificate is valid (or use verify_ssl: false)
6. Check firewall rules

### VM/Container Operations Failing

1. Check VMID is valid and unique
2. Verify node has sufficient resources
3. Check storage is available
4. Review Proxmox task log for details
5. Ensure no locks on resources
6. Verify user permissions

### Authentication Failures

1. Verify username includes realm (e.g., root@pam)
2. Check password is correct
3. Ensure account is not locked
4. Verify account has necessary permissions
5. Check ticket hasn't expired
6. Review Proxmox authentication logs

### Cluster Operations Issues

1. Verify cluster is healthy: `pvecm status`
2. Check all nodes are online
3. Verify quorum is present
4. Check network connectivity between nodes
5. Review cluster logs
6. Ensure time is synchronized (NTP)

## Proxmox API Specifics

### API Versioning

- Proxmox API version varies by PVE version
- Check version: `GET /api2/json/version`
- Some features require specific versions
- Test with your Proxmox version

### Task Management

```python
# Long-running operations return task UPID
# Poll task status for completion
def wait_for_task(upid: str, timeout: int = 300) -> dict:
    """Wait for task completion."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = api.get_task_status(node, upid)
        if status["status"] == "stopped":
            if status.get("exitstatus") == "OK":
                return {"status": "success"}
            else:
                raise Exception(f"Task failed: {status}")
        time.sleep(2)
    raise TimeoutError("Task timeout")
```

### Resource Allocation

```python
# Check resources before allocation
def check_resources(node: str, memory: int, cores: int) -> bool:
    """Verify node has sufficient resources."""
    node_status = api.get_node_status(node)
    
    available_memory = node_status["memory"]["free"]
    if memory * 1024 * 1024 > available_memory:
        raise ValueError("Insufficient memory")
    
    available_cores = node_status["cpuinfo"]["cpus"]
    if cores > available_cores:
        raise ValueError("Insufficient CPU cores")
    
    return True
```

## Related Documentation

- [Proxmox MCP README](../proxmox-mcp/README.md)
- [Proxmox MCP SECURITY](../proxmox-mcp/SECURITY.md)
- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/)
- [Proxmox API Documentation](https://pve.proxmox.com/pve-docs/api-viewer/)
- [Main Repository README](../README.md)

## Notes

- This manages production virtualization infrastructure - test thoroughly
- VM/Container operations affect running workloads
- Deletion is permanent - implement confirmation
- Resource allocation affects cluster capacity
- Keep Proxmox updated for security and features
- Monitor resource usage and capacity
- Implement backup strategy for VMs/Containers
- Document your VM inventory and dependencies
