# GitHub Copilot Quick Reference

Quick reference guide for using GitHub Copilot with this repository.

## 📁 File Locations

```
.github/
├── copilot-instructions.md           # General repository guidance
├── COPILOT_SETUP.md                  # This setup documentation
├── agents/                           # Expert agent profiles
│   ├── python-mcp-expert.md         # Python & MCP development
│   ├── documentation-expert.md      # Technical writing
│   ├── security-expert.md           # Security review
│   └── testing-expert.md            # Testing & QA
└── instructions/                     # Project-specific guidance
    ├── pfsense-mcp.instructions.md  # pfSense firewall
    ├── truenas-mcp.instructions.md  # TrueNAS storage
    ├── idrac-mcp.instructions.md    # Dell iDRAC
    └── proxmox-mcp.instructions.md  # Proxmox VE
```

## 🚀 Quick Start

### Working on Python Code
→ **Python MCP Expert** agent automatically assists  
→ Follow patterns in copilot-instructions.md  
→ Path-specific instructions apply when in project directory

### Writing Documentation
→ **Documentation Expert** agent provides guidance  
→ Use templates and examples from the agent file  
→ Follow documentation structure standards

### Security Review
→ **Security Expert** agent checks for vulnerabilities  
→ Review input validation patterns  
→ Check credential management practices

### Writing Tests
→ **Testing Expert** agent helps with test structure  
→ Use pytest patterns and fixtures  
→ Aim for coverage goals in instructions

## 🎯 Common Scenarios

### Scenario: Adding a new tool to pfSense MCP

1. Navigate to `pfsense-mcp/src/`
2. Copilot applies pfSense instructions automatically
3. Python MCP Expert helps with code structure
4. Add tool definition and handler
5. Testing Expert helps write tests
6. Security Expert reviews for issues

**Key Files:**
- Instructions: `.github/instructions/pfsense-mcp.instructions.md`
- Agent: `.github/agents/python-mcp-expert.md`

### Scenario: Fixing a security vulnerability

1. Security Expert agent provides guidance
2. Review security patterns in agent file
3. Implement input validation improvements
4. Add security tests
5. Document the fix

**Key Files:**
- Agent: `.github/agents/security-expert.md`
- General: `.github/copilot-instructions.md` (Security section)

### Scenario: Improving test coverage

1. Testing Expert agent assists
2. Review test organization patterns
3. Add missing test cases
4. Run coverage report
5. Document test approach

**Key Files:**
- Agent: `.github/agents/testing-expert.md`
- General: `.github/copilot-instructions.md` (Testing section)

### Scenario: Updating documentation

1. Documentation Expert agent guides writing
2. Follow structure templates
3. Include code examples
4. Cross-reference related docs
5. Verify links work

**Key Files:**
- Agent: `.github/agents/documentation-expert.md`
- Project READMEs in each directory

## 🔑 Key Patterns

### Python MCP Servers

```python
# Tool definition
Tool(
    name="action_name",
    description="Clear description",
    inputSchema={...}
)

# Handler implementation
async def handler(self, param: str) -> Dict[str, Any]:
    # Validate input
    # Perform action
    # Return result
    return {"status": "success", "data": result}
```

### Input Validation

```python
# Always validate inputs
if not isinstance(param, str):
    raise TypeError("param must be string")

if not param:
    raise ValueError("param is required")

if not re.match(VALID_PATTERN, param):
    raise ValueError("param has invalid format")
```

### Error Handling

```python
try:
    result = await api_call()
except ConnectionError:
    logger.error("Connection failed")
    return {"error": "Service unavailable"}
except Exception as e:
    logger.error(f"Error: {type(e).__name__}")
    return {"error": "Internal error"}
```

### Test Structure (AAA Pattern)

```python
async def test_feature():
    # Arrange - Set up test data
    mock_client = MockClient()
    handler = Handler(mock_client)
    
    # Act - Execute code
    result = await handler.action()
    
    # Assert - Verify results
    assert result["status"] == "success"
```

## 🛠️ Development Commands

### Setup
```bash
cd <project-name>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Testing
```bash
pytest tests/ -v                    # Run tests
pytest tests/ --cov=src            # With coverage
pytest tests/test_validation.py    # Specific test
```

### Code Quality
```bash
black src/ tests/ --line-length=120
isort src/ tests/ --profile black
flake8 src/ tests/ --max-line-length=120
mypy src/ --ignore-missing-imports
bandit -r src/ -ll
```

### Running Servers
```bash
# TrueNAS
python -m src.http_cli serve

# pfSense
python -m src.http_pfsense_server

# iDRAC (ONLY this file)
python working_mcp_server.py

# Proxmox (ONLY this file)
python working_proxmox_server.py
```

## ⚠️ Critical Safety Rules

### Never Commit
- `.env` files with credentials
- `config.json` with passwords
- API keys or tokens
- SSL certificates or private keys

### Always Validate
- User inputs before processing
- Server/VM/Dataset IDs before operations
- Resource availability before allocation
- Permissions before destructive operations

### Dangerous Operations
- **Power off/reset** (iDRAC) - Can cause downtime
- **Delete datasets** (TrueNAS) - Permanent data loss
- **Firewall rules** (pfSense) - Can block access
- **VM deletion** (Proxmox) - Cannot be undone

### Security Checks
```python
# Before destructive operations
if is_system_resource(resource_id):
    raise ValueError("Cannot delete system resource")

if not has_permission(user, action, resource):
    raise PermissionError("Not authorized")

logger.warning(f"DESTRUCTIVE: {action} on {resource_id}")
```

## 📚 References

### Documentation
- [Repository README](../README.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Security Policy](../SECURITY.md)
- [Testing Guide](../TESTING.md)

### Project-Specific
- [pfSense README](../pfsense-mcp/README.md)
- [TrueNAS README](../truenas-mcp/README.md)
- [iDRAC README](../idrac-mcp/README.md)
- [Proxmox README](../proxmox-mcp/README.md)

### Copilot Setup
- [Setup Documentation](./COPILOT_SETUP.md)
- [Agents Directory](./agents/README.md)
- [Instructions Directory](./instructions/README.md)

## 💡 Tips

1. **Read instructions first** - Understand patterns before coding
2. **Trust the agents** - They have specialized knowledge
3. **Validate suggestions** - Always test Copilot's code
4. **Follow patterns** - Consistency improves quality
5. **Ask for help** - Open issues if something's unclear

## 🆘 Troubleshooting

### Copilot not using instructions?
- Ensure files are in `.github/` directory
- Check file naming matches conventions
- Verify files are valid markdown
- Try reopening your editor/IDE

### Instructions not applying to path?
- Check file name matches path pattern
- Verify you're in the correct directory
- File should be named `<project>.instructions.md`

### Agent not providing expected guidance?
- Ensure agent file is in `.github/agents/`
- Check agent profile matches your task
- Review agent's expertise areas
- Try being more specific in comments/prompts

---

**Quick Help:** For any issues, check [COPILOT_SETUP.md](./COPILOT_SETUP.md) or open an issue.
