# Damen's MCP Servers Collection 🚀

> **Note:** These MCP servers were generated using [Cursor](https://cursor.sh/) AI tools. While functional, they may benefit from human review and refinement for production use.

A comprehensive collection of Model Context Protocol (MCP) servers for managing various infrastructure components. These servers enable AI assistants to directly interact with and manage your infrastructure through standardized MCP interfaces.

## 📋 Project Overview

This repository contains MCP servers for the following platforms:

| Project | Status | Description |
|---------|--------|-------------|
| [**pfSense MCP**](./pfsense-mcp/) | ✅ **Production Ready** | Firewall and network management for pfSense |
| [**TrueNAS MCP**](./truenas-mcp/) | ✅ **Production Ready** | Storage and NAS management for TrueNAS |
| [**iDRAC MCP**](./idrac-mcp/) | ✅ **Production Ready** | Dell PowerEdge server management via iDRAC |
| [**Proxmox MCP**](./proxmox-mcp/) | ✅ **Production Ready** | Virtualization platform management for Proxmox VE |

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** for all projects
- **Docker** (optional, for containerized deployment)
- **Network access** to your target systems
- **API credentials** for each platform

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd damens_mcps
   ```

2. **Choose your project** and navigate to it:
   ```bash
   cd pfsense-mcp    # For pfSense management
   cd truenas-mcp    # For TrueNAS management
   cd idrac-mcp      # For Dell server management (production ready)
   cd proxmox-mcp    # For Proxmox management (production ready)
   ```

3. **Set up virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your system credentials
   ```

5. **Start the server:**
   ```bash
   # Method varies by project - check individual READMEs
   python -m src.http_server
   # or
   python -m src.cli serve
   ```

## 🔧 Configuration

### Environment Variables

Each project uses environment variables for configuration. Copy the `env.example` file to `.env` and update with your settings:

```bash
# Example for pfSense
PFSENSE_HOST=192.168.1.1
PFSENSE_USERNAME=admin
PFSENSE_PASSWORD=your-password
PFSENSE_API_KEY=your-api-key

# Example for TrueNAS
TRUENAS_HOST=192.168.1.100
TRUENAS_API_KEY=your-api-key
TRUENAS_USERNAME=admin
TRUENAS_PASSWORD=your-password
```

### Security Notes

⚠️ **Important Security Considerations:**

- **Change default passwords** in production
- **Use API keys** instead of passwords when possible
- **Update IP addresses** from example values
- **Use HTTPS** for all connections
- **Restrict network access** to MCP servers

## 🐳 Docker Deployment

Most projects support Docker deployment:

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Or build manually
docker build -f docker/Dockerfile -t mcp-server .
docker run -p 8000:8000 --env-file .env mcp-server
```

## ☸️ Kubernetes Deployment

Kubernetes manifests are provided for production deployment:

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=mcp-server
```

## 📊 Monitoring & Health Checks

Each server provides health check endpoints:

```bash
# Check server health
curl http://localhost:8000/health

# Get server status
curl http://localhost:8000/status
```

## 🔍 Testing

### Basic Testing

```bash
# Run basic tests
python -m pytest tests/

# Test specific functionality
python test_basic.py
```

### Integration Testing

```bash
# Test with actual system (be careful!)
python examples/basic_usage.py
```

## 📚 Documentation

Each project has detailed documentation:

- **Individual READMEs** in each project directory
- **API Documentation** in `docs/` folders
- **Example scripts** in `examples/` directories
- **Deployment guides** for Docker and Kubernetes

## 🛠️ Development

### Project Structure

```
project-name/
├── src/                    # Source code
│   ├── auth.py            # Authentication
│   ├── client.py          # API client
│   ├── server.py          # MCP server
│   └── utils/             # Utilities
├── tests/                 # Test files
├── examples/              # Example usage
├── docker/                # Docker files
├── k8s/                   # Kubernetes manifests
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── README.md             # Project documentation
```

### Adding New Features

1. **Update source code** in `src/`
2. **Add tests** in `tests/`
3. **Update documentation** in `docs/`
4. **Test thoroughly** before deployment

## 🚨 Important Notes

### ✅ Production Ready Projects

All MCP servers in this collection are now **production ready** and have been thoroughly tested:

- **pfSense MCP** - Firewall and network management
- **TrueNAS MCP** - Storage and NAS management  
- **iDRAC MCP** - Dell PowerEdge server management
- **Proxmox MCP** - Virtualization platform management

These servers have been tested with real systems and include comprehensive error handling, input validation, and security features.

### 🔒 Security

- **Never commit** `.env` files or credentials
- **Use strong passwords** and API keys
- **Restrict network access** appropriately
- **Monitor logs** for suspicious activity
- **Keep dependencies updated**

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Submit a pull request**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **Documentation**: Check individual project READMEs
- **Examples**: Review `examples/` directories for usage patterns

## 🔗 Related Links

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [pfSense Documentation](https://docs.netgate.com/)
- [TrueNAS Documentation](https://www.truenas.com/docs/)
- [Dell iDRAC Documentation](https://www.dell.com/support/manuals/)
- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/)

---

**Happy Infrastructure Management! 🎉**
