"""HTTP server for Proxmox MCP Server."""

import asyncio
import json
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .server import ProxmoxMCPServer
from .auth import AuthManager
from .utils.mcp_logging import get_logger, setup_logging

logger = get_logger(__name__)

# Security
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    admin_token: str

class ToolCallRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = None

class ToolCallResponse(BaseModel):
    content: str
    error: Optional[str] = None

# FastAPI app
app = FastAPI(
    title="Proxmox MCP Server",
    description="HTTP-based Model Context Protocol server for Proxmox VE management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
proxmox_server: Optional[ProxmoxMCPServer] = None
auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the authentication manager."""
    if auth_manager is None:
        raise HTTPException(status_code=500, detail="Authentication manager not initialized")
    return auth_manager


def get_proxmox_server() -> ProxmoxMCPServer:
    """Get the Proxmox MCP server."""
    if proxmox_server is None:
        raise HTTPException(status_code=500, detail="Proxmox server not initialized")
    return proxmox_server


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    auth_mgr = get_auth_manager()
    payload = auth_mgr.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup."""
    global proxmox_server, auth_manager
    
    # Setup logging
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format_type=os.getenv("LOG_FORMAT", "json")
    )
    
    # Configuration
    config = {
        "host": os.getenv("PROXMOX_HOST"),
        "port": int(os.getenv("PROXMOX_PORT", "8006")),
        "protocol": os.getenv("PROXMOX_PROTOCOL", "https"),
        "username": os.getenv("PROXMOX_USERNAME"),
        "password": os.getenv("PROXMOX_PASSWORD"),
        "api_token": os.getenv("PROXMOX_API_TOKEN"),
        "realm": os.getenv("PROXMOX_REALM", "pve"),
        "verify_ssl": os.getenv("PROXMOX_SSL_VERIFY", "true").lower() == "true",
        "secret_key": os.getenv("SECRET_KEY"),
    }
    
    # Validate required configuration
    if not config["host"]:
        logger.error("PROXMOX_HOST environment variable is required")
        return
    
    if not config["api_token"] and (not config["username"] or not config["password"]):
        logger.error("Either PROXMOX_API_TOKEN or PROXMOX_USERNAME/PROXMOX_PASSWORD is required")
        return
    
    if not config["secret_key"]:
        logger.error("SECRET_KEY environment variable is required")
        return
    
    try:
        # Initialize components
        auth_manager = AuthManager(config)
        proxmox_server = ProxmoxMCPServer(config)
        
        logger.info("Proxmox MCP HTTP server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Proxmox MCP Server",
        "version": "1.0.0",
        "description": "HTTP-based Model Context Protocol server for Proxmox VE management",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if proxmox_server is None:
            return {"status": "error", "message": "Server not initialized"}
        
        # Test Proxmox connection
        connection_test = await proxmox_server.proxmox_client.test_connection()
        
        return {
            "status": "healthy" if connection_test["status"] == "success" else "unhealthy",
            "proxmox_connection": connection_test,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/auth/login")
async def login(request: LoginRequest):
    """Login endpoint to get JWT token."""
    auth_mgr = get_auth_manager()
    
    # For now, we'll use a simple authentication
    # In production, you might want to validate against Proxmox or a user database
    expected_credentials = {
        "username": os.getenv("MCP_USERNAME", "admin"),
        "password_hash": auth_mgr.get_password_hash(os.getenv("MCP_PASSWORD", "admin"))
    }
    
    if auth_mgr.authenticate_user(request.username, request.password, expected_credentials):
        token_data = {
            "sub": request.username,
            "type": "user",
            "permissions": ["read", "write"]
        }
        token = auth_mgr.create_access_token(token_data)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/auth/token")
async def create_token(request: TokenRequest):
    """Create a token using admin token."""
    auth_mgr = get_auth_manager()
    
    # Validate admin token (you might want to implement proper admin token validation)
    if request.admin_token != os.getenv("ADMIN_TOKEN", "admin-token-change-this"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )
    
    token_data = {
        "sub": "admin",
        "type": "admin",
        "permissions": ["read", "write", "admin"]
    }
    token = auth_mgr.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/mcp/initialize")
async def mcp_initialize(payload: Dict[str, Any] = Depends(verify_token)):
    """MCP initialization endpoint."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "proxmox-mcp",
            "version": "1.0.0"
        }
    }


@app.post("/mcp/tools/list")
async def mcp_list_tools(payload: Dict[str, Any] = Depends(verify_token)):
    """List available MCP tools."""
    server = get_proxmox_server()
    
    # Get tools from the server
    tools = []
    for tool_name, tool_info in server.server._tools.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "inputSchema": tool_info["inputSchema"]
        })
    
    return {"tools": tools}


@app.post("/mcp/tools/call")
async def mcp_call_tool(
    request: ToolCallRequest,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """Call an MCP tool."""
    server = get_proxmox_server()
    
    try:
        # Create a mock MCP request
        from mcp.types import CallToolRequest
        mcp_request = CallToolRequest(
            name=request.name,
            arguments=request.arguments or {}
        )
        
        # Call the tool
        result = await server._call_tool(mcp_request)
        
        # Extract content from result
        content = ""
        if result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    content += item.text
        
        return ToolCallResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error calling tool {request.name}: {e}")
        return ToolCallResponse(
            content="",
            error=str(e)
        )


@app.get("/tools")
async def list_tools(payload: Dict[str, Any] = Depends(verify_token)):
    """List available tools (alternative endpoint)."""
    server = get_proxmox_server()
    
    tools = []
    for tool_name, tool_info in server.server._tools.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "inputSchema": tool_info["inputSchema"]
        })
    
    return {"tools": tools}


@app.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """Call a specific tool (alternative endpoint)."""
    server = get_proxmox_server()
    
    try:
        # Create a mock MCP request
        from mcp.types import CallToolRequest
        mcp_request = CallToolRequest(
            name=tool_name,
            arguments=arguments or {}
        )
        
        # Call the tool
        result = await server._call_tool(mcp_request)
        
        # Extract content from result
        content = ""
        if result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    content += item.text
        
        return {"content": content, "error": None}
        
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return {"content": "", "error": str(e)}


def run_server():
    """Run the HTTP server."""
    port = int(os.getenv("SERVER_PORT", "8000"))
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Proxmox MCP HTTP server on {host}:{port}")
    
    uvicorn.run(
        "src.http_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
