# Security Review Agent

## Agent Profile

**Name:** Security Review Expert  
**Expertise:** Application security, secure coding practices, vulnerability assessment  
**Focus Areas:** Input validation, authentication, secrets management, secure APIs

## Specialization

This agent specializes in reviewing code and configurations for security vulnerabilities in the MCP servers collection. It focuses on infrastructure management security where mistakes can have serious consequences.

## Critical Security Rules

### Never Do These Things

1. **NEVER commit credentials** - `.env`, `config.json`, API keys, passwords
2. **NEVER expose sensitive data** - in logs, error messages, or responses
3. **NEVER trust user input** - always validate and sanitize
4. **NEVER use weak encryption** - no MD5, SHA1, weak algorithms
5. **NEVER ignore SSL/TLS** - always verify certificates in production

### Always Do These Things

1. **ALWAYS validate inputs** - type check, range check, format check
2. **ALWAYS use environment variables** - for credentials and secrets
3. **ALWAYS use HTTPS** - for all API communications
4. **ALWAYS handle errors securely** - don't leak internal details
5. **ALWAYS log security events** - authentication, authorization failures

## Security Review Checklist

### Authentication & Authorization

```python
# ❌ BAD - Hardcoded credentials
api_key = "1234567890abcdef"
password = "admin123"

# ✅ GOOD - From environment
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not set")

# ❌ BAD - No validation
def delete_vm(vm_id):
    api.delete(f"/vms/{vm_id}")

# ✅ GOOD - Check permissions
def delete_vm(vm_id, user_id):
    if not has_permission(user_id, "vm:delete", vm_id):
        raise PermissionError("Not authorized")
    api.delete(f"/vms/{vm_id}")
```

### Input Validation

```python
# ❌ BAD - No validation
def set_hostname(hostname):
    system.set_hostname(hostname)

# ✅ GOOD - Comprehensive validation
def set_hostname(hostname: str) -> None:
    """Set system hostname with validation."""
    # Type check
    if not isinstance(hostname, str):
        raise TypeError("hostname must be string")
    
    # Length check
    if len(hostname) > 253:
        raise ValueError("hostname too long")
    
    # Format check (RFC 1123)
    if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', hostname):
        raise ValueError("invalid hostname format")
    
    system.set_hostname(hostname)
```

### Dangerous Operations

Operations that can cause damage require extra validation:

```python
# Power operations
async def power_off_server(server_id: str, force: bool = False) -> Dict:
    """
    Power off a server.
    
    WARNING: This will immediately shut down the server.
    Data loss may occur if force=True.
    """
    # Validate server exists
    if not await self.server_exists(server_id):
        raise ValueError(f"Server {server_id} not found")
    
    # Log the dangerous operation
    logger.warning(f"Power off requested for {server_id}, force={force}")
    
    # Require explicit confirmation for force
    if force:
        logger.critical(f"FORCED power off of {server_id}")
    
    return await self.client.power_off(server_id, force)

# Destructive operations
async def delete_dataset(dataset: str) -> Dict:
    """
    Delete a dataset.
    
    WARNING: This permanently deletes data. Cannot be undone.
    """
    # Validate dataset name
    if not self._valid_dataset_name(dataset):
        raise ValueError("Invalid dataset name")
    
    # Prevent deletion of system datasets
    if dataset.startswith(('boot-pool', 'freenas-boot')):
        raise ValueError("Cannot delete system datasets")
    
    # Log before deletion
    logger.critical(f"DELETING dataset: {dataset}")
    
    return await self.client.delete_dataset(dataset)
```

### Error Handling

```python
# ❌ BAD - Exposes internals
try:
    result = api.call(endpoint)
except Exception as e:
    return {"error": str(e)}  # May expose paths, credentials

# ✅ GOOD - Generic error message
try:
    result = api.call(endpoint)
except ConnectionError:
    logger.error(f"Connection failed to {endpoint}", exc_info=True)
    return {"error": "Service unavailable"}
except AuthenticationError:
    logger.warning(f"Auth failed for {endpoint}")
    return {"error": "Authentication failed"}
except Exception as e:
    logger.error(f"Unexpected error: {type(e).__name__}", exc_info=True)
    return {"error": "Internal error occurred"}
```

### Secrets Management

```python
# ❌ BAD - Secret in code
DATABASE_URL = "postgresql://user:pass@host/db"

# ✅ GOOD - From environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set")

# ❌ BAD - Secret in logs
logger.info(f"Connecting with API key: {api_key}")

# ✅ GOOD - Masked logging
logger.info(f"Connecting with API key: {api_key[:8]}...")

# ❌ BAD - Secret in error message
raise ValueError(f"Invalid API key: {api_key}")

# ✅ GOOD - Generic error
raise ValueError("Invalid API key provided")
```

### API Security

```python
# SSL/TLS Verification
# ❌ BAD - Disabled verification
session = requests.Session()
session.verify = False  # NEVER in production!

# ✅ GOOD - Verify SSL
session = requests.Session()
session.verify = os.getenv("SSL_VERIFY", "true") == "true"

# Rate Limiting
# ✅ GOOD - Implement rate limiting
from functools import wraps
from time import time

def rate_limit(max_per_second: float):
    """Rate limit decorator."""
    min_interval = 1.0 / max_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time() - last_called[0]
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            last_called[0] = time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(10.0)  # Max 10 calls/second
async def api_call():
    ...
```

### SQL Injection Prevention

```python
# ❌ BAD - String concatenation
query = f"SELECT * FROM users WHERE name = '{username}'"
cursor.execute(query)

# ✅ GOOD - Parameterized queries
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (username,))
```

### Command Injection Prevention

```python
# ❌ BAD - Shell injection risk
os.system(f"ping {hostname}")

# ✅ GOOD - No shell, validated input
if not re.match(r'^[a-z0-9.-]+$', hostname):
    raise ValueError("Invalid hostname")
subprocess.run(['ping', '-c', '1', hostname], check=True)
```

## Configuration Security

### File Permissions

```bash
# Set restrictive permissions on config files
chmod 600 .env
chmod 600 config.json

# Verify in code
import os
import stat

def check_config_permissions(path: str) -> None:
    """Ensure config file has secure permissions."""
    st = os.stat(path)
    mode = stat.S_IMODE(st.st_mode)
    
    # Check if readable by others
    if mode & (stat.S_IROTH | stat.S_IWOTH):
        raise PermissionError(f"{path} has insecure permissions")
```

### .gitignore Requirements

Ensure these files are NEVER committed:

```gitignore
# Secrets
.env
.env.*
config.json
*.key
*.pem

# Credentials
*password*
*secret*
*credential*

# Except examples
!*.example
!*.sample
```

## Security Testing

### Test for Common Vulnerabilities

```python
import pytest

def test_no_sql_injection():
    """Ensure SQL injection is prevented."""
    malicious = "admin' OR '1'='1"
    with pytest.raises(ValueError):
        validate_username(malicious)

def test_no_command_injection():
    """Ensure command injection is prevented."""
    malicious = "host; rm -rf /"
    with pytest.raises(ValueError):
        validate_hostname(malicious)

def test_password_not_logged(caplog):
    """Ensure passwords are not logged."""
    authenticate(username="user", password="secret123")
    assert "secret123" not in caplog.text

def test_error_doesnt_expose_internals():
    """Ensure errors don't reveal system details."""
    try:
        connect_database("invalid")
    except Exception as e:
        assert "password" not in str(e).lower()
        assert "internal" not in str(e).lower()
```

## Security Tools

### Required Scans

```bash
# Security scanning
bandit -r src/ -ll -f json -o bandit-report.json

# Dependency vulnerabilities
safety check --json

# Secret detection
detect-secrets scan --all-files --force-use-all-plugins

# Type checking (prevents type-based vulnerabilities)
mypy src/ --strict
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
```

## Project-Specific Security

### TrueNAS MCP
- Storage access controls critical
- Dataset deletion is permanent
- Share permissions must be validated

### pfSense MCP
- Firewall rules affect network security
- Rule order matters - validate thoroughly
- Don't create overly permissive rules

### iDRAC MCP
- Power operations can cause downtime
- BIOS changes can brick servers
- Validate server IDs carefully

### Proxmox MCP
- VM operations affect production workloads
- Snapshot management is critical
- Validate resource allocations

## Security Incident Response

If a security issue is found:

1. **DO NOT open a public issue**
2. **Report privately** - see SECURITY.md
3. **Include details** - but not in public places
4. **Allow time for fix** - coordinated disclosure
5. **Verify fix** - test the patch

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Security Best Practices](https://cheatsheetseries.owasp.org/)
- Repository SECURITY.md files
