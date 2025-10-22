# pfSense MCP Server 🔥

A comprehensive Model Context Protocol (MCP) server for pfSense firewall management, providing AI assistants with direct access to pfSense configuration and monitoring capabilities.

## Features ✨

### System Management
- **System Information**: Get pfSense version, uptime, and system status
- **System Health**: Monitor CPU, memory, and disk usage
- **Network Interfaces**: View all interfaces and their status
- **Services**: Check running services (DNS, DHCP, etc.)

### Firewall Management 🔥
- **Firewall Rules**: List, create, delete, and manage firewall rules
- **Firewall Logs**: Access recent firewall activity logs
- **Rule Validation**: Built-in validation for firewall rule parameters

### Network Configuration 🌐
- **VLAN Management**: Create, delete, and manage VLANs
- **DHCP Leases**: View current DHCP lease information
- **DNS Configuration**: Check DNS server settings

### Package Management 📦
- **Installed Packages**: List currently installed packages
- **Package Installation**: Install new packages
- **Package Removal**: Remove existing packages
- **Update Checking**: Check for available package updates

### VPN Management 🔐
- **VPN Status**: Check VPN connection status
- **OpenVPN Servers**: Manage OpenVPN server configurations
- **OpenVPN Clients**: Manage OpenVPN client configurations
- **Service Restart**: Restart VPN services

### Backup & Restore 💾
- **System Backups**: Create system configuration backups
- **Backup Restoration**: Restore from existing backups
- **Backup Management**: List and manage available backups

## Quick Start 🚀

### Prerequisites

- Python 3.8 or higher
- pfSense 2.5+ with REST API enabled
- API key or username/password for authentication

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pfsense-mcp
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your pfSense settings
   ```

### Configuration

Set up your environment variables in `.env`:

```bash
# pfSense Connection
PFSENSE_HOST=192.168.1.1
PFSENSE_PORT=443
PFSENSE_PROTOCOL=https

# Authentication (choose one method)
PFSENSE_API_KEY=your-api-key-here
# OR
# PFSENSE_USERNAME=admin
# PFSENSE_PASSWORD=your-password

# SSL Settings
PFSENSE_SSL_VERIFY=true
```

#### Configuration Options Explained

##### Connection Settings

- **PFSENSE_HOST** (required)
  - **Type:** String (hostname or IP address)
  - **Description:** pfSense firewall address
  - **Example:** `192.168.1.1` or `firewall.example.com`
  - **Security:** Should be on a trusted management network

- **PFSENSE_PORT** (optional)
  - **Type:** Integer
  - **Default:** `443`
  - **Description:** HTTPS port for pfSense web interface
  - **Valid Range:** 1-65535
  - **Note:** Use port 80 only if HTTPS is unavailable

- **PFSENSE_PROTOCOL** (optional)
  - **Type:** String
  - **Default:** `https`
  - **Valid Values:** `https`, `http`
  - **Description:** Protocol for pfSense connection
  - **Security:** Always use `https` in production

##### Authentication Methods

pfSense MCP supports two authentication methods. **Choose only one:**

**Method 1: API Key (Recommended)**
- **PFSENSE_API_KEY** (required if not using username/password)
  - **Type:** String
  - **Description:** pfSense REST API key
  - **Security:** Preferred method - supports key rotation without password changes
  - **How to generate:**
    1. Log into pfSense web interface
    2. Navigate to **System → API**
    3. Enable the REST API if not already enabled
    4. Click **+ Add** to create a new API key
    5. Assign appropriate permissions (typically full access for MCP)
    6. Copy the generated key immediately (it won't be shown again)
  - **Example:** `AbCdEf123456789GhIjKlMnOpQrStUvWxYz`

**Method 2: Username & Password**
- **PFSENSE_USERNAME** (required if not using API key)
  - **Type:** String
  - **Description:** pfSense admin username
  - **Default:** `admin`
  - **Security:** Use a dedicated account with minimal necessary privileges

- **PFSENSE_PASSWORD** (required if not using API key)
  - **Type:** String
  - **Description:** pfSense admin password
  - **Security:** Use a strong password; rotate regularly

**Authentication Precedence:** If both API key and username/password are provided, the API key takes precedence.

##### SSL/TLS Settings

- **PFSENSE_SSL_VERIFY** (optional)
  - **Type:** Boolean
  - **Default:** `true`
  - **Valid Values:** `true`, `false`
  - **Description:** Whether to verify SSL certificates
  - **Security Implications:**
    - `true` (recommended): Verifies the SSL certificate, preventing MITM attacks
    - `false`: Disables SSL verification, accepting self-signed certificates
  - **When to use `false`:**
    - Development/testing environments
    - pfSense uses a self-signed certificate
    - Custom CA certificate (see below for better option)
  - **Production:** Always use `true` with valid certificates

#### Troubleshooting SSL Certificate Issues

If you encounter SSL certificate errors:

**Option 1: Disable Verification (Testing Only)**
```bash
PFSENSE_SSL_VERIFY=false
```

**Option 2: Use Valid Certificates (Recommended)**
1. Install Let's Encrypt or commercial certificate on pfSense
2. Navigate to **System → Cert. Manager**
3. Import or generate a valid certificate
4. Set it as the web interface certificate

**Option 3: Trust Self-Signed Certificate**
```python
# Add custom CA certificate to Python's trust store
import certifi
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/custom-ca-bundle.crt'
```

#### Required pfSense Configuration

Before using this MCP server, ensure pfSense is properly configured:

1. **Enable REST API**
   - Navigate to **System → API**
   - Check **Enable REST API**
   - Select **JSON** as the API format
   - Click **Save**

2. **API Version Requirements**
   - **Minimum:** pfSense 2.5.0
   - **Recommended:** pfSense 2.6.0 or later
   - Some tools may require specific versions (noted in tool descriptions)

3. **User Permissions**
   - API key or user account must have appropriate permissions
   - For full functionality, use an account with **System Administrator** privileges
   - For restricted access, create a custom privilege set

#### Environment Variable Alternatives

Instead of `.env` file, you can also set variables directly:

```bash
# Export variables in your shell
export PFSENSE_HOST=192.168.1.1
export PFSENSE_API_KEY=your-api-key-here

# Run the server
python src/http_pfsense_server.py
```

Or pass them when running:

```bash
PFSENSE_HOST=192.168.1.1 PFSENSE_API_KEY=your-key python src/http_pfsense_server.py
```

### Testing the Connection

Run the basic usage example to test your configuration:

```bash
python examples/basic_usage.py
```

## MCP Configuration 📋

### Claude Desktop

Add to `~/.config/claude/mcp.json`:

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

### Cursor

Add to `~/.cursor/mcp.json`:

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

## Available Tools 🛠️

### System Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_system_info` | Get pfSense system information | None |
| `get_system_health` | Get system health metrics | None |
| `get_interfaces` | List network interfaces | None |
| `get_services` | List running services | None |

### Firewall Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_firewall_rules` | List all firewall rules | None |
| `create_firewall_rule` | Create new firewall rule | `action`, `interface`, `direction`, `source`, `destination`, `port`, `description` |
| `delete_firewall_rule` | Delete firewall rule | `rule_id` |
| `get_firewall_logs` | Get firewall logs | `limit` (optional) |

### Network Configuration

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_vlans` | List VLAN configurations | None |
| `create_vlan` | Create new VLAN | `vlan_id`, `interface`, `description` |
| `delete_vlan` | Delete VLAN | `vlan_id` |
| `get_dhcp_leases` | Get DHCP leases | None |
| `get_dns_servers` | Get DNS configuration | None |

### Package Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_installed_packages` | List installed packages | None |
| `install_package` | Install package | `package_name` |
| `remove_package` | Remove package | `package_name` |
| `get_package_updates` | Check for updates | None |

### VPN Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_vpn_status` | Get VPN status | None |
| `get_openvpn_servers` | List OpenVPN servers | None |
| `get_openvpn_clients` | List OpenVPN clients | None |
| `restart_vpn_service` | Restart VPN service | `service_name` |

### Backup & Restore

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_backup` | Create system backup | `backup_name` |
| `restore_backup` | Restore from backup | `backup_id` |
| `get_backup_list` | List backups | None |

### Connection

| Tool | Description | Parameters |
|------|-------------|------------|
| `test_connection` | Test pfSense connection | None |

## Usage Examples 💡

### Get System Information
```python
# Get basic system info
result = await client.get_system_info()
print(f"pfSense Version: {result['version']}")
```

### Create Firewall Rule
```python
# Create a rule to allow HTTP traffic
rule = {
    "action": "pass",
    "interface": "wan",
    "direction": "in",
    "source": "any",
    "destination": "any",
    "port": "80",
    "description": "Allow HTTP traffic"
}
result = await client.create_firewall_rule(rule)
```

### Monitor System Health
```python
# Check system health
health = await client.get_system_health()
print(f"CPU Usage: {health['cpu_usage']}%")
print(f"Memory Usage: {health['memory_usage']}%")
```

### Manage VLANs
```python
# Create a new VLAN
vlan = {
    "vlan_id": 100,
    "interface": "igb0",
    "description": "Guest Network"
}
result = await client.create_vlan(vlan)
```

## Error Handling 🛡️

The server includes comprehensive error handling:

- **Validation Errors**: Input validation for all parameters
- **API Errors**: Proper handling of pfSense API errors
- **Network Errors**: Connection timeout and SSL error handling
- **Serialization Errors**: Fixed using dictionary responses instead of CallToolResult objects

### Common Error Scenarios

1. **Authentication Failed**: Check API key or username/password
2. **Connection Refused**: Verify pfSense host and port
3. **SSL Certificate Error**: Set `PFSENSE_SSL_VERIFY=false` for self-signed certificates
4. **Invalid Parameters**: Check tool parameter requirements

## Security Considerations 🔒

- **API Keys**: Use API keys instead of username/password when possible
- **SSL Verification**: Enable SSL verification in production
- **Network Access**: Restrict access to pfSense management interface
- **Input Validation**: All inputs are validated and sanitized
- **Error Messages**: Sensitive information is not exposed in error messages

## Troubleshooting 🔧

### Connection Issues

1. **Check pfSense API**: Ensure REST API is enabled in pfSense
2. **Verify Credentials**: Double-check API key or username/password
3. **Network Connectivity**: Test basic connectivity to pfSense
4. **SSL Issues**: Try disabling SSL verification temporarily

### Tool Errors

1. **Parameter Validation**: Check required parameters for each tool
2. **API Permissions**: Ensure your credentials have sufficient permissions
3. **pfSense Version**: Some features may require specific pfSense versions

### Logging

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
```

## Development 🛠️

### Project Structure

```
pfsense-mcp/
├── src/
│   ├── http_pfsense_server.py    # Main MCP server
│   ├── pfsense_client.py         # pfSense API client
│   ├── auth.py                   # Authentication handling
│   └── utils/
│       ├── logging.py            # Logging utilities
│       └── validation.py         # Input validation
├── examples/
│   ├── config.json.example       # MCP config example
│   └── basic_usage.py           # Usage example
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables
└── README.md                     # This file
```

### Adding New Tools

1. Add the tool definition to `_create_tools()` in `HTTPPfSenseMCPServer`
2. Implement the tool logic in `_call_tool()`
3. Add the corresponding method to `HTTPPfSenseClient`
4. Update documentation and examples

### Testing

Run the test script to verify functionality:

```bash
python examples/basic_usage.py
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For issues and questions:

1. Check the troubleshooting section
2. Review the error logs
3. Test with the basic usage example
4. Open an issue on GitHub

## Changelog 📝

### Version 1.0.0
- Initial release
- Complete pfSense management capabilities
- MCP server implementation
- Comprehensive error handling
- Input validation and sanitization

---

**Note**: This MCP server is designed for pfSense 2.5+ with REST API enabled. Ensure your pfSense installation meets these requirements before use.
