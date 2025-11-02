# Code Quality Standards

This document outlines the code quality standards and tools used in the Damen's MCP Servers collection.

## Overview

All projects in this repository follow consistent code quality standards enforced through automated checks in CI/CD and pre-commit hooks.

## Tools

### 1. Code Formatting

#### Black
- **Purpose**: Automatic Python code formatting
- **Configuration**: Line length of 120 characters
- **Usage**: 
  ```bash
  black src/ tests/ --line-length=120
  ```
- **Check only**: 
  ```bash
  black --check src/ tests/ --line-length=120
  ```

#### isort
- **Purpose**: Import statement sorting and organization
- **Configuration**: Black-compatible profile, 120 character line length
- **Usage**: 
  ```bash
  isort src/ tests/ --profile black --line-length=120
  ```
- **Check only**: 
  ```bash
  isort --check-only src/ tests/ --profile black --line-length=120
  ```

### 2. Linting

#### Flake8
- **Purpose**: PEP 8 style guide enforcement
- **Configuration**: 
  - Max line length: 120
  - Ignored codes: E203 (whitespace before ':'), W503 (line break before binary operator)
- **Usage**: 
  ```bash
  flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503
  ```

#### Pylint
- **Purpose**: Comprehensive Python code analysis
- **Usage**: 
  ```bash
  pylint src/ tests/
  ```

### 3. Type Checking

#### mypy
- **Purpose**: Static type checking
- **Configuration**: 
  - Ignore missing imports
  - No strict optional checking
- **Usage**: 
  ```bash
  mypy src/ --ignore-missing-imports --no-strict-optional
  ```

### 4. Security

#### Bandit
- **Purpose**: Security vulnerability scanning
- **Configuration**: Low-low severity threshold (-ll)
- **Usage**: 
  ```bash
  bandit -r src/ -ll
  ```
- **Note**: Tests directory is excluded from security scans

#### Safety
- **Purpose**: Dependency vulnerability checking
- **Usage**: 
  ```bash
  safety check
  ```

### 5. Documentation

#### Interrogate
- **Purpose**: Documentation coverage measurement
- **Configuration**: Minimum 40% documentation coverage
- **Usage**: 
  ```bash
  interrogate src/ -vv --fail-under=40
  ```

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit. To use them:

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install
```

### Manual Execution

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files src/module.py
```

### Hooks Included

1. **black** - Code formatting
2. **isort** - Import sorting
3. **flake8** - Linting
4. **mypy** - Type checking
5. **bandit** - Security scanning
6. **trailing-whitespace** - Remove trailing whitespace
7. **end-of-file-fixer** - Ensure files end with newline
8. **check-yaml** - Validate YAML files
9. **check-json** - Validate JSON files
10. **check-toml** - Validate TOML files
11. **check-merge-conflict** - Detect merge conflicts
12. **detect-private-key** - Prevent committing private keys
13. **check-added-large-files** - Prevent large file commits

## CI/CD Integration

### GitHub Actions Workflows

#### Test Workflow (`.github/workflows/test.yml`)
- Runs pytest with coverage
- Uploads coverage to Codecov
- Runs on push and pull requests to main/develop branches

#### Code Quality Workflow (`.github/workflows/code-quality.yml`)
- Runs all code quality checks
- Separate jobs for each project (pfSense, TrueNAS, iDRAC, Proxmox)
- Currently set to `continue-on-error: true` for gradual adoption
- Runs on push and pull requests to main/develop branches

### Quality Checks per Project

Each project runs:
1. ✅ Format check (black)
2. ✅ Import sort check (isort)
3. ✅ Linting (flake8)
4. ✅ Type checking (mypy)
5. ✅ Security scan (bandit)
6. ✅ Dependency scan (safety)
7. ✅ Documentation coverage (interrogate)

## Standards and Best Practices

### Code Style

1. **Line Length**: Maximum 120 characters
2. **Imports**: Organized with isort, grouped by standard library, third-party, and local
3. **Formatting**: Consistent with Black code style
4. **Type Hints**: Use type annotations for function parameters and returns
5. **Docstrings**: Follow Google or NumPy docstring style

### Security

1. **No Hardcoded Credentials**: Use environment variables or config files
2. **Input Validation**: Validate all user inputs and API parameters
3. **Error Handling**: Comprehensive exception handling with meaningful messages
4. **Dependency Updates**: Regular security updates via Dependabot

### Documentation

1. **Module Docstrings**: Every module should have a docstring
2. **Function Docstrings**: All public functions should be documented
3. **Class Docstrings**: All classes should have descriptive docstrings
4. **Inline Comments**: Use sparingly, only when code is not self-explanatory
5. **README**: Each project has comprehensive README documentation

## Running Quality Checks Locally

### Individual Project

```bash
# Navigate to project
cd pfsense-mcp  # or truenas-mcp, idrac-mcp, proxmox-mcp

# Install quality tools
pip install flake8 black isort mypy bandit safety interrogate

# Run all checks
black --check src/ tests/ --line-length=120
isort --check-only src/ tests/ --profile black --line-length=120
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503
mypy src/ --ignore-missing-imports --no-strict-optional
bandit -r src/ -ll
safety check
interrogate src/ -vv --fail-under=40
```

### All Projects

Use the provided convenience script to run all checks on all projects:

```bash
# Run all checks on all projects
./run_code_quality_checks.sh
```

This script will:
- Run all 7 quality checks on each project
- Create virtual environments if needed
- Install required dependencies
- Report any issues found
- Continue even if checks find issues (warnings only)

## Gradual Adoption

The code quality checks are currently configured with `continue-on-error: true` to allow gradual adoption:

1. **Phase 1 (Current)**: All checks run but don't fail the build
2. **Phase 2**: Enable specific checks to fail the build (formatting, security)
3. **Phase 3**: Enable all checks to fail the build

## Configuration Files

### Project-level Configuration

Some tools can be configured via project files:

- **setup.cfg** or **pyproject.toml**: Configure flake8, mypy, isort, black
- **.flake8**: Flake8-specific configuration
- **mypy.ini**: mypy-specific configuration

### Example pyproject.toml

```toml
[tool.black]
line-length = 120
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 120

[tool.mypy]
ignore_missing_imports = true
no_strict_optional = true
```

## Troubleshooting

### Common Issues

1. **Black and Flake8 conflicts**: Use `--extend-ignore=E203,W503` in flake8
2. **Import order issues**: Run `isort src/ tests/` to auto-fix
3. **Type checking errors**: Add `# type: ignore` comments for specific lines
4. **Security false positives**: Use `# nosec` comments with justification

### Getting Help

- Check tool documentation: Run `<tool> --help`
- Review configuration in `.pre-commit-config.yaml`
- Check CI/CD logs for detailed error messages
- Consult project-specific documentation

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)

## Contributing

When contributing to this repository:

1. Install pre-commit hooks: `pre-commit install`
2. Run quality checks before committing
3. Fix any issues identified by the checks
4. Ensure CI/CD passes before requesting review
5. Follow the code quality standards outlined in this document

## Updates and Changes

This document and the associated tools are periodically reviewed and updated. Check the commit history for recent changes to code quality standards.
