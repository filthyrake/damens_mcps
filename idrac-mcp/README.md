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

### `list_servers`
Lists all configured iDRAC servers.

**Arguments**: None

### `test_connection`
Tests connectivity to an iDRAC server.

**Arguments**:
- `server_id` (optional): ID of the server to test. Uses default if not specified.

### `get_system_info`
Retrieves system information from an iDRAC server.

**Arguments**:
- `server_id` (optional): ID of the server to query. Uses default if not specified.

### `get_power_status`
Gets the current power status of a server.

**Arguments**:
- `server_id` (optional): ID of the server to query. Uses default if not specified.

### `power_on`
Powers on a server.

**Arguments**:
- `server_id` (optional): ID of the server to control. Uses default if not specified.

### `power_off`
Gracefully powers off a server.

**Arguments**:
- `server_id` (optional): ID of the server to control. Uses default if not specified.

### `force_power_off`
Forces a server to power off immediately.

**Arguments**:
- `server_id` (optional): ID of the server to control. Uses default if not specified.

### `restart`
Gracefully restarts a server.

**Arguments**:
- `server_id` (optional): ID of the server to control. Uses default if not specified.

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
