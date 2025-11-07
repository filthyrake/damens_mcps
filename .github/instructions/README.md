# Path-Specific Instructions

This directory contains path-specific instructions for GitHub Copilot. These instructions provide detailed guidance for working with specific parts of the repository.

## What are Path-Specific Instructions?

Path-specific instructions give GitHub Copilot context about specific directories or projects. When you're working in a particular path, Copilot uses these instructions to provide more accurate suggestions based on the project's architecture, conventions, and requirements.

## Available Instructions

### [pfSense MCP Server](./pfsense-mcp.instructions.md)
**Path:** `pfsense-mcp/`  
**Focus:** Firewall and network management  
**Key Points:**
- MCP library-based architecture
- HTTP transport with FastAPI
- Firewall rule validation critical
- Security-focused operations

### [TrueNAS MCP Server](./truenas-mcp.instructions.md)
**Path:** `truenas-mcp/`  
**Focus:** Storage and NAS management  
**Key Points:**
- MCP library-based architecture
- HTTP and stdio transport options
- Data loss prevention critical
- Storage operation safety

### [iDRAC MCP Server](./idrac-mcp.instructions.md)
**Path:** `idrac-mcp/`  
**Focus:** Dell server management  
**Key Points:**
- Pure JSON-RPC implementation
- Fleet management support
- Power operations dangerous
- Redfish API integration

### [Proxmox MCP Server](./proxmox-mcp.instructions.md)
**Path:** `proxmox-mcp/`  
**Focus:** Virtualization platform management  
**Key Points:**
- Pure JSON-RPC implementation
- VM/Container operations critical
- Ticket-based authentication
- Cluster-aware operations

## How Path Instructions Work

When you edit files in a specific path, GitHub Copilot automatically applies the relevant instructions. For example:

- Working in `pfsense-mcp/src/` → Uses pfSense instructions
- Editing `truenas-mcp/tests/` → Uses TrueNAS instructions
- Modifying `idrac-mcp/working_mcp_server.py` → Uses iDRAC instructions

## Instruction Structure

Each instruction file includes:

1. **Project Overview** - What the project does
2. **Key Characteristics** - Architecture and implementation details
3. **Critical Requirements** - Must-know information
4. **Configuration** - Setup and environment variables
5. **Testing** - How to run tests
6. **Development Commands** - Common tasks
7. **Security Considerations** - Safety and security
8. **Troubleshooting** - Common issues and solutions
9. **Related Documentation** - Links to more info

## Creating New Instructions

To add instructions for a new path:

1. Create a new `.instructions.md` file
2. Name it after the path (e.g., `project-name.instructions.md`)
3. Follow the structure of existing instructions
4. Include project-specific critical information
5. Add common commands and patterns
6. Document security considerations
7. Update this README

## Using Instructions Effectively

### For Contributors

When working on a project:

1. **Read the path instructions** before making changes
2. **Follow the patterns** described in the instructions
3. **Use the provided commands** for consistency
4. **Consult security sections** for dangerous operations
5. **Reference troubleshooting** when issues arise

### For Copilot

Path instructions help Copilot:

- Understand project architecture
- Use correct file paths and commands
- Apply appropriate coding patterns
- Recognize security-critical operations
- Suggest relevant error handling

## Best Practices

### Keep Instructions Updated

- Update when architecture changes
- Add new common patterns
- Document new security considerations
- Include new troubleshooting steps

### Be Specific

- Include exact file paths
- Provide complete commands
- Show actual code examples
- Link to relevant documentation

### Focus on Differences

- Highlight unique aspects of each project
- Explain why certain patterns are used
- Note security-critical operations
- Document project-specific conventions

## Related Files

- [`.github/copilot-instructions.md`](../copilot-instructions.md) - Repository-wide instructions
- [`.github/agents/`](../agents/) - Custom agent profiles
- Project-specific `README.md` files in each directory
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) - General contribution guidelines

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Repository Custom Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
- [Best Practices](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
