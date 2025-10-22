# Contributing to iDRAC MCP Server

Thank you for your interest in contributing to the iDRAC MCP Server! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Security](#security)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards other contributors

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Dell PowerEdge server with iDRAC 8+ (for testing)
- Basic understanding of Model Context Protocol (MCP)

### Finding Issues to Work On

- Check the [issue tracker](../../issues) for open issues
- Look for issues labeled `good-first-issue` for beginner-friendly tasks
- Issues labeled `help-wanted` are particularly suitable for contributions
- Feel free to propose new features by opening an issue first

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/damens_mcps.git
cd damens_mcps/idrac-mcp
```

### 2. Create Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install pytest black isort flake8 mypy
```

### 4. Configure Environment

```bash
# Copy example configuration
cp config.example.json config.json

# Edit config.json with your iDRAC connection details
nano config.json
```

### 5. Verify Setup

```bash
# Test the server
python test_server.py

# Run unit tests (if available)
pytest
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with the following specifics:

**Formatting**
- **Line length:** 100 characters maximum (120 for comments/docstrings)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Use double quotes `"` for strings, single quotes `'` for dict keys when beneficial
- **Imports:** Group and sort imports (stdlib, third-party, local)

**Code Formatting Tools**
```bash
# Format code with black
black src/ examples/ --line-length 100

# Sort imports with isort
isort src/ examples/

# Check style with flake8
flake8 src/ examples/ --max-line-length=100
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Any, Dict, List, Optional

def get_system_info(self, include_details: bool = False) -> Dict[str, Any]:
    """Get system information.
    
    Args:
        include_details: Include detailed system information
        
    Returns:
        Dictionary containing system information
    """
    pass
```

### Docstrings

Use **Google-style docstrings** for all public functions, classes, and modules:

```python
def create_firewall_rule(
    self,
    action: str,
    interface: str,
    source: str,
    destination: str,
    port: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new firewall rule.
    
    Creates a firewall rule with the specified parameters. The rule is
    added to the pfSense configuration and must be applied to take effect.
    
    Args:
        action: Rule action ('pass', 'block', 'reject')
        interface: Network interface name (e.g., 'wan', 'lan')
        source: Source address or network (e.g., 'any', '192.168.1.0/24')
        destination: Destination address or network
        port: Optional destination port number
        
    Returns:
        Dict containing rule creation result:
            - rule_id: Unique identifier for the created rule
            - status: Creation status ('success' or 'error')
            - message: Human-readable status message
            
    Raises:
        ValueError: If action or interface is invalid
        PfSenseAPIError: If pfSense API returns an error
        
    Example:
        >>> result = client.create_firewall_rule(
        ...     action='pass',
        ...     interface='wan',
        ...     source='any',
        ...     destination='192.168.1.100',
        ...     port=80
        ... )
        >>> print(result['rule_id'])
        'rule_123'
    """
    pass
```

### Naming Conventions

- **Functions/Methods:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`
- **Module-level private:** `_single_leading_underscore`

### Error Handling

Always provide informative error messages:

```python
try:
    result = self._make_api_request(endpoint)
except requests.exceptions.Timeout:
    raise PfSenseAPIError(
        f"Request to {endpoint} timed out after {self.timeout}s. "
        "Check network connectivity and pfSense responsiveness."
    )
except requests.exceptions.SSLError as e:
    raise PfSenseAPIError(
        f"SSL verification failed: {e}. "
        "Set PFSENSE_SSL_VERIFY=false for self-signed certificates."
    )
```

## Testing Guidelines

### Writing Tests

Create test files in `tests/` directory:

```bash
tests/
├── test_client.py
├── test_server.py
├── test_validation.py
└── conftest.py  # pytest configuration
```

**Test Structure**
```python
import pytest
from src.pfsense_client import HTTPPfSenseClient

class TestHTTPPfSenseClient:
    """Tests for HTTPPfSenseClient class."""
    
    def test_connection_success(self, mock_pfsense):
        """Test successful connection to pfSense."""
        client = HTTPPfSenseClient(mock_pfsense.config)
        result = client.test_connection()
        assert result['status'] == 'success'
    
    def test_invalid_credentials(self, mock_pfsense):
        """Test handling of invalid credentials."""
        mock_pfsense.set_auth_fail()
        client = HTTPPfSenseClient(mock_pfsense.config)
        
        with pytest.raises(PfSenseAPIError) as exc_info:
            client.test_connection()
        
        assert 'authentication failed' in str(exc_info.value).lower()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::TestHTTPPfSenseClient::test_connection_success

# Run with verbose output
pytest -v
```

### Test Coverage

- Aim for **at least 80% code coverage**
- All new features must include tests
- Bug fixes should include regression tests
- Test edge cases and error conditions

## Submitting Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-dhcp-management` - New features
- `fix/ssl-verification-error` - Bug fixes
- `docs/improve-readme` - Documentation updates
- `refactor/simplify-client-init` - Code refactoring
- `test/add-validation-tests` - Test additions

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(firewall): add support for firewall rule groups

Implements firewall rule group management including create, update,
and delete operations. Groups allow organizing related rules.

Closes #123
```

```
fix(ssl): handle self-signed certificates correctly

The SSL verification was failing for self-signed certificates even
when PFSENSE_SSL_VERIFY was set to false. Updated the client to
properly respect this setting.

Fixes #456
```

### Pull Request Process

1. **Update your fork**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation
   - Ensure all tests pass

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create Pull Request**
   - Go to GitHub and create a pull request
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (run `black`, `isort`, `flake8`)
- [ ] Type hints are present and correct (`mypy`)
- [ ] All tests pass (`pytest`)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive information (passwords, API keys) in code
- [ ] CHANGELOG.md is updated (if applicable)

## Documentation

### Code Documentation

- **Public APIs:** Must have comprehensive docstrings
- **Complex logic:** Add inline comments explaining why, not what
- **Type hints:** Required for all function signatures
- **Examples:** Include usage examples in docstrings

### README Updates

When adding features, update README.md:

- Add tool to "Available Tools" table
- Include usage example
- Document any new configuration options
- Update troubleshooting if needed

### API Documentation

For new tools, document in README:

```markdown
| Tool | Description | Parameters |
|------|-------------|------------|
| `new_tool_name` | What it does | `param1`, `param2` |
```

## Security

### Security Considerations

- **Never commit sensitive data** (passwords, API keys, tokens)
- **Validate all inputs** before processing
- **Sanitize error messages** - don't expose internal details
- **Use parameterized queries** to prevent injection
- **Follow principle of least privilege**

### Reporting Security Issues

**Do NOT open public issues for security vulnerabilities.**

Instead:
1. Email security concerns to the maintainers (see README)
2. Provide detailed description of the vulnerability
3. Include steps to reproduce
4. Wait for acknowledgment before public disclosure

### Security Testing

- Test authentication and authorization
- Verify input validation works
- Check for information leakage in errors
- Test SSL/TLS configuration
- Validate credential handling

## Questions?

- Check [existing issues](../../issues)
- Review [README.md](README.md)
- Examine existing code for examples
- Open a discussion on GitHub

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to iDRAC MCP Server!** 🎉
