# Warewulf MCP Server - Testing Status ⚠️

[![Status: Testing](https://img.shields.io/badge/Status-Testing-orange)](https://github.com/filthyrake/damens_mcps)
[![Tested: ⚠️ Testing](https://img.shields.io/badge/Tested-%E2%9A%A0%EF%B8%8F%20Testing-orange)](https://github.com/filthyrake/damens_mcps)
[![Tools: 15 Available](https://img.shields.io/badge/Tools-15%20Available-blue)](https://github.com/filthyrake/damens_mcps)

## ⚠️ **IMPORTANT: Testing Status**

**This MCP server is currently in testing status and has NOT been tested against a live Warewulf server.** 

- **Status**: Testing/Development
- **Tested**: ❌ Not yet tested
- **Compatibility**: Warewulf v4.6.0+ (API v1)
- **Use Case**: Development and testing purposes only

## 🚀 **Quick Start**

1. **Setup Environment:**
   ```bash
   ./setup.sh
   ```

2. **Configure Connection:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your Warewulf server details
   ```

3. **Start Server:**
   ```bash
   .venv/bin/python working_warewulf_server.py
   ```

4. **Test Connection:**
   ```bash
   .venv/bin/python test_server.py
   ```

## 🛠️ **Available Tools (15 Total)**

### **Core Management Tools**
- **`warewulf_test_connection`** - Test connection to Warewulf server
- **`warewulf_get_version`** - Get Warewulf version information
- **`warewulf_get_api_docs`** - Get API documentation endpoint

### **Node Management**
- **`warewulf_list_nodes`** - List all nodes in the cluster
- **`warewulf_get_node`** - Get detailed information about a specific node
- **`warewulf_create_node`** - Create a new node
- **`warewulf_update_node`** - Update an existing node
- **`warewulf_delete_node`** - Delete a node
- **`warewulf_get_node_fields`** - Get available node fields
- **`warewulf_get_node_raw`** - Get raw node configuration

### **Profile Management**
- **`warewulf_list_profiles`** - List all node profiles
- **`warewulf_get_profile`** - Get detailed information about a profile
- **`warewulf_create_profile`** - Create a new profile
- **`warewulf_update_profile`** - Update an existing profile
- **`warewulf_delete_profile`** - Delete a profile

### **Image Management**
- **`warewulf_list_images`** - List all available images
- **`warewulf_get_image`** - Get detailed information about an image
- **`warewulf_build_image`** - Build an image
- **`warewulf_import_image`** - Import an image
- **`warewulf_delete_image`** - Delete an image

### **Overlay Management**
- **`warewulf_list_overlays`** - List all overlays
- **`warewulf_get_overlay`** - Get detailed information about an overlay
- **`warewulf_create_overlay`** - Create a new overlay
- **`warewulf_delete_overlay`** - Delete an overlay
- **`warewulf_get_overlay_file`** - Get overlay file contents

### **Power Management**
- **`warewulf_power_on`** - Power on a node
- **`warewulf_power_off`** - Power off a node
- **`warewulf_power_reset`** - Reset a node
- **`warewulf_power_cycle`** - Power cycle a node
- **`warewulf_power_status`** - Get power status of a node

## 🔧 **Tool Usage Examples**

### **Create a New Node**
```json
{
  "name": "warewulf_create_node",
  "arguments": {
    "node_name": "compute-01",
    "profile": "compute",
    "ipaddr": "192.168.1.100",
    "hwaddr": "00:11:22:33:44:55"
  }
}
```

### **Get Node Information**
```json
{
  "name": "warewulf_get_node",
  "arguments": {
    "node_id": "compute-01"
  }
}
```

### **Build Node Overlays**
```json
{
  "name": "warewulf_build_node_overlays",
  "arguments": {
    "node_id": "compute-01"
  }
}
```

### **Power Management**
```json
{
  "name": "warewulf_power_on",
  "arguments": {
    "node_id": "compute-01"
  }
}
```

## 🔐 **Authentication**

The Warewulf MCP server supports authentication via:

1. **Username/Password** - Basic authentication
2. **API Token** - Token-based authentication (recommended)
3. **Environment Variables** - Secure credential storage

## 📋 **Prerequisites**

- **Warewulf Server**: v4.6.0 or later with REST API enabled
- **Python**: 3.8+
- **Network Access**: To Warewulf server (default: localhost:9873)

## 🚨 **Security Considerations**

- **API Access**: The Warewulf API provides root-level access to the server
- **Local Access Only**: API is only accessible via localhost by default
- **Credential Management**: Store credentials securely using environment variables
- **Network Security**: Ensure proper network isolation for production deployments

## 🔗 **API Reference**

For detailed API documentation, see:
- [Warewulf REST API Documentation](https://warewulf.org/docs/main/server/api.html)
- [Warewulf User Guide](https://warewulf.org/docs/main/)

## 📝 **Configuration**

### **Basic Configuration (config.json)**
```json
{
  "host": "localhost",
  "port": 9873,
  "protocol": "http",
  "username": "admin",
  "password": "your-password",
  "ssl_verify": false
}
```

### **Environment Variables (.env)**
```bash
WAREWULF_HOST=localhost
WAREWULF_PORT=9873
WAREWULF_PROTOCOL=http
WAREWULF_USERNAME=admin
WAREWULF_PASSWORD=your-password
WAREWULF_SSL_VERIFY=false
```

## 🧪 **Testing**

To test the MCP server:

1. **Unit Tests**: Run `python -m pytest tests/`
2. **Integration Tests**: Run `python test_server.py`
3. **Manual Testing**: Use the examples in `examples/` directory

## 🤝 **Contributing**

This MCP server is in active development. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ **Disclaimer**

This MCP server is provided as-is for testing and development purposes. It has not been tested against production Warewulf deployments and should not be used in production without thorough testing.
