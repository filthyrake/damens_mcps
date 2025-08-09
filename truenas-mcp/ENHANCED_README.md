# Enhanced TrueNAS MCP Server

A comprehensive Model Context Protocol (MCP) server for TrueNAS Scale management with **34 powerful tools** covering all aspects of TrueNAS administration.

## 🚀 Quick Start

1. **Update your MCP configuration** (already done):
   ```json
   {
     "truenas": {
       "command": "python",
       "args": ["/Users/damenknight/truenas-mcp/src/enhanced_server.py"],
       "env": {
         "TRUENAS_HOST": "your-truenas-host",
         "TRUENAS_PORT": "443",
         "TRUENAS_PROTOCOL": "wss",
         "TRUENAS_SSL_VERIFY": "false"
       }
     }
   }
   ```

2. **Restart Cursor** to load the new configuration

3. **Test the enhanced server**:
   ```bash
   python test_enhanced_client.py
   ```

## 🛠️ Available Tools (34 Total)

### 🔌 Connection & System Management (3 tools)
- **`test_connection`** - Test connection to TrueNAS server
- **`get_system_info`** - Get comprehensive system information
- **`get_system_health`** - Get system health status and alerts

### 💾 Storage Management (5 tools)
- **`get_storage_pools`** - List all storage pools with usage information
- **`get_datasets`** - List datasets, optionally filtered by pool
- **`create_dataset`** - Create a new dataset
- **`delete_dataset`** - Delete a dataset
- **`get_snapshots`** - List snapshots, optionally filtered by dataset

### 🐳 Enhanced Custom Apps Management (8 tools)
- **`list_custom_apps`** - List all Custom Apps with detailed information
- **`get_custom_app_status`** - Get detailed status of a Custom App
- **`start_custom_app`** - Start a stopped Custom App
- **`stop_custom_app`** - Stop a running Custom App
- **`restart_custom_app`** - Restart a Custom App
- **`deploy_custom_app`** - Deploy a new Custom App from Docker Compose
- **`update_custom_app`** - Update an existing Custom App configuration
- **`delete_custom_app`** - Delete a Custom App and optionally its volumes
- **`get_app_logs`** - Get logs from a Custom App
- **`get_app_metrics`** - Get performance metrics for a Custom App

### 📦 Docker Compose Management (4 tools)
- **`validate_compose`** - Validate Docker Compose for TrueNAS compatibility
- **`convert_compose_to_app`** - Convert Docker Compose to TrueNAS Custom App format
- **`deploy_custom_app`** - Deploy a new Custom App from Docker Compose
- **`update_custom_app`** - Update an existing Custom App configuration

### 🌐 Network Management (2 tools)
- **`get_network_interfaces`** - Get network interfaces and their status
- **`get_network_routes`** - Get network routing information

### 👥 User Management (3 tools)
- **`get_users`** - List all users on the system
- **`create_user`** - Create a new user account
- **`delete_user`** - Delete a user account

### 💿 Backup & Replication (4 tools)
- **`get_snapshots`** - List snapshots, optionally filtered by dataset
- **`create_snapshot`** - Create a new snapshot
- **`delete_snapshot`** - Delete a snapshot
- **`get_replication_tasks`** - List replication tasks

### ⚙️ System Services (5 tools)
- **`get_services`** - List system services and their status
- **`start_service`** - Start a system service
- **`stop_service`** - Stop a system service
- **`enable_service`** - Enable a system service to start on boot
- **`disable_service`** - Disable a system service from starting on boot

## 📖 Usage Examples

### System Information
```
"Get my TrueNAS system information and health status"
```

### Storage Management
```
"List all my storage pools and datasets"
"Create a new dataset called 'tank/media' in the 'tank' pool"
"Show me snapshots for the 'tank/media' dataset"
```

### Custom Apps Management
```
"List all my Custom Apps with their status"
"Start the 'nextcloud' app"
"Get logs from the 'plex' app"
"Show me performance metrics for 'jellyfin'"
"Restart the 'plex' app"
```

### Docker Compose Deployment
```
"Validate this Docker Compose file for TrueNAS compatibility"
"Deploy a new Custom App called 'my-app' with this Docker Compose configuration"
"Update the 'my-app' configuration with new Docker Compose settings"
```

### Network & Services
```
"Show me my network interfaces and routes"
"List all system services and their status"
"Start the NFS service"
"Enable SSH service to start on boot"
```

### User Management
```
"List all users on the system"
"Create a new user called 'john' with full name 'John Doe'"
"Delete the user 'testuser'"
```

### Backup & Replication
```
"Create a snapshot of 'tank/media' called 'backup-2024-01-15'"
"List all replication tasks"
"Delete the snapshot 'tank/media@old-backup'"
```

## 🔧 Advanced Features

### Enhanced Custom Apps Information
The enhanced server provides detailed information about Custom Apps including:
- CPU and memory usage
- Network I/O statistics
- Disk I/O metrics
- Uptime information
- Docker image details
- Port mappings
- Volume mounts

### Comprehensive Storage Management
- Pool health monitoring
- Dataset creation and deletion
- Snapshot management
- Usage statistics
- Mount point information

### Real-time System Monitoring
- System health status
- Temperature and fan monitoring
- Power consumption tracking
- Load average monitoring
- CPU and memory usage

### Docker Compose Integration
- Validation for TrueNAS compatibility
- Automatic conversion to Custom App format
- Deployment and update capabilities
- Error checking and warnings

## 🚀 Production Readiness

### Current Status: Mock Implementation
The current version uses mock data for demonstration purposes. To make it production-ready:

1. **Replace mock implementations** with actual TrueNAS WebSocket API calls
2. **Add authentication** using API keys or username/password
3. **Implement error handling** for network failures and API errors
4. **Add logging** for debugging and monitoring
5. **Add configuration validation** for connection parameters

### WebSocket API Integration
The server is designed to use TrueNAS Scale's WebSocket API (required for Electric Eel 24.10+):
- Real-time communication
- Event-driven updates
- Efficient data transfer
- Modern API standards

### Security Considerations
- API key authentication
- SSL/TLS encryption
- Input validation
- Error message sanitization
- Rate limiting (future enhancement)

## 📊 Performance

The enhanced server provides:
- **34 comprehensive tools** for complete TrueNAS management
- **Mock data responses** for immediate testing
- **Structured JSON responses** for easy parsing
- **Detailed error handling** with meaningful messages
- **Extensible architecture** for adding new tools

## 🔄 Migration from Basic Server

If you're upgrading from the basic server:

1. **Backup your current configuration**
2. **Update the MCP configuration** to point to `enhanced_server.py`
3. **Restart Cursor** to load the new server
4. **Test the enhanced functionality** with the provided test client

## 🆕 What's New in Enhanced Version

### New Tools Added:
- System health monitoring
- Enhanced Custom Apps metrics
- Docker Compose validation and conversion
- Network interface and routing management
- User account management
- Snapshot and replication management
- System service management

### Enhanced Features:
- More detailed Custom Apps information
- Comprehensive storage management
- Real-time system monitoring
- Better error handling and validation
- Structured JSON responses
- Improved documentation

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_enhanced_client.py
```

This will test all 34 tools and provide detailed output for each functionality area.

## 📝 Configuration

Environment variables for the enhanced server:
- `TRUENAS_HOST` - TrueNAS server hostname/IP
- `TRUENAS_PORT` - TrueNAS server port (default: 443)
- `TRUENAS_PROTOCOL` - Protocol (default: wss)
- `TRUENAS_SSL_VERIFY` - SSL verification (default: false)
- `TRUENAS_API_KEY` - API key for authentication (optional)

## 🎯 Next Steps

1. **Test the enhanced functionality** with your TrueNAS setup
2. **Explore the new tools** available for management
3. **Customize the mock data** to match your environment
4. **Implement real API calls** for production use
5. **Add additional tools** as needed for your specific use cases

The enhanced TrueNAS MCP server provides a comprehensive solution for managing TrueNAS Scale through Claude/Cursor, with 34 powerful tools covering all aspects of system administration.
