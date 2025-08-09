# iDRAC MCP Server

⚠️ **⚠️ WARNING: UNTESTED PROJECT ⚠️**

**This iDRAC MCP server has NOT been tested in production environments. Use at your own risk!**

- 🔴 **No real-world testing** has been performed
- 🔴 **API compatibility** may not be fully verified
- 🔴 **Error handling** may be incomplete
- 🔴 **Security validation** is pending

**Consider this project as a starting point for development rather than production-ready software.**

---

A Model Context Protocol (MCP) server for managing Dell PowerEdge servers via iDRAC (Integrated Dell Remote Access Controller).

## 🚀 Features

- **HTTP-based**: Fast, portable, and easy to deploy
- **Docker Ready**: Containerized deployment with Docker
- **Secure**: JWT authentication and HTTPS support
- **Fast**: Built with FastAPI for high performance
- **Monitoring**: Comprehensive logging and health checks
- **RESTful**: Clean REST API for iDRAC management

## 🛠️ Capabilities

### System Management
- Get system information and health status
- View hardware inventory (CPU, memory, storage, network)
- Monitor power consumption and thermal status
- Check system events and logs

### Power Management
- Power on/off servers
- Power cycle operations
- Graceful shutdown
- Force power operations

### User Management
- List, create, update, and delete iDRAC users
- Manage user privileges and roles
- Configure authentication settings

### Network Management
- Configure iDRAC network settings
- View network interfaces and IP configuration
- Manage VLAN settings

### Storage Management
- List storage controllers and drives
- View RAID configuration
- Monitor storage health and status

### Firmware Management
- Check firmware versions
- List available firmware updates
- Initiate firmware updates

### Virtual Media
- Mount/unmount virtual media
- List available virtual media options
- Configure virtual media settings

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Dell PowerEdge server with iDRAC
- Network access to iDRAC interface

### Local Development

1. **Clone and setup:**
```bash
cd idrac-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp env.example .env
# Edit .env with your iDRAC settings
```

3. **Start the server:**
   ```bash
   python -m src.http_server
   ```

4. **Test the server:**
   ```bash
   python -m src.http_server
   ```

5. **For fleet management (multiple servers):**
   ```bash
   # Use the secure fleet CLI (recommended)
   python secure_fleet_cli.py init
   python secure_fleet_cli.py add server_name host username
   
   # Or use the basic fleet CLI (less secure)
   python fleet_cli.py init
   python fleet_cli.py add server_name host username password
   ```

### Docker Deployment

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## 📚 Documentation

- **[Usage Guide](USAGE_GUIDE.md)** - Comprehensive guide for using all features
- **[Security Warning](SECURITY_WARNING.md)** - Critical security information

## 🔐 Security

**IMPORTANT:** This project now includes secure password encryption for fleet management. See [SECURITY_WARNING.md](SECURITY_WARNING.md) for details.

- ✅ Passwords are encrypted using Fernet (AES-128-CBC)
- ✅ Encryption keys are stored separately
- ✅ All sensitive files are in `.gitignore`
- ✅ Secure CLI prompts for passwords

### Kubernetes Deployment

```bash
kubectl apply -f k8s/
```

## ⚙️ Configuration

### Environment Variables

```bash
# iDRAC Connection Settings
IDRAC_HOST=192.168.1.100
IDRAC_PORT=443
IDRAC_PROTOCOL=https
IDRAC_USERNAME=root
IDRAC_PASSWORD=your-password

# SSL Settings
IDRAC_SSL_VERIFY=false
IDRAC_SSL_CERT_PATH=

# MCP Server Settings
SERVER_PORT=8000
SECRET_KEY=your-secret-key
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Authentication
MCP_USERNAME=admin
MCP_PASSWORD=admin
ADMIN_TOKEN=admin-token-change-this
```

### CLI Usage

```bash
# Initialize configuration
python -m src.cli init

# Start server
python -m src.cli serve

# Check health
python -m src.cli health

# Login to get JWT token
python -m src.cli login

# List available tools
python -m src.cli list-tools

# Call a specific tool
python -m src.cli call-tool --tool idrac_system_info --node server1
```

## 🔧 Cursor Integration

Add to your Cursor MCP configuration (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "idrac": {
      "url": "http://localhost:8000/mcp/",
      "headers": {
        "Authorization": "Bearer your-jwt-token-here"
      }
    }
  }
}
```

## 🛠️ Available Tools

### System Tools
- `idrac_system_info` - Get system information
- `idrac_system_health` - Check system health status
- `idrac_hardware_inventory` - List hardware components
- `idrac_power_status` - Get power status
- `idrac_thermal_status` - Get thermal status

### Power Management
- `idrac_power_on` - Power on server
- `idrac_power_off` - Power off server
- `idrac_power_cycle` - Power cycle server
- `idrac_graceful_shutdown` - Graceful shutdown

### User Management
- `idrac_users_list` - List iDRAC users
- `idrac_user_create` - Create new user
- `idrac_user_update` - Update user settings
- `idrac_user_delete` - Delete user

### Network Management
- `idrac_network_config` - Get network configuration
- `idrac_network_interfaces` - List network interfaces
- `idrac_network_update` - Update network settings

### Storage Management
- `idrac_storage_controllers` - List storage controllers
- `idrac_storage_drives` - List storage drives
- `idrac_raid_config` - Get RAID configuration

### Firmware Management
- `idrac_firmware_versions` - Check firmware versions
- `idrac_firmware_updates` - List available updates
- `idrac_firmware_update` - Initiate firmware update

### Virtual Media
- `idrac_virtual_media_list` - List virtual media
- `idrac_virtual_media_mount` - Mount virtual media
- `idrac_virtual_media_unmount` - Unmount virtual media

## 📝 Examples

### Get System Information
```python
# Using the MCP client
result = await client.call_tool("idrac_system_info", {"node": "server1"})
print(result)
```

### Power Management
```python
# Power cycle a server
result = await client.call_tool("idrac_power_cycle", {
    "node": "server1",
    "force": False
})
```

### User Management
```python
# Create a new user
result = await client.call_tool("idrac_user_create", {
    "node": "server1",
    "username": "newuser",
    "password": "securepass",
    "privilege": "Administrator"
})
```

## 🔒 Security

- JWT token authentication
- HTTPS support for iDRAC communication
- Password hashing with bcrypt
- Configurable SSL verification
- Role-based access control

## 🏗️ Development

### Project Structure
```
idrac-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── http_server.py     # FastAPI HTTP server
│   ├── cli.py            # Command-line interface
│   ├── idrac_client.py   # iDRAC API client
│   ├── auth.py           # Authentication manager
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py    # Logging configuration
│   │   └── validation.py # Input validation
│   └── resources/
│       ├── __init__.py
│       ├── base.py       # Base resource handler
│       ├── system.py     # System management
│       ├── power.py      # Power management
│       ├── users.py      # User management
│       ├── network.py    # Network management
│       ├── storage.py    # Storage management
│       ├── firmware.py   # Firmware management
│       └── virtual_media.py # Virtual media
├── examples/
├── tests/
├── docker/
├── k8s/
├── requirements.txt
├── env.example
└── README.md
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_system.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Create an issue for bugs or feature requests
- Check the documentation in the `docs/` folder
- Review the examples in the `examples/` folder

## 🗺️ Roadmap

- [ ] Support for multiple iDRAC versions
- [ ] Advanced monitoring and alerting
- [ ] Bulk operations across multiple servers
- [ ] Integration with monitoring systems
- [ ] Web UI for configuration
- [ ] Plugin system for custom tools
- [ ] Support for Dell OpenManage
- [ ] Advanced security features

---

Built with ❤️ for Dell PowerEdge server management
