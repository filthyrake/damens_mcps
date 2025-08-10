"""
HTTP server interface for the Warewulf MCP Server.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .server import WarewulfMCPServer
from .utils.logging import setup_logging


# Request/Response Models
class ToolCallRequest(BaseModel):
    """Request model for calling a tool."""
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    success: bool = Field(..., description="Whether the tool call was successful")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool result")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Server status")
    version: str = Field(..., description="MCP server version")
    warewulf_status: str = Field(..., description="Warewulf connection status")


class WarewulfHTTPServer:
    """HTTP server for the Warewulf MCP Server."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize HTTP server."""
        self.config = config or {}
        self.mcp_server = WarewulfMCPServer(config)
        self.logger = setup_logging()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Warewulf MCP Server",
            description="HTTP interface for Warewulf MCP Server",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint."""
            return {
                "message": "Warewulf MCP Server",
                "version": "0.1.0",
                "status": "running",
                "docs": "/docs"
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            try:
                # Test Warewulf connection
                warewulf_status = "unknown"
                if hasattr(self.mcp_server, 'client') and self.mcp_server.client:
                    try:
                        result = self.mcp_server.client.test_connection()
                        warewulf_status = "connected" if result.get('success') else "disconnected"
                    except Exception:
                        warewulf_status = "error"
                
                return HealthResponse(
                    status="healthy",
                    version="0.1.0",
                    warewulf_status=warewulf_status
                )
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools."""
            try:
                tools = self.mcp_server.get_tools()
                return {
                    "success": True,
                    "tools": [tool.dict() for tool in tools],
                    "count": len(tools)
                }
            except Exception as e:
                self.logger.error(f"Failed to list tools: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/call", response_model=ToolCallResponse)
        async def call_tool(request: ToolCallRequest):
            """Call a specific tool."""
            try:
                self.logger.info(f"Calling tool: {request.name} with args: {request.arguments}")
                
                result = await self.mcp_server.call_tool(request.name, request.arguments)
                
                return ToolCallResponse(
                    success=True,
                    result=result.content[0].text if result.content else None
                )
                
            except Exception as e:
                self.logger.error(f"Tool call failed: {e}")
                return ToolCallResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.get("/warewulf/status")
        async def warewulf_status():
            """Get Warewulf server status."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.test_connection()
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to get Warewulf status: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/warewulf/version")
        async def warewulf_version():
            """Get Warewulf server version."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.get_version()
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to get Warewulf version: {e}")
                return {"success": False, "error": str(e)}
        
        # Node management endpoints
        @self.app.get("/warewulf/nodes")
        async def list_nodes():
            """List all nodes."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.list_nodes()
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to list nodes: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/warewulf/nodes/{node_id}")
        async def get_node(node_id: str):
            """Get a specific node."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.get_node(node_id)
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to get node {node_id}: {e}")
                return {"success": False, "error": str(e)}
        
        # Profile management endpoints
        @self.app.get("/warewulf/profiles")
        async def list_profiles():
            """List all profiles."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.list_profiles()
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to list profiles: {e}")
                return {"success": False, "error": str(e)}
        
        # Image management endpoints
        @self.app.get("/warewulf/images")
        async def list_images():
            """List all images."""
            try:
                if not hasattr(self.mcp_server, 'client') or not self.mcp_server.client:
                    return {"success": False, "error": "Client not initialized"}
                
                result = self.mcp_server.client.list_images()
                return {"success": True, "result": result}
                
            except Exception as e:
                self.logger.error(f"Failed to list images: {e}")
                return {"success": False, "error": str(e)}
        
        # Error handlers
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Global exception handler."""
            self.logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Internal server error"}
            )
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTP server."""
        self.logger.info(f"Starting HTTP server on {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


async def main():
    """Main entry point for HTTP server."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    # Create and run server
    server = WarewulfHTTPServer()
    server.run(host=host, port=port)


if __name__ == "__main__":
    asyncio.run(main())
