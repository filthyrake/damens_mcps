# pfSense MCP Server Generation Prompt

**Task**: Create a comprehensive MCP (Model Context Protocol) server for pfSense firewall management, similar to the working TrueNAS MCP server we just completed.

## Key Requirements

### 1. **MCP Serialization Fix (CRITICAL)**
- **IMPORTANT**: Return dictionaries instead of `CallToolResult` objects to avoid serialization issues
- Use this pattern for all tool responses:
```python
return {
    "content": [{"type": "text", "text": result_text}],
    "isError": False
}
```
- Do NOT use `CallToolResult(content=[TextContent(...)])` as it causes tuple serialization errors

### 2. **Server Structure**
- Create an HTTP-based server using `aiohttp` for REST API calls to pfSense
- Use the same structure as the working TrueNAS server:
  - `HTTPPfSenseClient` class for API communication
  - `HTTPPfSenseMCPServer` class for MCP server logic
  - Proper async/await patterns
  - Environment variable configuration

### 3. **pfSense API Integration**
- Use pfSense's REST API (available in pfSense 2.5+)
- Implement authentication using API tokens or username/password
- Handle SSL certificate verification (pfSense uses HTTPS)
- Support both GET and POST requests for different operations

### 4. **Core pfSense Management Tools**

#### System Management
- `get_system_info` - Get pfSense version, uptime, system status
- `get_system_health` - Get system health, CPU, memory, disk usage
- `get_interfaces` - List all network interfaces and their status
- `get_services` - List running services (DNS, DHCP, etc.)

#### Firewall Management
- `get_firewall_rules` - List all firewall rules
- `create_firewall_rule` - Create new firewall rule
- `delete_firewall_rule` - Delete existing firewall rule
- `enable_firewall_rule` - Enable/disable firewall rule
- `get_firewall_logs` - Get recent firewall logs

#### Network Configuration
- `get_vlans` - List VLAN configurations
- `create_vlan` - Create new VLAN
- `delete_vlan` - Delete VLAN
- `get_dhcp_leases` - Get DHCP lease information
- `get_dns_servers` - Get DNS server configuration

#### Package Management
- `get_installed_packages` - List installed packages
- `install_package` - Install new package
- `remove_package` - Remove package
- `get_package_updates` - Check for available updates

#### VPN Management
- `get_vpn_status` - Get VPN connection status
- `get_openvpn_servers` - List OpenVPN server configurations
- `get_openvpn_clients` - List OpenVPN client configurations
- `restart_vpn_service` - Restart VPN service

#### Backup & Restore
- `create_backup` - Create system backup
- `restore_backup` - Restore from backup
- `get_backup_list` - List available backups

### 5. **Error Handling & Logging**
- Implement comprehensive error handling for API failures
- Use proper logging with different levels (INFO, ERROR, DEBUG)
- Handle network timeouts and connection issues
- Provide meaningful error messages

### 6. **Configuration Management**
- Support environment variables for configuration:
  - `PFSENSE_HOST` - pfSense hostname/IP
  - `PFSENSE_PORT` - Port (usually 443)
  - `PFSENSE_API_KEY` - API key for authentication
  - `PFSENSE_USERNAME` - Username (if using password auth)
  - `PFSENSE_PASSWORD` - Password (if using password auth)
  - `PFSENSE_SSL_VERIFY` - SSL verification (true/false)

### 7. **Code Quality Requirements**
- Follow Python best practices and PEP 8
- Use type hints throughout
- Include comprehensive docstrings
- Implement proper exception handling
- Use async/await patterns correctly
- Include input validation for all parameters

### 8. **Testing & Documentation**
- Create a simple test server for validation
- Include example configuration files
- Provide clear setup instructions
- Document all available tools and their parameters

### 9. **File Structure**
```
pfsense-mcp/
├── src/
│   ├── http_pfsense_server.py    # Main server file
│   ├── pfsense_client.py         # pfSense API client
│   ├── auth.py                   # Authentication handling
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── validation.py
├── examples/
│   ├── config.json.example
│   └── basic_usage.py
├── requirements.txt
├── README.md
└── .env.example
```

### 10. **MCP Configuration Files**
Create example MCP configuration files for:
- Claude Desktop: `~/.config/claude/mcp.json`
- Cursor: `~/.cursor/mcp.json`

### 11. **Lessons from TrueNAS Implementation**
- **Avoid CallToolResult objects** - use dictionaries instead
- **Test serialization thoroughly** before deployment
- **Use proper async patterns** for HTTP requests
- **Handle SSL certificates** properly for pfSense HTTPS
- **Implement proper error handling** for network issues
- **Use environment variables** for configuration

### 12. **pfSense-Specific Considerations**
- pfSense REST API requires authentication
- Some operations may require different API endpoints
- Handle pfSense's specific response formats
- Consider pfSense version compatibility
- Implement proper session management

## Expected Output
1. Complete working MCP server for pfSense
2. All core management tools implemented
3. Proper error handling and logging
4. Configuration examples
5. Setup documentation
6. Test files for validation

## Success Criteria
- MCP server connects successfully to pfSense
- All tools return proper responses (no serialization errors)
- Works with both Claude Desktop and Cursor
- Handles errors gracefully
- Follows all coding best practices

## Example MCP Configuration

### Claude Desktop (`~/.config/claude/mcp.json`)
```json
{
  "mcpServers": {
    "pfsense": {
      "command": "/path/to/pfsense-mcp/.venv/bin/python",
      "args": [
        "/path/to/pfsense-mcp/src/http_pfsense_server.py"
      ],
      "env": {
        "PFSENSE_HOST": "192.168.1.1",
        "PFSENSE_PORT": "443",
        "PFSENSE_API_KEY": "your-api-key-here",
        "PFSENSE_SSL_VERIFY": "false"
      }
    }
  }
}
```

### Cursor (`~/.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer your-github-token"
      }
    },
    "pfsense": {
      "command": "/path/to/pfsense-mcp/.venv/bin/python",
      "args": [
        "/path/to/pfsense-mcp/src/http_pfsense_server.py"
      ],
      "env": {
        "PFSENSE_HOST": "192.168.1.1",
        "PFSENSE_PORT": "443",
        "PFSENSE_API_KEY": "your-api-key-here",
        "PFSENSE_SSL_VERIFY": "false"
      }
    }
  }
}
```

## Requirements.txt Example
```
mcp>=1.12.4
aiohttp>=3.8.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

## Key Implementation Notes

### Critical Serialization Pattern
```python
# ✅ CORRECT - Use dictionaries
async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # ... tool logic ...
        result_text = json.dumps(result, indent=2, default=str)
        return {
            "content": [{"type": "text", "text": result_text}],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }

# ❌ WRONG - Don't use CallToolResult objects
# return CallToolResult(content=[TextContent(type="text", text=result_text)])
```

### pfSense API Client Pattern
```python
class HTTPPfSenseClient:
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 443)
        self.api_key = config.get("api_key")
        self.protocol = config.get("protocol", "https")
        self.ssl_verify = config.get("ssl_verify", False)
        self.session = None
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementation with proper SSL handling and authentication
        pass
```

This prompt incorporates all the key lessons we learned from fixing the TrueNAS MCP server, especially the critical serialization fix that was the main blocker. The structure and approach should result in a working pfSense MCP server from the start! 🚀
