# Proxmox MCP Server 🖥️

A comprehensive Model Context Protocol (MCP) server for Proxmox VE management, providing AI assistants with direct access to Proxmox virtualization platform capabilities. This enables AI tools to manage virtual machines, containers, storage, networking, and system administration tasks on Proxmox VE servers.

## 🚀 Key Features

- **🌐 HTTP-based**: Accessible via HTTP/HTTPS like other MCP servers
- **📦 Portable**: Run locally, on any server, or in the cloud
- **🐳 Docker Ready**: Containerized deployment with Docker and Kubernetes
- **🔐 Secure**: JWT authentication for MCP clients
- **⚡ Fast**: Async operations with FastAPI
- **📊 Monitoring**: Health checks and comprehensive logging

## 🛠️ Capabilities

### 🖥️ Virtual Machine Management
- Create, start, stop, and delete virtual machines
- Manage VM configurations (CPU, memory, storage, network)
- Monitor VM performance and resource usage
- Take snapshots and manage VM backups
- Migrate VMs between nodes

### 📦 Container Management
- Create and manage LXC containers
- Manage container configurations and resources
- Monitor container performance
- Take container snapshots

### 💾 Storage Management
- View and manage storage pools
- Create and manage storage volumes
- Monitor storage usage and performance
- Manage storage snapshots

### 🌐 Network Configuration
- View and configure network interfaces
- Manage virtual networks and bridges
- Configure VLANs and bonding
- Monitor network performance

### 🏗️ Cluster Management
- View cluster information and node status
- Monitor cluster health and performance
- Manage cluster resources and HA groups

### 👥 User & Permission Management
- Manage Proxmox users and groups
- Configure role-based access control
- Manage API tokens and permissions

### 📊 Monitoring & Alerts
- Get system metrics and statistics
- Monitor resource usage across nodes
- View system logs and alerts

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (for local development)
- Docker (for containerized deployment)
- Proxmox VE 8.0+ with API access
- API token or username/password for authentication

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-username/proxmox-mcp.git
   cd proxmox-mcp
   pip install -r requirements.txt
   ```

2. **Initialize configuration**:
   ```bash
   python -m src.http_cli init
   ```

3. **Update configuration**:
   Edit `.env` file with your Proxmox details:
   ```env
   PROXMOX_HOST=your-proxmox-host.example.com
   PROXMOX_PORT=8006
   PROXMOX_USERNAME=your-username
   PROXMOX_PASSWORD=your-password
   # OR use API token
   PROXMOX_API_TOKEN=your-api-token
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
docker build -f docker/Dockerfile -t proxmox-mcp .
docker run -d -p 8000:8000 \
  -e PROXMOX_HOST=your-proxmox-host \
  -e PROXMOX_USERNAME=your-username \
  -e PROXMOX_PASSWORD=your-password \
  -e SECRET_KEY=your-secret-key \
  proxmox-mcp
```

### Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl create namespace proxmox-mcp
kubectl apply -f k8s/

# Create secrets
kubectl create secret generic proxmox-mcp-secrets \
  --from-literal=proxmox_username=your-username \
  --from-literal=proxmox_password=your-password \
  --from-literal=secret_key=your-secret-key \
  -n proxmox-mcp
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROXMOX_HOST` | Proxmox server hostname | - | Yes |
| `PROXMOX_PORT` | Proxmox API port | 8006 | No |
| `PROXMOX_USERNAME` | Username for authentication | - | Yes* |
| `PROXMOX_PASSWORD` | Password for authentication | - | Yes* |
| `PROXMOX_API_TOKEN` | API token for authentication | - | Yes* |
| `PROXMOX_REALM` | Authentication realm | pve | No |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `SERVER_PORT` | MCP server port | 8000 | No |
| `DEBUG` | Enable debug mode | false | No |

*Either API token or username/password is required.

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
  "host": "your-proxmox-host",
  "port": 8006,
  "username": "your-username",
  "password": "your-password",
  "realm": "pve",
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
       "proxmox": {
         "url": "http://localhost:8000/mcp/",
         "headers": {
           "Authorization": "Bearer your-jwt-token"
         }
       }
     }
   }
   ```

4. **Restart Cursor** and start using Proxmox tools!

### Example Usage in Cursor

Once configured, you can ask Cursor to:

- "Show me all virtual machines on my Proxmox server"
- "Create a new VM with 4GB RAM and 2 CPU cores"
- "Start the VM named 'web-server'"
- "Show me the storage usage across all nodes"
- "Create a snapshot of VM 'database-server'"

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
python -m src.http_cli call-tool proxmox_vm_list

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

## Available Tools

### Virtual Machine Tools
- `proxmox_vm_list` - List all virtual machines
- `proxmox_vm_get_info` - Get detailed VM information
- `proxmox_vm_create` - Create a new virtual machine
- `proxmox_vm_start` - Start a virtual machine
- `proxmox_vm_stop` - Stop a virtual machine
- `proxmox_vm_shutdown` - Shutdown a virtual machine gracefully
- `proxmox_vm_reset` - Reset a virtual machine
- `proxmox_vm_delete` - Delete a virtual machine
- `proxmox_vm_snapshot_create` - Create a VM snapshot
- `proxmox_vm_snapshot_list` - List VM snapshots
- `proxmox_vm_snapshot_restore` - Restore VM from snapshot
- `proxmox_vm_migrate` - Migrate VM to another node

### Container Tools
- `proxmox_ct_list` - List all containers
- `proxmox_ct_get_info` - Get detailed container information
- `proxmox_ct_create` - Create a new container
- `proxmox_ct_start` - Start a container
- `proxmox_ct_stop` - Stop a container
- `proxmox_ct_shutdown` - Shutdown a container gracefully
- `proxmox_ct_delete` - Delete a container
- `proxmox_ct_snapshot_create` - Create a container snapshot
- `proxmox_ct_snapshot_list` - List container snapshots
- `proxmox_ct_snapshot_restore` - Restore container from snapshot

### Storage Tools
- `proxmox_storage_list` - List all storage pools
- `proxmox_storage_get_info` - Get storage information
- `proxmox_storage_create` - Create a new storage pool
- `proxmox_storage_delete` - Delete a storage pool
- `proxmox_storage_content_list` - List storage content
- `proxmox_storage_upload` - Upload file to storage

### Network Tools
- `proxmox_network_list` - List network interfaces
- `proxmox_network_get_info` - Get network interface information
- `proxmox_network_create` - Create a new network interface
- `proxmox_network_delete` - Delete a network interface

### Cluster Tools
- `proxmox_cluster_status` - Get cluster status
- `proxmox_cluster_nodes` - List cluster nodes
- `proxmox_cluster_get_node_info` - Get node information
- `proxmox_cluster_ha_groups` - List HA groups

### System Tools
- `proxmox_system_version` - Get Proxmox version
- `proxmox_system_status` - Get system status
- `proxmox_system_tasks` - List system tasks
- `proxmox_system_logs` - Get system logs

### User Tools
- `proxmox_users_list` - List all users
- `proxmox_users_get_info` - Get user information
- `proxmox_users_create` - Create a new user
- `proxmox_users_update` - Update user information
- `proxmox_users_delete` - Delete a user

## Examples

### List All VMs
```python
# Using the MCP server
result = await call_tool("proxmox_vm_list")
print(result)
```

### Create a New VM
```python
result = await call_tool("proxmox_vm_create", {
    "name": "test-vm",
    "node": "pve",
    "cores": 2,
    "memory": 4096,
    "storage": "local-lvm",
    "disk_size": "20G"
})
```

### Start a VM
```python
result = await call_tool("proxmox_vm_start", {
    "node": "pve",
    "vmid": 100
})
```

### Create a Container
```python
result = await call_tool("proxmox_ct_create", {
    "name": "web-container",
    "node": "pve",
    "ostemplate": "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz",
    "cores": 2,
    "memory": 2048,
    "storage": "local-lvm",
    "disk_size": "10G"
})
```

## Security Considerations

- **API Token Management**: Store API tokens securely and rotate them regularly
- **SSL Verification**: Always verify SSL certificates in production
- **Input Validation**: All inputs are validated and sanitized
- **Audit Logging**: All operations are logged for security auditing
- **Permission Checks**: Implement appropriate permission checks for destructive operations

## Development

### Project Structure
```
proxmox-mcp/
├── src/
│   ├── server.py              # Main MCP server
│   ├── proxmox_client.py      # Proxmox API client
│   ├── auth.py               # Authentication manager
│   ├── cli.py                # Command-line interface
│   ├── resources/            # Resource handlers
│   │   ├── base.py
│   │   ├── vm.py
│   │   ├── container.py
│   │   ├── storage.py
│   │   ├── network.py
│   │   ├── cluster.py
│   │   ├── system.py
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

- [ ] Advanced VM configuration options
- [ ] Backup and restore operations
- [ ] Performance monitoring and alerting
- [ ] Web UI for configuration
- [ ] Plugin system for custom tools
- [ ] Integration with backup solutions

## Acknowledgments

- Proxmox team for the excellent API
- MCP community for the protocol specification
- Contributors and users of this project
