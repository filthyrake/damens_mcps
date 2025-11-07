# GitHub Copilot Setup

This document explains the GitHub Copilot instructions setup for this repository.

## Overview

This repository is configured with comprehensive GitHub Copilot instructions following [best practices for Copilot coding agent](https://gh.io/copilot-coding-agent-tips). The setup provides context-aware assistance through:

1. **Repository-wide instructions** - General guidance for the entire repository
2. **Custom agents** - Specialized experts for specific types of work
3. **Path-specific instructions** - Detailed guidance for each MCP server project

## Structure

```
.github/
├── copilot-instructions.md       # Repository-wide instructions
├── agents/                        # Custom agent profiles
│   ├── README.md
│   ├── python-mcp-expert.md
│   ├── documentation-expert.md
│   ├── security-expert.md
│   └── testing-expert.md
└── instructions/                  # Path-specific instructions
    ├── README.md
    ├── pfsense-mcp.instructions.md
    ├── truenas-mcp.instructions.md
    ├── idrac-mcp.instructions.md
    └── proxmox-mcp.instructions.md
```

## How It Works

### Repository-Wide Instructions

**File:** `.github/copilot-instructions.md`

Provides general guidance for working anywhere in the repository:
- Project overview and structure
- Development environment setup
- Coding conventions and standards
- Build and test instructions
- Security requirements
- Common development tasks

### Custom Agents

**Directory:** `.github/agents/`

Specialized agent profiles that Copilot can leverage for specific tasks:

#### Python MCP Server Expert
- Python development patterns
- MCP protocol implementation
- Async/await best practices
- API client development

#### Documentation Expert
- Technical writing guidelines
- Documentation structure
- API documentation patterns
- Examples and templates

#### Security Expert
- Security review guidelines
- Input validation patterns
- Credential management
- Dangerous operation handling

#### Testing Expert
- Test organization and structure
- Pytest patterns and fixtures
- Coverage requirements
- Mocking strategies

### Path-Specific Instructions

**Directory:** `.github/instructions/`

Detailed guidance for each MCP server project:

Each instruction file includes:
- Project overview and architecture
- Critical requirements
- Configuration details
- Testing procedures
- Security considerations
- Common commands
- Troubleshooting guides

## For Contributors

### Using Copilot with This Setup

When you work on code:

1. **Copilot automatically applies** relevant instructions based on your location
2. **Custom agents** provide specialized expertise when needed
3. **Path-specific instructions** give context for the specific project

### Best Practices

1. **Read the instructions** - Familiarize yourself with the guidance
2. **Follow patterns** - Use the patterns described in instructions
3. **Trust the agents** - Custom agents have specialized knowledge
4. **Validate changes** - Always test and review Copilot suggestions

### Example Workflows

#### Adding a New Feature to pfSense MCP

1. Navigate to `pfsense-mcp/` directory
2. Copilot applies pfSense-specific instructions
3. Python MCP Expert agent provides coding patterns
4. Testing Expert helps write tests
5. Security Expert reviews for vulnerabilities

#### Writing Documentation

1. Open or create a documentation file
2. Documentation Expert agent provides guidance
3. Follow documentation structure templates
4. Use provided examples and patterns

#### Fixing a Security Issue

1. Security Expert agent reviews code
2. Provides secure coding patterns
3. Suggests input validation improvements
4. Helps implement safety checks

## For Maintainers

### Updating Instructions

When updating the repository:

1. **Repository-wide changes** → Update `.github/copilot-instructions.md`
2. **Agent expertise** → Update relevant agent file in `.github/agents/`
3. **Project-specific changes** → Update relevant instruction in `.github/instructions/`

### Adding New Agents

To add a new custom agent:

1. Create new `.md` file in `.github/agents/`
2. Follow existing agent structure
3. Include clear expertise areas
4. Provide code examples and patterns
5. Update `.github/agents/README.md`

### Adding New Path Instructions

To add instructions for a new project:

1. Create new `.instructions.md` file in `.github/instructions/`
2. Follow existing instruction structure
3. Include project-specific critical information
4. Add common commands and patterns
5. Update `.github/instructions/README.md`

## Benefits

### For Development

✅ **Consistent code** - Copilot follows repository conventions  
✅ **Better suggestions** - Context-aware based on location  
✅ **Specialized expertise** - Custom agents for specific tasks  
✅ **Security awareness** - Built-in security guidance  
✅ **Faster onboarding** - New contributors get context automatically

### For Code Quality

✅ **Pattern adherence** - Follows established patterns  
✅ **Best practices** - Applies project-specific best practices  
✅ **Error prevention** - Warns about dangerous operations  
✅ **Test coverage** - Encourages comprehensive testing  
✅ **Documentation** - Promotes good documentation practices

## Technical Details

### File Naming Conventions

- Repository-wide: `copilot-instructions.md`
- Custom agents: `<agent-name>.md` in `agents/`
- Path-specific: `<project-name>.instructions.md` in `instructions/`
- README files: `README.md` in each directory

### Content Structure

All instruction files follow markdown format with:
- Clear headings and sections
- Code examples with syntax highlighting
- Links to related documentation
- Practical guidelines and patterns

### Integration with CI/CD

The instructions complement CI/CD workflows:
- Pre-commit hooks enforce standards
- GitHub Actions run tests and quality checks
- Instructions guide Copilot to follow same standards

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Best Practices for Copilot Coding Agent](https://gh.io/copilot-coding-agent-tips)
- [Custom Instructions Guide](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions)
- [Repository CONTRIBUTING.md](../CONTRIBUTING.md)

## Feedback

If you have suggestions for improving these instructions:

1. Open an issue describing the improvement
2. Submit a pull request with changes
3. Discuss in the relevant issue

---

**Last Updated:** 2025-11-07  
**Maintained By:** Repository maintainers
