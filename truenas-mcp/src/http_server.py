"""HTTP server for TrueNAS MCP Server."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .server import TrueNASMCPServer
from .auth import JWTAuthManager
from .config import load_settings, Settings
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenRequest(BaseModel):
    """Token creation request model."""
    admin_token: str
    username: Optional[str] = "admin"


class ToolCallRequest(BaseModel):
    """MCP tool call request model."""
    name: str
    arguments: Optional[Dict[str, Any]] = None


class ToolCallResponse(BaseModel):
    """MCP tool call response model."""
    content: list
    isError: bool = False


# Global variables
truenas_server: Optional[TrueNASMCPServer] = None
jwt_auth_manager: Optional[JWTAuthManager] = None
app_settings: Optional[Settings] = None


def get_jwt_auth_manager() -> JWTAuthManager:
    """Get the JWT authentication manager."""
    if jwt_auth_manager is None:
        raise HTTPException(status_code=500, detail="Authentication manager not initialized")
    return jwt_auth_manager


def get_truenas_server() -> TrueNASMCPServer:
    """Get the TrueNAS MCP server."""
    if truenas_server is None:
        raise HTTPException(status_code=500, detail="TrueNAS server not initialized")
    return truenas_server


def get_settings() -> Settings:
    """Get application settings."""
    if app_settings is None:
        raise HTTPException(status_code=500, detail="Settings not initialized")
    return app_settings


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    auth_mgr = get_jwt_auth_manager()
    token_data = auth_mgr.verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": token_data.username}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    global truenas_server, jwt_auth_manager, app_settings
    
    # Load settings
    try:
        app_settings = load_settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifespan (startup and shutdown)."""
        global truenas_server, jwt_auth_manager
        
        # Startup
        # Setup logging
        setup_logging(
            level=app_settings.log_level,
            log_format=app_settings.log_format,
            log_file=app_settings.log_file
        )
        
        # Configuration for TrueNAS
        config = {
            "host": app_settings.truenas_host,
            "port": app_settings.truenas_port,
            "api_key": app_settings.truenas_api_key,
            "username": app_settings.truenas_username,
            "password": app_settings.truenas_password,
            "verify_ssl": app_settings.truenas_verify_ssl,
            "secret_key": app_settings.secret_key,
        }
        
        try:
            # Initialize JWT authentication manager
            jwt_auth_manager = JWTAuthManager(
                secret_key=app_settings.secret_key,
                algorithm=app_settings.jwt_algorithm,
                access_token_expire_minutes=app_settings.access_token_expire_minutes
            )
            
            # Initialize TrueNAS MCP server
            truenas_server = TrueNASMCPServer(config)
            
            logger.info("TrueNAS MCP HTTP server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
        
        yield
        
        # Shutdown
        logger.info("TrueNAS MCP HTTP server shutting down")
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="TrueNAS MCP Server",
        description="HTTP-based Model Context Protocol server for TrueNAS Scale management",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=app_settings.cors_allow_credentials,
        allow_methods=app_settings.cors_allow_methods,
        allow_headers=app_settings.cors_allow_headers,
    )
    
    @app.get("/")
    async def root():
        """Root endpoint with server information."""
        return {
            "name": "TrueNAS MCP Server",
            "version": "0.1.0",
            "description": "HTTP-based Model Context Protocol server for TrueNAS Scale management",
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        if truenas_server is None:
            return {
                "status": "error",
                "message": "Server not initialized",
                "truenas_connection": "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Basic health check - connection is configured
        return {
            "status": "healthy",
            "truenas_connection": "configured",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.post("/auth/login")
    async def login(request: LoginRequest):
        """Login endpoint to get JWT token."""
        auth_mgr = get_jwt_auth_manager()
        
        # Authenticate user
        user = auth_mgr.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=app_settings.access_token_expire_minutes)
        access_token = auth_mgr.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    
    @app.post("/auth/token")
    async def create_token(request: TokenRequest):
        """Create a JWT token using admin token."""
        settings = get_settings()
        
        # Verify admin token
        if not settings.admin_token or request.admin_token != settings.admin_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token",
            )
        
        auth_mgr = get_jwt_auth_manager()
        
        # Create access token for the specified username
        access_token_expires = timedelta(minutes=app_settings.access_token_expire_minutes)
        access_token = auth_mgr.create_access_token(
            data={"sub": request.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": request.username
        }
    
    @app.post("/mcp/tools/list")
    async def list_tools(token_data: Dict[str, Any] = Depends(verify_token)):
        """List available MCP tools."""
        try:
            server = get_truenas_server()
            
            # Get tools from server
            from mcp.types import ListToolsRequest
            request = ListToolsRequest()
            result = await server._list_tools(request)
            
            # Convert tools to dict format
            tools = []
            for tool in result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            
            return {"tools": tools}
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing tools: {str(e)}"
            )
    
    @app.post("/mcp/tools/call")
    async def call_tool(
        request: ToolCallRequest,
        token_data: Dict[str, Any] = Depends(verify_token)
    ):
        """Call an MCP tool."""
        try:
            server = get_truenas_server()
            
            # Create MCP tool call request
            from mcp.types import CallToolRequest as MCPCallToolRequest
            mcp_request = MCPCallToolRequest(
                name=request.name,
                arguments=request.arguments or {}
            )
            
            # Call the tool
            result = await server._call_tool(mcp_request)
            
            # Convert result to dict format
            content = []
            for item in result.content:
                if hasattr(item, 'type') and hasattr(item, 'text'):
                    content.append({
                        "type": item.type,
                        "text": item.text
                    })
            
            return {
                "content": content,
                "isError": getattr(result, 'isError', False)
            }
        except Exception as e:
            logger.error(f"Error calling tool {request.name}: {e}")
            # Return a generic error message to avoid exposing stack traces
            return {
                "content": [{"type": "text", "text": f"Tool '{request.name}' execution failed. Check server logs for details."}],
                "isError": True
            }
    
    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
):
    """Run the HTTP server programmatically.
    
    Note: The canonical way to start the server is via the CLI:
        python -m src.http_cli serve
    
    This function is provided for:
    - Programmatic server startup in custom deployments
    - Development/testing when direct execution is needed
    - Integration with other Python applications
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        log_level: Logging level
    """
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    # For development/testing only
    # Production usage: python -m src.http_cli serve
    run_server()
