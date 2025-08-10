# 🚀 Complete Setup Guide for Damen's MCP Servers

This guide will walk you through setting up and using any of the MCP servers in this collection.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Detailed Setup by Project](#detailed-setup-by-project)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

## 🔧 Prerequisites

### System Requirements

- **Python 3.8+** (Python 3.11+ recommended)
- **Git** for cloning the repository
- **Network access** to your target systems
- **API credentials** for each platform

### Platform-Specific Requirements

| Platform | Requirements |
|----------|--------------|
| **pfSense** | pfSense 2.6+ with API access enabled |
| **TrueNAS** | TrueNAS SCALE 22.02+ or CORE 13+ |
| **iDRAC** | Dell PowerEdge server with iDRAC 8+ |
| **Proxmox** | Proxmox VE 7.0+ with API access |

## ⚡ Quick Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd damens_mcps
```

### 2. Choose Your Project

```bash
# For pfSense (Production Ready)
cd pfsense-mcp

# For TrueNAS (Production Ready)
cd truenas-mcp

# For iDRAC (Production Ready)
cd idrac-mcp

# For Proxmox (Untested - Use with caution)
cd proxmox-mcp
```

### 3. Set Up Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure

```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env  # or use your preferred editor
```

### 5. Start the Server

```bash
# Method varies by project - check individual READMEs
python -m src.http_server
# OR
python -m src.cli serve
```

## 📖 Detailed Setup by Project

### 🔥 pfSense MCP (Production Ready)

**Best for:** Firewall and network management

#### Setup Steps:

1. **Enable pfSense API:**
   - Log into pfSense web interface
   - Go to System → API
   - Enable API access
   - Create an API key

2. **Configure environment:**
   ```bash
   cd pfsense-mcp
   cp env.example .env
   ```

3. **Edit `.env`:**
   ```env
   PFSENSE_HOST=192.168.1.1
   PFSENSE_USERNAME=admin
   PFSENSE_PASSWORD=your-password
   PFSENSE_API_KEY=your-api-key
   PFSENSE_SSL_VERIFY=true
   ```

4. **Start server:**
   ```bash
   python -m src.http_server
   ```

#### Testing:
```bash
python examples/basic_usage.py
```

### 💾 TrueNAS MCP (Production Ready)

**Best for:** Storage and NAS management

#### Setup Steps:

1. **Create API Key in TrueNAS:**
   - Log into TrueNAS web interface
   - Go to Credentials → API Keys
   - Create a new API key with appropriate permissions

2. **Configure environment:**
   ```bash
   cd truenas-mcp
   cp env.example .env
   ```

3. **Edit `.env`:**
   ```env
   TRUENAS_HOST=192.168.1.100
   TRUENAS_API_KEY=your-api-key
   TRUENAS_USERNAME=admin
   TRUENAS_PASSWORD=your-password
   SECRET_KEY=your-generated-secret-key
   ```

4. **Start server:**
   ```bash
   python -m src.http_server
   ```

#### Testing:
```bash
python examples/basic_usage.py
```

### ✅ iDRAC MCP (Production Ready)

**✅ STATUS: This project is now production ready and fully tested!**

#### Setup Steps:

1. **Enable iDRAC API:**
   - Access iDRAC web interface
   - Enable API access in iDRAC settings
   - Note down iDRAC IP and credentials

2. **Configure environment:**
   ```bash
   cd idrac-mcp
   cp config.example.json config.json
   ```

3. **Edit `config.json`:**
   ```json
   {
     "idrac_servers": {
       "server1": {
         "name": "Production Server 1",
         "host": "192.168.1.100",
         "port": 443,
         "protocol": "https",
         "username": "root",
         "password": "your-password",
         "ssl_verify": false
       }
     },
     "default_server": "server1",
     "server": {
       "port": 8000,
       "debug": true
     }
   }
   ```

4. **Start server:**
   ```bash
   python working_mcp_server.py
   ```

#### Testing:
```bash
python test_server.py
```

### ⚠️ Proxmox MCP (Untested)

**⚠️ WARNING: This project is untested. Use with extreme caution!**

#### Setup Steps:

1. **Enable Proxmox API:**
   - Log into Proxmox web interface
   - Go to Datacenter → Permissions → API Tokens
   - Create a new API token

2. **Configure environment:**
   ```bash
   cd proxmox-mcp
   cp env.example .env
   ```

3. **Edit `.env`:**
   ```env
   PROXMOX_HOST=192.168.1.100
   PROXMOX_PORT=8006
   PROXMOX_USERNAME=your-username
   PROXMOX_PASSWORD=your-password
   PROXMOX_API_TOKEN=your-api-token
   SECRET_KEY=your-generated-secret-key
   ```

4. **Start server:**
   ```bash
   python -m src.cli serve
   ```

#### Testing:
```bash
python tests/test_basic.py
```

## ⚙️ Configuration

### Configuration Methods

**iDRAC MCP** now uses `config.json` files instead of environment variables for better multi-server support and security.

**Other projects** continue to use environment variables for configuration.

### Environment Variables (pfSense, TrueNAS, Proxmox)

Each project uses environment variables for configuration. Here are the common ones:

#### Connection Settings
```env
# Host/IP address of your system
HOST=192.168.1.100

# Port number (varies by system)
PORT=443

# Protocol (http/https)
PROTOCOL=https

# SSL verification
SSL_VERIFY=true
```

#### Authentication
```env
# Username for API access
USERNAME=admin

# Password (use API keys when possible)
PASSWORD=your-password

# API key (preferred over password)
API_KEY=your-api-key
```

#### Server Settings
```env
# JWT secret key for MCP authentication
SECRET_KEY=your-generated-secret-key

# Server port for MCP server
SERVER_PORT=8000

# Log level
LOG_LEVEL=INFO
```

### Security Configuration

#### Generate Secure Secret Keys

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use OpenSSL
openssl rand -hex 32
```

#### SSL/TLS Configuration

```env
# Enable SSL verification
SSL_VERIFY=true

# Custom CA certificate path (if needed)
SSL_CA_CERT=/path/to/ca-cert.pem

# Client certificate (if required)
SSL_CLIENT_CERT=/path/to/client-cert.pem
SSL_CLIENT_KEY=/path/to/client-key.pem
```

## 🧪 Testing

### Basic Health Checks

```bash
# Check if server is running
curl http://localhost:8000/health

# Get server status
curl http://localhost:8000/status

# Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

### Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_basic.py

# Run with verbose output
python -m pytest -v tests/
```

### Integration Tests

```bash
# Test with actual system (be careful!)
python examples/basic_usage.py

# Test specific functionality
python test_server.py
```

### Manual Testing

1. **Start the server** in one terminal
2. **Use curl or Postman** to test endpoints
3. **Check logs** for any errors
4. **Verify responses** match expected format

## 🔧 Troubleshooting

### Common Issues

#### Connection Errors

**Problem:** Cannot connect to target system
```bash
# Check network connectivity
ping 192.168.1.100

# Check if port is open
telnet 192.168.1.100 443

# Test with curl
curl -k https://192.168.1.100/api/v1/system/info
```

**Solutions:**
- Verify IP address and port
- Check firewall settings
- Ensure API is enabled on target system
- Try with `SSL_VERIFY=false` for testing

#### Authentication Errors

**Problem:** 401 Unauthorized errors
```bash
# Check credentials
echo $USERNAME
echo $PASSWORD

# Test authentication manually
curl -u username:password https://host/api/endpoint
```

**Solutions:**
- Verify username/password
- Check API key format
- Ensure user has proper permissions
- Try regenerating API key

#### Import Errors

**Problem:** Module not found errors
```bash
# Check Python environment
python --version
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check virtual environment
echo $VIRTUAL_ENV
```

**Solutions:**
- Activate virtual environment
- Install missing dependencies
- Check Python version compatibility
- Clear pip cache: `pip cache purge`

#### Port Already in Use

**Problem:** Port 8000 already in use
```bash
# Check what's using the port
lsof -i :8000

# Kill process using port
kill -9 <PID>

# Or use different port
export SERVER_PORT=8001
```

### Debug Mode

Enable debug logging:

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Start server with debug output
python -m src.http_server --debug

# Or check logs
tail -f logs/server.log
```

### Getting Help

1. **Check the logs** for error messages
2. **Review the README** in each project directory
3. **Test with examples** in the `examples/` folder
4. **Create an issue** on GitHub with:
   - Error messages
   - System information
   - Steps to reproduce

## 🔒 Security Best Practices

### Before Production Use

1. **Change Default Passwords**
   ```bash
   # Update all default passwords in .env
   PASSWORD=strong-password-here
   SECRET_KEY=generated-secret-key
   ```

2. **Use API Keys Instead of Passwords**
   ```env
   # Prefer API keys over passwords
   API_KEY=your-api-key
   # PASSWORD=  # Comment out password
   ```

3. **Enable SSL/TLS**
   ```env
   PROTOCOL=https
   SSL_VERIFY=true
   ```

4. **Restrict Network Access**
   ```bash
   # Use firewall rules to restrict access
   ufw allow from 192.168.1.0/24 to any port 8000
   ```

5. **Use Environment Variables**
   ```bash
   # Don't hardcode credentials in scripts
   export PASSWORD=$(cat /path/to/password-file)
   ```

### Monitoring and Logging

```bash
# Monitor server logs
tail -f logs/server.log

# Check for failed login attempts
grep "401" logs/server.log

# Monitor system resources
htop
```

### Regular Maintenance

1. **Update Dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Rotate API Keys**
   - Generate new API keys regularly
   - Update configuration files
   - Remove old keys from systems

3. **Backup Configuration**
   ```bash
   # Backup your .env files
   cp .env .env.backup.$(date +%Y%m%d)
   ```

4. **Security Audits**
   - Review access logs regularly
   - Check for unauthorized access
   - Update security policies

## 📚 Additional Resources

### Documentation
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [pfSense Documentation](https://docs.netgate.com/)
- [TrueNAS Documentation](https://www.truenas.com/docs/)
- [Dell iDRAC Documentation](https://www.dell.com/support/manuals/)
- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/)

### Examples and Tutorials
- Check `examples/` directories in each project
- Review test files for usage patterns
- Look at individual project READMEs

### Support
- Create GitHub issues for bugs
- Check existing issues for solutions
- Review project documentation

---

**Happy Infrastructure Management! 🎉**

Remember: Start with the production-ready projects (pfSense, TrueNAS, iDRAC) and be very careful with the untested ones (Proxmox).
