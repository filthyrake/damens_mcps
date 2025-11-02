# 📖 iDRAC MCP Usage Guide

This guide covers how to use all features of the iDRAC MCP server, from basic operations to advanced fleet management.

## 🚀 Getting Started

### 1. Initial Setup

```bash
# Clone and setup
cd idrac-mcp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure your iDRAC
cp env.example .env
# Edit .env with your iDRAC details
```

### 2. Test Your Setup

```bash
# Quick test
python test_real_idrac.py

# Should show your server info like:
# ✅ Model: PowerEdge R730xd
# ✅ Serial: CN7792156A00OX
# ✅ Power: On
# ✅ Health: Warning
```

## 🔧 Basic Usage

### Single Server Operations

#### Using the iDRAC Client Directly

```python
import asyncio
import os
from dotenv import load_dotenv
from src.idrac_client import IDracClient

# Load configuration
load_dotenv()
config = {
    "host": os.getenv("IDRAC_HOST"),
    "port": int(os.getenv("IDRAC_PORT", "443")),
    "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
    "username": os.getenv("IDRAC_USERNAME"),
    "password": os.getenv("IDRAC_PASSWORD"),
    "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
}

async def main():
    async with IDracClient(config) as client:
        # Get system information
        system_info = await client.get_system_info()
        print(f"Model: {system_info['data']['model']}")
        
        # Get hardware inventory
        inventory = await client.get_hardware_inventory()
        print(f"Processors: {inventory['data']['processors']['count']}")
        
        # Get thermal status
        thermal = await client.get_thermal_status()
        print(f"Temperature sensors: {thermal['data']['temperatures']['count']}")

asyncio.run(main())
```

#### Using the HTTP Server

```bash
# Start the HTTP server
python -m src.http_server

# The server will be available at http://localhost:8000
# Use the API endpoints for iDRAC operations
```

#### Using the CLI

```bash
# Start the CLI
python -m src.cli

# Follow the prompts to configure and use the server
```

## 🚁 Fleet Management

### Secure Fleet Management (Recommended)

#### Initial Setup

```bash
# Initialize secure fleet management
python secure_fleet_cli.py init
# You'll be prompted for a master password for encryption
```

#### Adding Servers

```bash
# Add a server (password prompted securely)
python secure_fleet_cli.py add server1 10.0.10.11 root
# Password will be prompted with hidden input

# Add another server
python secure_fleet_cli.py add server2 10.0.10.12 root
```

#### Fleet Operations

```bash
# List all servers
python secure_fleet_cli.py list

# Test all server connections
python secure_fleet_cli.py test

# Get system information from all servers
python secure_fleet_cli.py info

# Get health status from all servers
python secure_fleet_cli.py health

# Get power status from all servers
python secure_fleet_cli.py power

# Get thermal data for specific server
python secure_fleet_cli.py thermal server1

# Check security status
python secure_fleet_cli.py security-info
```

#### Server Management

```bash
# Enable/disable servers
python secure_fleet_cli.py enable server1
python secure_fleet_cli.py disable server2

# Remove a server
python secure_fleet_cli.py remove server2
```

### Basic Fleet Management

```bash
# Initialize basic fleet management
python fleet_cli.py init

# Add servers (password will be prompted securely)
python fleet_cli.py add server1 10.0.10.11 root
# Password will be prompted with hidden input

# Same operations as secure version
python fleet_cli.py list
python fleet_cli.py test
python fleet_cli.py info
# etc.
```

**Note**: As of the latest version, `fleet_cli.py` now uses secure password prompting (just like `secure_fleet_cli.py`). The main difference is that `secure_fleet_cli.py` also encrypts passwords in the configuration file, while `fleet_cli.py` stores them in plain text.

## 📊 Data Retrieval Examples

### System Information

```python
# Get detailed system information
system_info = await client.get_system_info()
data = system_info['data']

print(f"Model: {data['model']}")
print(f"Manufacturer: {data['manufacturer']}")
print(f"Serial Number: {data['serial_number']}")
print(f"Power State: {data['power_state']}")
print(f"Health: {data['health']}")
print(f"BIOS Version: {data['bios_version']}")
```

### Hardware Inventory

```python
# Get hardware inventory
inventory = await client.get_hardware_inventory()
data = inventory['data']

print(f"Processors: {data['processors']['count']}")
for proc in data['processors']['details']:
    print(f"  - {proc['name']}: {proc['cores']} cores, {proc['threads']} threads")

print(f"Memory Modules: {data['memory_modules']['count']}")
print(f"Storage Controllers: {data['storage_controllers']['count']}")
```

### Thermal Monitoring

```python
# Get thermal status
thermal = await client.get_thermal_status()
data = thermal['data']

print(f"Temperature Sensors: {data['temperatures']['count']}")
for temp in data['temperatures']['sensors']:
    print(f"  - {temp['name']}: {temp['reading_celsius']}°C ({temp['health']})")

print(f"Fans: {data['fans']['count']}")
for fan in data['fans']['fans']:
    print(f"  - {fan['name']}: {fan['reading_rpm']} RPM ({fan['health']})")
```

### Power Status

```python
# Get power status
power = await client.get_power_status()
data = power['data']

print(f"Power State: {data['power_state']}")
print(f"Power Supplies: {data['power_supplies']['count']}")
for ps in data['power_supplies']['supplies']:
    print(f"  - {ps['name']}: {ps['status']} ({ps['health']})")
```

## 🔌 API Usage

### HTTP API Endpoints

When running the HTTP server, you can use these endpoints:

```bash
# Get system information
curl http://localhost:8000/api/system/info

# Get hardware inventory
curl http://localhost:8000/api/system/inventory

# Get thermal status
curl http://localhost:8000/api/system/thermal

# Get power status
curl http://localhost:8000/api/system/power

# Test connection
curl http://localhost:8000/api/system/test
```

### MCP Integration

For MCP (Model Context Protocol) integration:

```python
# Example MCP client usage
from mcp import ClientSession

async with ClientSession("ws://localhost:8000") as session:
    # Get system information
    result = await session.call_tool("idrac_system_info", {})
    print(result)
    
    # Get hardware inventory
    result = await session.call_tool("idrac_hardware_inventory", {})
    print(result)
```

## 🔒 Security Best Practices

### Password Management

1. **Use the secure fleet CLI** for password management
2. **Never store passwords in plain text**
3. **Use strong master passwords** for encryption
4. **Regularly rotate iDRAC passwords**

### Network Security

1. **Use HTTPS** for all iDRAC connections
2. **Enable SSL verification** when possible
3. **Use firewall rules** to restrict access
4. **Monitor access logs**

### Configuration Security

```bash
# Verify sensitive files are protected
grep -E "(fleet_servers\.json|\.fleet_key|\.env)" .gitignore

# Check for any tracked sensitive files
git status --porcelain | grep -E "(fleet_servers\.json|\.fleet_key|\.env)"

# View security status
python secure_fleet_cli.py security-info
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed:**
   ```bash
   # Check network connectivity
   ping 10.0.10.11
   
   # Check iDRAC web interface
   curl -k https://10.0.10.11/redfish/v1/
   ```

2. **Authentication Failed:**
   ```bash
   # Verify credentials
   cat .env
   
   # Test with curl
   curl -k -u root:password https://10.0.10.11/redfish/v1/
   ```

3. **SSL Certificate Issues:**
   ```bash
   # Set SSL verification to false
   echo "IDRAC_SSL_VERIFY=false" >> .env
   ```

4. **Import Errors:**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or modify test scripts to show more info
```

## 📈 Performance Optimization

### Connection Pooling

```python
# Reuse client connections
async with IDracClient(config) as client:
    # Multiple operations with same connection
    await client.get_system_info()
    await client.get_hardware_inventory()
    await client.get_thermal_status()
```

### Batch Operations

```python
# Use fleet management for bulk operations
manager = SecureMultiServerManager()
fleet_info = await manager.get_fleet_system_info()
fleet_health = await manager.get_fleet_health()
```

### Caching

```python
# Implement caching for frequently accessed data
import time
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_system_info(server_name, timestamp=None):
    # Cache system info for 5 minutes
    return system_info
```

## 🔄 Automation Examples

### Scheduled Health Checks

```python
import asyncio
import schedule
import time

async def health_check():
    manager = SecureMultiServerManager()
    fleet_health = await manager.get_fleet_health()
    
    for server, result in fleet_health.items():
        if result["status"] == "error":
            print(f"⚠️ {server}: {result['message']}")
        elif result["data"]["overall_health"] != "OK":
            print(f"⚠️ {server}: Health is {result['data']['overall_health']}")

# Schedule health checks every 5 minutes
schedule.every(5).minutes.do(lambda: asyncio.run(health_check()))

while True:
    schedule.run_pending()
    time.sleep(1)
```

### Alert System

```python
async def check_and_alert():
    manager = SecureMultiServerManager()
    fleet_health = await manager.get_fleet_health()
    
    alerts = []
    for server, result in fleet_health.items():
        if result["status"] == "error":
            alerts.append(f"❌ {server}: Connection failed")
        elif result["data"]["overall_health"] == "Critical":
            alerts.append(f"🚨 {server}: Critical health issue")
    
    if alerts:
        # Send alerts (email, Slack, etc.)
        send_alerts(alerts)
```

## 📝 Best Practices

1. **Always test in a safe environment** before production
2. **Use the secure fleet CLI** for password management
3. **Monitor system resources** during operations
4. **Implement proper error handling** in your scripts
5. **Keep encryption keys secure** and backed up
6. **Regularly update dependencies** and firmware
7. **Document your configurations** and procedures
8. **Use version control** for your scripts (not passwords)

## 🆘 Getting Help

- **Check the testing guide** for troubleshooting steps
- **Review the security warning** for important security information
- **Check the examples** in the `examples/` directory
- **Create an issue** with detailed error information
- **Check the logs** for detailed error messages

---

**Remember:** Always test power management commands in a safe environment first!
