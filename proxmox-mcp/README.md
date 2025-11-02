# Proxmox MCP Server - Production Ready ✅

[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/filthyrake/damens_mcps)
[![Tested: ✅ Working](https://img.shields.io/badge/Tested-%E2%9C%85%20Working-brightgreen)](https://github.com/filthyrake/damens_mcps)
[![Tools: 21 Available](https://img.shields.io/badge/Tools-21%20Available-blue)](https://github.com/filthyrake/damens_mcps)

## 🚀 **Quick Start**

1. **Setup Environment:**
   ```bash
   ./setup.sh
   ```

2. **Configure Connection:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your Proxmox details
   ```

3. **🔒 Secure Your Credentials (Recommended):**
   ```bash
   # Migrate to encrypted password storage
   python migrate_config.py
   
   # Set master password
   export PROXMOX_MASTER_PASSWORD='your-master-password'
   ```

4. **Start Server:**
   ```bash
   .venv/bin/python working_proxmox_server.py
   ```

5. **Test Connection:**
   ```bash
   .venv/bin/python test_server.py
   ```

## 🛠️ **Available Tools (21 Total)**

### **Core Management Tools**
- **`proxmox_test_connection`** - Test connection to Proxmox server
- **`proxmox_get_version`** - Get Proxmox version information
- **`proxmox_list_nodes`** - List all nodes in the cluster

### **Node Management**
- **`proxmox_get_node_status`** - Get detailed status and resource usage for a specific node

### **Virtual Machine Management**
- **`proxmox_list_vms`** - List all virtual machines (optionally filtered by node)
- **`proxmox_get_vm_info`** - Get detailed information about a specific VM
- **`proxmox_get_vm_status`** - Get current status and resource usage of a VM
- **`proxmox_create_vm`** - Create a new virtual machine with configurable resources
- **`proxmox_start_vm`** - Start a virtual machine
- **`proxmox_stop_vm`** - Stop a virtual machine
- **`proxmox_suspend_vm`** - Suspend a running virtual machine
- **`proxmox_resume_vm`** - Resume a suspended virtual machine
- **`proxmox_delete_vm`** - Delete a virtual machine

### **Container Management**
- **`proxmox_list_containers`** - List all containers (optionally filtered by node)
- **`proxmox_start_container`** - Start a container
- **`proxmox_stop_container`** - Stop a container

### **Storage Management**
- **`proxmox_list_storage`** - List all storage pools (optionally filtered by node)
- **`proxmox_get_storage_usage`** - Get storage usage and capacity information

### **Snapshot Management**
- **`proxmox_create_snapshot`** - Create a snapshot of a VM or container
- **`proxmox_list_snapshots`** - List snapshots for a VM or container

## 🔧 **Tool Usage Examples**

### **Create a New VM**
```json
{
  "name": "proxmox_create_vm",
  "arguments": {
    "node": "pve",
    "name": "test-vm",
    "cores": "2",
    "memory": "1024"
  }
}
```

### **Get Node Status**
```json
{
  "name": "proxmox_get_node_status",
  "arguments": {
    "node": "pve"
  }
}
```

### **Create Snapshot**
```json
{
  "name": "proxmox_create_snapshot",
  "arguments": {
    "node": "pve",
    "vmid": "100",
    "snapname": "backup-2024-01-15",
    "description": "Monthly backup snapshot"
  }
}
```

## 📋 **Configuration**

### **config.json Structure**
```json
{
  "host": "your-proxmox-host",
  "username": "your-username",
  "password": "your-password",
  "realm": "pam",
  "port": 8006,
  "ssl_verify": false
}
```

### **Environment Variables (Optional)**
```bash
PROXMOX_HOST=your-proxmox-host
PROXMOX_USERNAME=your-username
PROXMOX_PASSWORD=your-password
PROXMOX_REALM=pam
PROXMOX_PORT=8006
PROXMOX_SSL_VERIFY=false
```

## 🔒 **Security Features**

### **Encrypted Password Storage** ✅
- **Password encryption at rest** using PBKDF2-SHA256 (480k iterations, OWASP 2023)
- **No encryption key on disk** - derived from master password each session
- **Migration tool** - Easy conversion: `python migrate_config.py`
- **Backward compatible** - Plaintext configs still work (with warnings)

### **Additional Security**
- **No Hardcoded Credentials** - All credentials loaded from config or environment
- **SSL Verification** - Configurable SSL certificate validation
- **Authentication** - Secure ticket-based authentication with Proxmox
- **Input Validation** - All tool inputs validated before execution

### **Configuration Security**

**Recommended: Encrypted Password Storage**
```bash
# One-time setup
python migrate_config.py

# Start server with encrypted config
export PROXMOX_MASTER_PASSWORD='your-master-password'
.venv/bin/python working_proxmox_server.py
```

**Legacy: Plaintext Storage** (deprecated)
```json
{
  "password": "plaintext-password"  // ⚠️ NOT RECOMMENDED
}
```

See [SECURITY.md](SECURITY.md) for detailed security best practices.

## 🧪 **Testing**

### **Test Server**
```bash
.venv/bin/python test_server.py
```

### **Manual Testing**
```bash
# Start server
.venv/bin/python working_proxmox_server.py

# In another terminal, test tools
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | .venv/bin/python working_proxmox_server.py
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Connection Failed**
   - Check host/IP address
   - Verify username/password
   - Ensure Proxmox server is running
   - Check firewall settings

2. **Authentication Error**
   - Verify realm setting (usually "pam")
   - Check username/password combination
   - Ensure user has appropriate permissions

3. **Encrypted Config Issues**
   - **"Master password required" error**: Set `PROXMOX_MASTER_PASSWORD` environment variable
   - **"Failed to decrypt password" error**: Wrong master password or corrupted config
   - **Migration fails**: Ensure config.json has `password` field before migration

4. **SSL Issues**
   - Set `ssl_verify: false` for self-signed certificates
   - Check certificate validity

5. **Tool Not Found**
   - Restart Claude Desktop completely
   - Verify server is running
   - Check tool names match exactly

### **Debug Mode**
Enable debug logging by setting environment variable:
```bash
export DEBUG=1
```

## 📚 **Technical Details**

### **Architecture**
- **Pure JSON-RPC Server** - No external MCP library dependencies
- **ProxmoxClient Class** - Handles all Proxmox API interactions
- **Tool Router** - Routes tool calls to appropriate client methods
- **Response Formatter** - Ensures Claude Desktop compatibility

### **Dependencies**
- `requests` - HTTP client for Proxmox API
- `urllib3` - HTTP library with SSL support
- `python-dotenv` - Environment variable loading

### **MCP Protocol Compliance**
- **Tools List** - Returns all available tools with `inputSchema`
- **Tool Calls** - Handles tool execution with proper error handling
- **Response Format** - Uses `content`/`isError` structure for Claude Desktop
- **Error Handling** - Graceful handling of all MCP protocol methods

## ✅ **Production Ready Status**

This Proxmox MCP server has been **thoroughly tested and verified working** with real Proxmox VE environments. All 21 tools have been validated and include comprehensive error handling, input validation, and security features.

## 🚀 **What's New in This Version**

### **Enhanced Tool Coverage**
- **12 New Tools** added for comprehensive Proxmox management
- **VM Lifecycle Management** - Create, suspend, resume, delete operations
- **Container Management** - Start/stop container operations
- **Storage Monitoring** - Detailed storage usage information
- **Snapshot Management** - Create and list snapshots for VMs/containers

### **Improved Functionality**
- **Auto VMID Assignment** - Automatically finds next available VM ID
- **Enhanced Error Handling** - Better error messages and status reporting
- **Resource Configuration** - Configurable CPU cores and memory for new VMs
- **Multi-format Support** - Handles both VMs and containers seamlessly

### **Better Integration**
- **Claude Desktop Ready** - All tools include proper `inputSchema`
- **Standardized Responses** - Consistent response format across all tools
- **Input Validation** - Proper parameter validation for all tools
- **Error Reporting** - Clear error messages with proper error flags

## 📈 **Performance & Reliability**

- **Connection Pooling** - Efficient HTTP connection management
- **Error Recovery** - Graceful handling of network issues
- **Resource Management** - Proper cleanup of resources
- **Logging** - Comprehensive debug logging for troubleshooting

## 🔮 **Future Enhancements**

- **Cluster Management** - Multi-node cluster operations
- **Backup Management** - Automated backup creation and restoration
- **Resource Monitoring** - Real-time resource usage tracking
- **Template Management** - VM template creation and deployment
- **Network Management** - Network configuration and monitoring

---

**🎯 This production-ready Proxmox MCP server provides comprehensive management capabilities for your Proxmox VE environment, with 21 tested tools covering all major operations you need for day-to-day management. Ready for production use!**
