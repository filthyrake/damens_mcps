# GitHub Copilot Custom Agents

This directory contains custom agent profiles for GitHub Copilot. These agents provide specialized expertise for specific tasks in the repository.

## What are Custom Agents?

Custom agents are specialized AI assistants with domain-specific knowledge and guidelines. When you're working on a task that matches an agent's expertise, GitHub Copilot can leverage these profiles to provide more accurate and context-aware assistance.

## Available Agents

### [Python MCP Server Expert](./python-mcp-expert.md)
**Expertise:** Python development, MCP implementation, API integration  
**Use for:**
- Writing or modifying Python code for MCP servers
- Implementing async/await patterns
- API client development
- Error handling and validation

### [Documentation Expert](./documentation-expert.md)
**Expertise:** Technical writing, documentation structure, API docs  
**Use for:**
- Writing or updating README files
- Creating API documentation
- Writing code examples
- Improving documentation clarity

### [Security Expert](./security-expert.md)
**Expertise:** Security review, secure coding, vulnerability assessment  
**Use for:**
- Reviewing code for security issues
- Implementing input validation
- Managing credentials and secrets
- Security best practices

### [Testing Expert](./testing-expert.md)
**Expertise:** Test-driven development, pytest, coverage  
**Use for:**
- Writing unit tests
- Creating test fixtures
- Improving test coverage
- Mocking and async testing

## How to Use Agents

When working on a task:

1. **Identify the task type** - Is it coding, documentation, security, or testing?
2. **Reference the relevant agent** - Copilot may automatically select the appropriate agent
3. **Follow agent guidelines** - Each agent has specific patterns and best practices
4. **Iterate based on feedback** - Agents provide context-aware suggestions

## Agent Guidelines

Each agent file contains:

- **Agent Profile** - Name, expertise, and focus areas
- **Specialization** - Detailed knowledge domain
- **Behavioral Guidelines** - How to approach tasks
- **Code Patterns** - Examples and templates
- **Best Practices** - Do's and don'ts
- **Resources** - Links to relevant documentation

## Creating New Agents

To add a new custom agent:

1. Create a new `.md` file in this directory
2. Follow the structure of existing agents
3. Include clear expertise areas and guidelines
4. Provide code examples and patterns
5. Link to relevant resources
6. Update this README with the new agent

## Related Files

- [`.github/copilot-instructions.md`](../copilot-instructions.md) - Repository-wide Copilot instructions
- [`.github/instructions/`](../instructions/) - Path-specific instructions for each project
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) - General contribution guidelines

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Custom Instructions Guide](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions)
- [Best Practices](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
