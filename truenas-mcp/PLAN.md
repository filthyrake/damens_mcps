# TrueNAS MCP Server Project Plan

## Overview
Build a Model Context Protocol (MCP) server that provides an interface between Cursor (and other AI tools) and TrueNAS Scale server (version 25.04.2). This will enable AI assistants to query system information, manage storage, configure services, and perform administrative tasks on TrueNAS Scale.

## NEW ARCHITECTURE: Portable HTTP-based MCP Server

### Design Goals
- **Portable**: Can run on any host (local, remote, cloud, container)
- **HTTP-based**: Accessible via HTTP/HTTPS like GitHub MCP servers
- **Standalone**: Self-contained executable with minimal dependencies
- **Configurable**: Easy configuration via environment variables or config files
- **Secure**: Proper authentication and authorization
- **Scalable**: Can handle multiple concurrent connections

### Architecture Components
1. **HTTP Server**: FastAPI-based web server exposing MCP endpoints
2. **MCP Protocol Handler**: Handles MCP protocol over HTTP
3. **TrueNAS Client**: Async client for TrueNAS Scale API
4. **Authentication**: JWT-based authentication for MCP clients
5. **Configuration**: Environment-based configuration
6. **Docker Support**: Containerized deployment
7. **CLI Tools**: Command-line utilities for management

### Deployment Options
- **Local Development**: Run locally for development
- **Remote Server**: Deploy on any server/VM
- **Cloud Deployment**: Deploy on AWS, GCP, Azure
- **Container**: Docker container deployment
- **Kubernetes**: K8s deployment for scaling

## Project Goals
- Create a secure, portable MCP server that can authenticate with TrueNAS Scale
- Provide comprehensive access to TrueNAS API endpoints
- Enable AI tools to query system status, storage pools, datasets, services, etc.
- Allow AI tools to perform administrative tasks (with appropriate safeguards)
- Implement proper error handling and logging
- Follow MCP protocol standards and best practices
- Support multiple deployment scenarios

## Technical Architecture

### Core Components
1. **HTTP MCP Server** - FastAPI server handling MCP protocol over HTTP
2. **TrueNAS API Client** - REST API client for TrueNAS Scale
3. **Authentication Manager** - JWT-based auth for MCP clients
4. **Resource Handlers** - Specific handlers for different TrueNAS resources
5. **Configuration Manager** - Environment and file-based configuration
6. **Docker Support** - Containerization for easy deployment

### Key Features
- **System Information**: Query system status, version, hardware info
- **Storage Management**: Pools, datasets, snapshots, replication
- **Network Configuration**: Interfaces, routes, services
- **Service Management**: SMB, NFS, iSCSI, Docker, Kubernetes
- **User Management**: Local users, groups, permissions
- **Monitoring**: System metrics, alerts, logs
- **Backup & Recovery**: Backup tasks, restore operations

## Implementation Phases

### Phase 1: Foundation (Week 1) ✅
- [x] Set up project structure and dependencies
- [x] Implement basic MCP server framework
- [x] Create TrueNAS API client with authentication
- [x] Add basic system information queries
- [x] Set up logging and error handling

### Phase 2: Core Resources (Week 2) ✅
- [x] Implement storage pool and dataset management
- [x] Add user and group management
- [x] Create network configuration handlers
- [x] Add service status and control functions
- [x] Implement safety validations

### Phase 3: Advanced Features (Week 3) ✅
- [x] Add monitoring and metrics collection
- [x] Implement backup and replication management
- [x] Create snapshot management
- [x] Add Docker/Kubernetes integration
- [x] Implement audit logging

### Phase 4: HTTP Server & Portability (Week 4) ✅
- [x] Convert to HTTP-based MCP server using FastAPI
- [x] Implement JWT authentication for MCP clients
- [x] Add configuration management for multiple environments
- [x] Create Docker containerization
- [x] Add health checks and monitoring endpoints

### Phase 5: Deployment & Documentation (Week 5) ✅
- [x] Create deployment guides for different scenarios
- [x] Add Kubernetes manifests
- [x] Implement configuration validation
- [x] Add comprehensive API documentation
- [x] Create example configurations for different setups

## Security Considerations
- JWT-based authentication for MCP clients
- API key management and rotation for TrueNAS
- Input validation and sanitization
- Rate limiting for API calls
- Audit logging for all operations
- Permission-based access control
- Secure credential storage
- HTTPS enforcement in production

## Dependencies
- Python 3.8+
- FastAPI (for HTTP server)
- MCP Python SDK
- aiohttp (for API calls)
- pydantic (for data validation)
- python-dotenv (for configuration)
- rich (for CLI interface)
- uvicorn (for ASGI server)
- docker (for containerization)

## File Structure
```
truenas-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # FastAPI HTTP server
│   ├── mcp_handler.py         # MCP protocol handler
│   ├── truenas_client.py      # TrueNAS API client
│   ├── auth.py               # JWT authentication
│   ├── config.py             # Configuration management
│   ├── resources/            # Resource handlers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── system.py
│   │   ├── storage.py
│   │   ├── network.py
│   │   ├── services.py
│   │   └── users.py
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── validation.py
│       └── logging.py
├── docker/                   # Docker files
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/                      # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── tests/                    # Test suite
├── examples/                 # Usage examples
├── docs/                     # Documentation
├── requirements.txt
├── pyproject.toml
├── README.md
└── PLAN.md
```

## Deployment Scenarios

### 1. Local Development
```bash
# Run locally
python -m src.server

# Or with Docker
docker run -p 8000:8000 truenas-mcp
```

### 2. Remote Server
```bash
# Deploy on any server
docker run -d -p 8000:8000 \
  -e TRUENAS_HOST=your-truenas-host \
  -e TRUENAS_API_KEY=your-api-key \
  truenas-mcp
```

### 3. Cloud Deployment
```bash
# Deploy on cloud platforms
# AWS, GCP, Azure with load balancers
```

### 4. Cursor Configuration
```json
{
  "mcpServers": {
    "truenas": {
      "url": "http://your-mcp-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer your-jwt-token"
      }
    }
  }
}
```

## Success Criteria
- [ ] MCP server runs as HTTP service accessible from anywhere
- [ ] JWT authentication works for MCP clients
- [ ] Docker containerization works
- [ ] Configuration via environment variables
- [ ] Health checks and monitoring
- [ ] Comprehensive documentation
- [ ] Multiple deployment scenarios covered
- [ ] Security best practices implemented

## Next Steps
1. Convert existing MCP server to HTTP-based
2. Implement JWT authentication
3. Add Docker support
4. Create deployment guides
5. Test with Cursor integration
