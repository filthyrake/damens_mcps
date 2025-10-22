# iDRAC MCP Server

A Model Context Protocol (MCP) server for managing multiple Dell iDRAC servers through their Redfish API.

## Features

- **Multi-Server Support**: Manage multiple iDRAC servers from a single MCP server
- **Power Management**: Power on, off, restart, and force power off servers
- **System Information**: Get hardware details, power status, and health information
- **Flexible Configuration**: JSON-based configuration with support for multiple server profiles
- **Authentication**: Secure credential management with configurable SSL verification

## Configuration

Create a `config.json` file in the same directory as the server:

```json
{
  "idrac_servers": {
    "production": {
      "name": "Production Server",
      "host": "10.0.10.11",
      "port": 443,
      "protocol": "https",
      "username": "root",
      "password": "your_password_here",
      "ssl_verify": false
    },
    "backup": {
      "name": "Backup Server",
      "host": "10.0.10.12",
      "port": 443,
      "protocol": "https",
      "username": "root",
      "password": "your_password_here",
      "ssl_verify": false
    }
  },
  "default_server": "production",
  "server": {
    "port": 8000,
    "debug": true
  }
}
```

### Configuration Options

- **`idrac_servers`**: Dictionary of server configurations
  - **`name`**: Human-readable server name (optional, defaults to server ID)
  - **`host`**: IP address or hostname of the iDRAC
  - **`port`**: Port number (usually 443 for HTTPS)
  - **`protocol`**: Protocol to use (http or https)
  - **`username`**: iDRAC username (usually "root")
  - **`password`**: iDRAC password
  - **`ssl_verify`**: Whether to verify SSL certificates (set to false for self-signed)
- **`default_server`**: ID of the server to use when no server_id is specified
- **`server`**: MCP server configuration

## Available Tools

The iDRAC MCP server provides **8 tools** for managing Dell PowerEdge servers:

### System Information Tools

#### `list_servers`
Lists all configured iDRAC servers and their basic information.

**Arguments**: None

**Returns**: List of configured server IDs

**Example**:
```json
{
  "servers": ["production", "backup", "test_server"]
}
```

**Use Cases**:
- Discovering available servers in multi-server environments
- Verifying configuration is loaded correctly
- Providing server options to users

---

#### `test_connection`
Tests connectivity to an iDRAC server and verifies authentication.

**Arguments**:
- `server_id` (optional, string): ID of the server to test. Uses default server if not specified.

**Returns**: Connection test result with status and server information

**Example**:
```json
{
  "server_id": "production",
  "connection": "success",
  "message": "Successfully connected to iDRAC",
  "api_version": "Redfish 1.x"
}
```

**Use Cases**:
- Verifying iDRAC is accessible before operations
- Troubleshooting network connectivity issues
- Validating credentials without making changes

---

#### `get_system_info`
Retrieves comprehensive system information from an iDRAC server including hardware details, model, service tag, and BIOS version.

**Arguments**:
- `server_id` (optional, string): ID of the server to query. Uses default server if not specified.

**Returns**: Detailed system information

**Example**:
```json
{
  "server_id": "production",
  "manufacturer": "Dell Inc.",
  "model": "PowerEdge R740",
  "service_tag": "ABC1234",
  "bios_version": "2.10.0",
  "memory_gb": 256,
  "processors": 2,
  "status": "OK"
}
```

**Use Cases**:
- Hardware inventory and asset management
- Verifying hardware specifications
- Checking firmware versions
- Documentation and auditing

---

### Power Management Tools

#### `get_power_status`
Gets the current power state of a server.

**Arguments**:
- `server_id` (optional, string): ID of the server to query. Uses default server if not specified.

**Returns**: Current power state

**Example**:
```json
{
  "server_id": "production",
  "power_state": "On",
  "status": "success"
}
```

**Possible Power States**:
- `On`: Server is powered on
- `Off`: Server is powered off
- `PoweringOn`: Server is in the process of powering on
- `PoweringOff`: Server is in the process of powering off

**Use Cases**:
- Monitoring server status
- Verifying power state before operations
- Health checks and automated monitoring

---

#### `power_on`
Powers on a server that is currently off.

**Arguments**:
- `server_id` (optional, string): ID of the server to control. Uses default server if not specified.

**Returns**: Power on operation result

**Example**:
```json
{
  "server_id": "production",
  "action": "power_on",
  "status": "success",
  "message": "Power on command sent successfully"
}
```

**⚠️ Important Notes**:
- Command is asynchronous - server takes time to fully boot
- Check power status after 30-60 seconds to confirm
- Does nothing if server is already powered on
- May fail if server has hardware issues

**Use Cases**:
- Remote server startup
- Automated recovery procedures
- Scheduled power-on operations
- Testing and development environments

---

#### `power_off`
Gracefully powers off a server by sending a shutdown signal to the OS.

**Arguments**:
- `server_id` (optional, string): ID of the server to control. Uses default server if not specified.

**Returns**: Power off operation result

**Example**:
```json
{
  "server_id": "production",
  "action": "power_off",
  "status": "success",
  "message": "Power off command sent successfully"
}
```

**⚠️ Important Notes**:
- **Graceful shutdown**: Allows OS to shut down properly
- Takes several minutes to complete
- Requires OS to be responsive
- Use `force_power_off` if OS is unresponsive
- **Production Impact**: Server will be unavailable

**Use Cases**:
- Scheduled maintenance windows
- Controlled server shutdown
- Power saving during off-hours
- Pre-hardware maintenance procedures

---

#### `force_power_off`
**DANGEROUS**: Immediately cuts power to the server without OS shutdown.

**Arguments**:
- `server_id` (optional, string): ID of the server to control. Uses default server if not specified.

**Returns**: Force power off operation result

**Example**:
```json
{
  "server_id": "production",
  "action": "force_power_off",
  "status": "success",
  "message": "Force power off command sent successfully"
}
```

**⚠️ CRITICAL WARNINGS**:
- **Data Loss Risk**: Does not allow OS to save data
- **File System Corruption**: May corrupt filesystems
- **Application Damage**: Running applications terminated immediately
- **Use ONLY as last resort** when OS is unresponsive
- Equivalent to pulling the power plug

**Safe Use Cases**:
- Server completely unresponsive (hung OS)
- Emergency situations only
- After graceful shutdown has failed
- Hardware testing in non-production

**DO NOT USE FOR**:
- Normal shutdowns
- Production servers (use `power_off` instead)
- Scheduled operations
- Convenience (use `power_off` instead)

---

#### `restart`
Gracefully restarts a server by sending a reboot signal to the OS.

**Arguments**:
- `server_id` (optional, string): ID of the server to control. Uses default server if not specified.

**Returns**: Restart operation result

**Example**:
```json
{
  "server_id": "production",
  "action": "restart",
  "status": "success",
  "message": "Restart command sent successfully"
}
```

**⚠️ Important Notes**:
- **Graceful reboot**: Allows OS to shut down properly
- Server will reboot automatically after shutdown
- Takes several minutes to complete
- Requires OS to be responsive
- **Production Impact**: Server will be briefly unavailable

**Use Cases**:
- Applying OS updates that require reboot
- Clearing memory issues
- Scheduled maintenance reboots
- After configuration changes

---

## Multi-Server Management

### Default Server
If you don't specify a `server_id`, the tool uses the `default_server` from your configuration:

```json
{
  "default_server": "production"
}
```

### Specifying a Server
To target a specific server, include the `server_id` parameter:

```bash
# Using production server (default)
{
  "tool": "get_system_info"
}

# Explicitly using backup server
{
  "tool": "get_system_info",
  "arguments": {
    "server_id": "backup"
  }
}
```

### Server Naming Best Practices

Use meaningful server IDs that indicate purpose or location:
- `production`, `backup`, `development`
- `dc1-web01`, `dc2-db01`
- `floor3-rack5-server2`

---

## Tool Summary Table

| Tool | Purpose | Destructive | Multi-Server |
|------|---------|-------------|--------------|
| `list_servers` | List configured servers | No | N/A |
| `test_connection` | Test connectivity | No | Yes |
| `get_system_info` | Get hardware info | No | Yes |
| `get_power_status` | Check power state | No | Yes |
| `power_on` | Start server | No* | Yes |
| `power_off` | Graceful shutdown | Yes | Yes |
| `force_power_off` | Emergency shutdown | **YES** | Yes |
| `restart` | Graceful reboot | Yes | Yes |

*Power on is not destructive but does consume power and start services

## Usage Examples

### With Claude Desktop

1. Add the MCP server to Claude Desktop
2. Use tools like:
   - "List all my iDRAC servers"
   - "Get system info from the production server"
   - "Check power status of all servers"
   - "Power on the backup server"

### Command Line Testing

Run the test server to verify functionality:

```bash
python test_server.py
```

## Security Notes

- **Never commit `config.json`** - it contains sensitive credentials
- Use `config.example.json` as a template
- Consider using environment variables for production deployments
- SSL verification is disabled by default for self-signed certificates

## Troubleshooting

### 401 Authentication Errors
- Verify credentials in `config.json`
- Check if the iDRAC server is accessible from your network
- Ensure the user account has appropriate permissions

### Connection Timeouts
- Verify the IP address and port
- Check firewall settings
- Ensure the iDRAC service is running

### SSL Errors
- Set `ssl_verify: false` for self-signed certificates
- Verify the protocol is set correctly (http vs https)

## Development

The server is built as a pure JSON-RPC implementation to avoid MCP library compatibility issues. It reads from stdin and writes to stdout for MCP protocol communication.

## License

This project is for internal use only.
