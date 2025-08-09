"""HTTP server for iDRAC MCP Server."""

import os
import asyncio
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .server import IDracMCPServer
from .auth import AuthManager
from .utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="iDRAC MCP Server",
    description="Model Context Protocol server for Dell PowerEdge iDRAC management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global instances
mcp_server: Optional[IDracMCPServer] = None
auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get authentication manager instance."""
    global auth_manager
    if auth_manager is None:
        auth_config = {
            "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
            "access_token_expire_minutes": 30
        }
        auth_manager = AuthManager(auth_config)
    return auth_manager


def get_mcp_server() -> IDracMCPServer:
    """Get MCP server instance."""
    global mcp_server
    if mcp_server is None:
        mcp_server = IDracMCPServer()
    return mcp_server


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token."""
    auth_manager = get_auth_manager()
    payload = auth_manager.verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    global mcp_server, auth_manager
    
    # Setup logging
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format_type=os.getenv("LOG_FORMAT", "console")
    )
    
    # Initialize auth manager
    auth_config = {
        "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
        "access_token_expire_minutes": 30
    }
    auth_manager = AuthManager(auth_config)
    
    # Initialize MCP server
    mcp_server = IDracMCPServer()
    
    logger.info("iDRAC MCP HTTP Server started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "iDRAC MCP Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test iDRAC connection
        mcp_server = get_mcp_server()
        result = await mcp_server.idrac_client.test_connection()
        
        return {
            "status": "healthy" if result["status"] == "success" else "unhealthy",
            "idrac_connection": result["data"]["connected"],
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


@app.post("/auth/login")
async def login(username: str, password: str):
    """Login endpoint to get JWT token."""
    auth_manager = get_auth_manager()
    
    # Check credentials
    expected_username = os.getenv("MCP_USERNAME", "admin")
    expected_password = os.getenv("MCP_PASSWORD", "admin-change-this")
    
    if username == expected_username and password == expected_password:
        token = auth_manager.create_access_token({"sub": username})
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@app.post("/auth/token")
async def create_token(admin_token: str):
    """Create JWT token using admin token."""
    auth_manager = get_auth_manager()
    expected_admin_token = os.getenv("ADMIN_TOKEN", "admin-token-change-this")
    
    if admin_token == expected_admin_token:
        token = auth_manager.create_access_token({"sub": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )


@app.post("/mcp/initialize")
async def initialize_mcp(payload: Dict[str, Any], token: Dict[str, Any] = Depends(verify_token)):
    """Initialize MCP connection."""
    mcp_server = get_mcp_server()
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "idrac-mcp",
            "version": "1.0.0"
        }
    }


@app.post("/mcp/list_tools")
async def list_tools(token: Dict[str, Any] = Depends(verify_token)):
    """List available tools."""
    mcp_server = get_mcp_server()
    tools = []
    
    for resource in mcp_server.resources.values():
        for tool in resource.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
    
    return {"tools": tools}


@app.post("/mcp/call_tool")
async def call_tool(payload: Dict[str, Any], token: Dict[str, Any] = Depends(verify_token)):
    """Call a specific tool."""
    mcp_server = get_mcp_server()
    
    tool_name = payload.get("name")
    arguments = payload.get("arguments", {})
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name is required")
    
    try:
        result = await mcp_server._call_tool(tool_name, arguments)
        return {"content": [{"type": "text", "text": str(result)}]}
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server():
    """Run the HTTP server."""
    port = int(os.getenv("SERVER_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "src.http_server:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
