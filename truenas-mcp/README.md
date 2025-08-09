# TrueNAS MCP Server

A **portable, HTTP-based** Model Context Protocol (MCP) server that provides an interface between AI tools (like Cursor) and TrueNAS Scale servers. This enables AI assistants to query system information, manage storage, configure services, and perform administrative tasks on TrueNAS Scale from anywhere.

## 🚀 Key Features

- **🌐 HTTP-based**: Accessible via HTTP/HTTPS like GitHub MCP servers
- **📦 Portable**: Run locally, on any server, or in the cloud
- **🐳 Docker Ready**: Containerized deployment with Docker and Kubernetes
- **🔐 Secure**: JWT authentication for MCP clients
- **⚡ Fast**: Async operations with FastAPI
- **📊 Monitoring**: Health checks and comprehensive logging

## 🛠️ Capabilities

### 🔧 System Management
- Get system information, version, and health status
- Monitor system uptime and statistics
- View system alerts and notifications
- Reboot and shutdown system (with safeguards)

### 💾 Storage Management
- Create, view, and manage storage pools
- Create and manage datasets with compression and encryption
- Create and manage snapshots
- Set up replication tasks
- Monitor storage health and usage

### 🌐 Network Configuration
- View and configure network interfaces
- Manage network routes
- Test network connectivity
- Configure IP addresses, netmasks, and gateways

### 🔌 Services Management
- Start, stop, and restart services
- Manage SMB, NFS, and iSCSI shares
- Configure service parameters
- Monitor service status

### 👥 User Management
- Create, update, and delete users
- Manage user groups
- Configure user permissions
- Set up user authentication

### 📊 Monitoring & Alerts
- Get system metrics and statistics
- View system alerts and notifications
- Monitor performance metrics
- Track system health

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (for local development)
- Docker (for containerized deployment)
- TrueNAS Scale server with API access

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-username/truenas-mcp.git
   cd truenas-mcp
   pip install -r requirements.txt
   ```

2. **Initialize configuration**:
   ```bash
   python -m src.http_cli init
   ```

3. **Update configuration**:
   Edit `.env` file with your TrueNAS details:
   ```env
   TRUENAS_HOST=your-truenas-host.example.com
   TRUENAS_API_KEY=your-api-key-here
   SECRET_KEY=your-generated-secret-key
   ```

4. **Start server**:
   ```bash
   python -m src.http_cli serve
   ```

5. **Test connection**:
   ```bash
   python -m src.http_cli health
   ```

### Docker Deployment

```bash
# Using Docker Compose (recommended)
docker-compose -f docker/docker-compose.yml up -d

# Or build and run manually
docker build -f docker/Dockerfile -t truenas-mcp .
docker run -d -p 8000:8000 \
  -e TRUENAS_HOST=your-truenas-host \
  -e TRUENAS_API_KEY=your-api-key \
  -e SECRET_KEY=your-secret-key \
  truenas-mcp
```

### Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl create namespace truenas-mcp
kubectl apply -f k8s/

# Create secrets
kubectl create secret generic truenas-mcp-secrets \
  --from-literal=truenas_api_key=your-api-key \
  --from-literal=secret_key=your-secret-key \
  -n truenas-mcp
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TRUENAS_HOST` | TrueNAS server hostname | - | Yes |
| `TRUENAS_API_KEY` | API key for authentication | - | Yes* |
| `TRUENAS_USERNAME` | Username for authentication | - | Yes* |
| `TRUENAS_PASSWORD` | Password for authentication | - | Yes* |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `SERVER_PORT` | MCP server port | 8000 | No |
| `DEBUG` | Enable debug mode | false | No |

*Either API key or username/password is required.

### Using the CLI

```bash
# Initialize configuration
python -m src.http_cli init

# Start server
python -m src.http_cli serve

# Check health
python -m src.http_cli health

# Login to get JWT token
python -m src.http_cli login

# List available tools
python -m src.http_cli list-tools
```

### Configuration File

Create a JSON configuration file:

```json
{
  "host": "your-truenas-host",
  "port": 443,
  "api_key": "your-api-key",
  "verify_ssl": true
}
```

## 🔗 Cursor Integration

### Setup

1. **Start the MCP server**:
   ```bash
   python -m src.http_cli serve
   ```

2. **Get a JWT token**:
   ```bash
   # Login with default credentials
   python -m src.http_cli login
   
   # Or create token with admin token
   python -m src.http_cli create-token --admin-token your-admin-token
   ```

3. **Configure Cursor**:
   Add to your `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "truenas": {
         "url": "http://localhost:8000/mcp/",
         "headers": {
           "Authorization": "Bearer your-jwt-token"
         }
       }
     }
   }
   ```

4. **Restart Cursor** and start using TrueNAS tools!

### Example Usage in Cursor

Once configured, you can ask Cursor to:

- "Show me the system information for my TrueNAS server"
- "List all storage pools and their usage"
- "Check the status of all services"
- "Create a new dataset called 'backups'"
- "Show me recent system alerts"

## 🛠️ Usage

### CLI Commands

```bash
# Initialize configuration
python -m src.http_cli init

# Start server
python -m src.http_cli serve

# Check health
python -m src.http_cli health

# Login to get JWT token
python -m src.http_cli login

# List available tools
python -m src.http_cli list-tools

# Call a specific tool
python -m src.http_cli call-tool truenas_system_get_info

# Generate configuration examples
python -m src.http_cli generate-config
```

### API Endpoints

- `GET /` - Server information
- `GET /health` - Health check
- `POST /auth/login` - Login to get JWT token
- `POST /auth/token` - Create token with admin token
- `POST /mcp/initialize` - MCP initialization
- `POST /mcp/tools/list` - List available tools
- `POST /mcp/tools/call` - Call a tool
truenas-mcp --log-level DEBUG serve
```

### Integration with Cursor

1. Add the MCP server to your Cursor configuration:

```json
{
  "mcpServers": {
    "truenas": {
      "command": "truenas-mcp",
      "args": ["serve"],
      "env": {
        "TRUENAS_HOST": "your-truenas-host",
        "TRUENAS_API_KEY": "your-api-key"
      }
    }
  }
}
```

2. Restart Cursor and start using the TrueNAS tools!

## Available Tools

### System Tools
- `truenas_system_get_info` - Get detailed system information
- `truenas_system_get_version` - Get TrueNAS version
- `truenas_system_get_health` - Get system health status
- `truenas_system_get_uptime` - Get system uptime
- `truenas_system_get_stats` - Get system statistics
- `truenas_system_get_alerts` - Get system alerts

### Storage Tools
- `truenas_storage_get_pools` - Get all storage pools
- `truenas_storage_create_pool` - Create a new storage pool
- `truenas_storage_get_datasets` - Get datasets
- `truenas_storage_create_dataset` - Create a new dataset
- `truenas_storage_get_snapshots` - Get snapshots
- `truenas_storage_create_snapshot` - Create a new snapshot

### Network Tools
- `truenas_network_get_interfaces` - Get network interfaces
- `truenas_network_update_interface` - Update interface configuration
- `truenas_network_get_routes` - Get network routes
- `truenas_network_test_connectivity` - Test network connectivity

### Services Tools
- `truenas_services_get_all` - Get all services
- `truenas_services_start_service` - Start a service
- `truenas_services_stop_service` - Stop a service
- `truenas_services_restart_service` - Restart a service

### User Tools
- `truenas_users_get_all` - Get all users
- `truenas_users_create_user` - Create a new user
- `truenas_users_update_user` - Update user information
- `truenas_users_get_groups` - Get all groups

## Examples

### Get System Information
```python
# Using the MCP server
result = await call_tool("truenas_system_get_info")
print(result)
```

### Create a Storage Pool
```python
result = await call_tool("truenas_storage_create_pool", {
    "name": "my_pool",
    "disks": ["sda", "sdb"],
    "raid_type": "mirror"
})
```

### Create a Dataset
```python
result = await call_tool("truenas_storage_create_dataset", {
    "name": "my_dataset",
    "pool": "my_pool",
    "type": "FILESYSTEM",
    "compression": "lz4"
})
```

## Security Considerations

- **API Key Management**: Store API keys securely and rotate them regularly
- **SSL Verification**: Always verify SSL certificates in production
- **Input Validation**: All inputs are validated and sanitized
- **Audit Logging**: All operations are logged for security auditing
- **Permission Checks**: Implement appropriate permission checks for destructive operations

## Development

### Project Structure
```
truenas-mcp/
├── src/
│   ├── server.py              # Main MCP server
│   ├── truenas_client.py      # TrueNAS API client
│   ├── auth.py               # Authentication manager
│   ├── cli.py                # Command-line interface
│   ├── resources/            # Resource handlers
│   │   ├── base.py
│   │   ├── system.py
│   │   ├── storage.py
│   │   ├── network.py
│   │   ├── services.py
│   │   └── users.py
│   └── utils/                # Utility functions
│       ├── validation.py
│       └── logging.py
├── tests/                    # Test suite
├── examples/                 # Usage examples
├── docs/                     # Documentation
└── README.md
```

### Running Tests
```bash
pytest
pytest --cov=src
pytest --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the [docs/](docs/) directory for detailed documentation
- **Examples**: See the [examples/](examples/) directory for usage examples

## Roadmap

- [ ] Docker/Kubernetes application management
- [ ] Advanced monitoring and alerting
- [ ] Backup and restore operations
- [ ] Performance optimization
- [ ] Web UI for configuration
- [ ] Plugin system for custom tools

## Acknowledgments

- TrueNAS team for the excellent API
- MCP community for the protocol specification
- Contributors and users of this project
