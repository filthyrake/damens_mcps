# Contributing to Damen's MCP Servers Collection

Thank you for your interest in contributing to this collection of Model Context Protocol (MCP) servers! This document provides guidelines for contributing to the repository as a whole.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [Contributing to Multiple Projects](#contributing-to-multiple-projects)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Security](#security)

## Code of Conduct

### Our Standards

- **Be respectful and inclusive** of differing viewpoints and experiences
- **Provide constructive feedback** and be open to receiving it
- **Focus on what's best** for the community and the projects
- **Show empathy** towards other community members
- **Collaborate openly** and transparently

### Unacceptable Behavior

- Harassment, discriminatory comments, or personal attacks
- Trolling, insulting/derogatory comments, or spam
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- **Python 3.8+** for all projects
- **Git** for version control
- **Virtual environment** knowledge (required for all Python development)
- **Network access** to infrastructure systems for testing
- **API credentials** for the platforms you want to work with

### Finding Issues to Work On

1. Browse the [issue tracker](../../issues) for open issues
2. Look for labels:
   - `good-first-issue` - Great for newcomers
   - `help-wanted` - Contributions especially welcome
   - `bug` - Bug fixes needed
   - `enhancement` - New features or improvements
3. Check individual project directories for project-specific issues
4. Feel free to propose new features by opening an issue first

## Repository Structure

```
damens_mcps/
├── pfsense-mcp/      # Firewall and network management
├── truenas-mcp/      # Storage and NAS management
├── idrac-mcp/        # Dell server management
├── proxmox-mcp/      # Virtualization platform management
├── .github/          # GitHub configuration and workflows
├── CONTRIBUTING.md   # This file
├── SECURITY.md       # Security policy
├── LICENSE           # MIT License
└── README.md         # Main documentation
```

Each project has its own:
- `CONTRIBUTING.md` - Project-specific contribution guidelines
- `SECURITY.md` - Project-specific security considerations
- `README.md` - Project documentation
- `tests/` - Test suite
- `examples/` - Usage examples

## Contributing to Multiple Projects

### Single Project Contributions

If you're contributing to just one project:

1. Navigate to the project directory (e.g., `cd pfsense-mcp`)
2. Read that project's `CONTRIBUTING.md` for specific guidelines
3. Follow the project-specific development workflow
4. Test changes within that project's context

### Multi-Project Contributions

If your contribution affects multiple projects:

1. **Documentation Changes**: Update all affected project READMEs
2. **Common Patterns**: Ensure consistency across projects
3. **Testing**: Test changes in each affected project
4. **Coordination**: Mention all affected projects in your PR

### Cross-Project Best Practices

- **Consistency**: Follow similar patterns across projects where possible
- **Documentation**: Keep documentation synchronized
- **Testing**: Maintain similar test coverage standards
- **Security**: Apply security best practices uniformly

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/damens_mcps.git
cd damens_mcps
```

### 2. Choose Your Project

```bash
# Navigate to the project you want to work on
cd pfsense-mcp    # or truenas-mcp, idrac-mcp, proxmox-mcp
```

### 3. Set Up Virtual Environment

**ALWAYS use virtual environments** - never install packages globally:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 4. Configure Environment

```bash
# Copy example configuration
cp env.example .env  # or config.example.json to config.json

# Edit with your credentials (never commit these!)
nano .env
```

### 5. Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install
```

### 6. Verify Setup

```bash
# Run tests to verify setup
pytest tests/ -v

# Try running the server
python -m src.server  # Command varies by project
```

## Coding Standards

All projects follow these standards. For comprehensive details, see [CODE_QUALITY.md](CODE_QUALITY.md).

### Python Style

- **PEP 8** compliance with 120-character line length
- **Type hints** required for all function signatures
- **Docstrings** required for all public APIs (Google-style)
- **Naming conventions**:
  - Functions/methods: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: `_leading_underscore`

### Code Quality Tools

We use automated code quality tools (enforced via pre-commit hooks and CI/CD):

```bash
# Install quality tools
pip install flake8 black isort mypy bandit safety pylint interrogate

# Format code
black src/ tests/ --line-length=120
isort src/ tests/ --profile black --line-length=120

# Check style
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503

# Type checking
mypy src/ --ignore-missing-imports --no-strict-optional

# Security scan
bandit -r src/ -ll

# Check dependencies
safety check
```

See [CODE_QUALITY.md](CODE_QUALITY.md) for complete documentation.

### Security Requirements

- **Input validation** for all user inputs
- **No hardcoded credentials** in code
- **Parameterized queries** to prevent injection
- **Error messages** should not expose sensitive information
- **Use HTTPS** for all API communications

## Testing Requirements

### Test Coverage

- **All new features** must include tests
- **Bug fixes** should include regression tests
- **Aim for 80%+ coverage** on new code
- **Test edge cases** and error conditions

### Running Tests

```bash
# Run all tests for a project
cd <project-name>
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v
```

### Test Organization

```
tests/
├── test_client.py          # API client tests
├── test_server.py          # MCP server tests
├── test_validation.py      # Input validation tests
└── conftest.py             # Shared fixtures
```

### CI/CD

All tests run automatically on:
- Every push to the repository
- Every pull request
- Tests must pass before merging

## Pull Request Process

### Branch Naming

Use descriptive branch names:

- `feature/add-<feature-name>` - New features
- `fix/<bug-description>` - Bug fixes
- `docs/<what-changed>` - Documentation updates
- `refactor/<what-refactored>` - Code refactoring
- `test/<what-tested>` - Test additions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(pfsense): add firewall rule grouping support

Implements firewall rule group management with create, update,
and delete operations. Groups help organize related rules.

Closes #123
```

### Pull Request Checklist

Before submitting your PR:

- [ ] Code follows style guidelines
- [ ] Type hints are present and correct
- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive information in code
- [ ] Project-specific CONTRIBUTING.md guidelines followed
- [ ] Security implications considered

### PR Template

When you create a PR, fill out the template with:
- Description of changes
- Motivation and context
- Type of change (bug fix, feature, etc.)
- Testing performed
- Checklist completion

### Review Process

1. **Automated checks** run first (tests, linting)
2. **Maintainer review** of code and approach
3. **Feedback and iteration** as needed
4. **Approval and merge** when ready

## Security

### Security First

- **Never commit credentials** (use `.gitignore`)
- **Validate all inputs** before processing
- **Report vulnerabilities** privately (see [SECURITY.md](SECURITY.md))
- **Follow security best practices** in each project's SECURITY.md

### Reporting Security Issues

**Do NOT open public issues for security vulnerabilities.**

Instead:
1. Review our [Security Policy](SECURITY.md)
2. Report vulnerabilities privately as described there
3. Allow time for fixes before public disclosure

## Project-Specific Guidelines

Each project has additional specific guidelines in its own `CONTRIBUTING.md`:

- **[pfSense MCP](pfsense-mcp/CONTRIBUTING.md)** - Firewall management specifics
- **[TrueNAS MCP](truenas-mcp/CONTRIBUTING.md)** - Storage management specifics
- **[iDRAC MCP](idrac-mcp/CONTRIBUTING.md)** - Server management specifics
- **[Proxmox MCP](proxmox-mcp/CONTRIBUTING.md)** - Virtualization specifics

**Always read the project-specific CONTRIBUTING.md** for the project you're working on.

## Questions and Support

- **Questions?** Open a [discussion](../../discussions) on GitHub
- **Issues?** Check the [issue tracker](../../issues)
- **Chat?** Join our community (see README for links)

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see [LICENSE](LICENSE)).

---

**Thank you for contributing to Damen's MCP Servers Collection!** 🎉

Your contributions help make infrastructure management more accessible and automated for everyone.
