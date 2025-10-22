"""Main MCP server implementation for TrueNAS Scale integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .truenas_client import TrueNASClient
from .auth import AuthManager
from .resources import (
    SystemResource,
    StorageResource,
    NetworkResource,
    ServicesResource,
    UsersResource,
)

logger = logging.getLogger(__name__)


class TrueNASMCPServer:
    """Main MCP server for TrueNAS Scale integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the TrueNAS MCP server.
        
        Args:
            config: Configuration dictionary containing TrueNAS connection details
        """
        self.config = config
        self.auth_manager = AuthManager(config)
        self.truenas_client = TrueNASClient(config, self.auth_manager)
        
        # Initialize resource handlers
        self.system_resource = SystemResource(self.truenas_client)
        self.storage_resource = StorageResource(self.truenas_client)
        self.network_resource = NetworkResource(self.truenas_client)
        self.services_resource = ServicesResource(self.truenas_client)
        self.users_resource = UsersResource(self.truenas_client)
        
        # Create MCP server
        self.server = Server("truenas-mcp")
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register all available tools with the MCP server."""
        
        # System tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
        
        # Register resource-specific tools
        self.system_resource.register_tools(self.server)
        self.storage_resource.register_tools(self.server)
        self.network_resource.register_tools(self.server)
        self.services_resource.register_tools(self.server)
        self.users_resource.register_tools(self.server)
    
    async def _list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List all available tools."""
        tools = []
        
        # Add system tools
        tools.extend([
            Tool(
                name="truenas_get_system_info",
                description="Get basic system information from TrueNAS",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_get_version",
                description="Get TrueNAS version information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_get_health",
                description="Get system health status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ])
        
        # Add resource-specific tools
        tools.extend(self.system_resource.get_tools())
        tools.extend(self.storage_resource.get_tools())
        tools.extend(self.network_resource.get_tools())
        tools.extend(self.services_resource.get_tools())
        tools.extend(self.users_resource.get_tools())
        
        return ListToolsResult(tools=tools)
    
    async def _call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls and route to appropriate resource handler."""
        tool_name = request.name
        
        try:
            # Route to appropriate resource handler
            if tool_name.startswith("truenas_system_"):
                return await self.system_resource.handle_tool(request)
            elif tool_name.startswith("truenas_storage_"):
                return await self.storage_resource.handle_tool(request)
            elif tool_name.startswith("truenas_network_"):
                return await self.network_resource.handle_tool(request)
            elif tool_name.startswith("truenas_services_"):
                return await self.services_resource.handle_tool(request)
            elif tool_name.startswith("truenas_users_"):
                return await self.users_resource.handle_tool(request)
            elif tool_name == "truenas_get_system_info":
                return await self._get_system_info()
            elif tool_name == "truenas_get_version":
                return await self._get_version()
            elif tool_name == "truenas_get_health":
                return await self._get_health()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _get_system_info(self) -> CallToolResult:
        """Get basic system information."""
        try:
            info = await self.truenas_client.get_system_info()
            return CallToolResult(
                content=[TextContent(type="text", text=f"System Info: {info}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting system info: {e}")],
                isError=True
            )
    
    async def _get_version(self) -> CallToolResult:
        """Get TrueNAS version information."""
        try:
            version = await self.truenas_client.get_version()
            return CallToolResult(
                content=[TextContent(type="text", text=f"TrueNAS Version: {version}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting version: {e}")],
                isError=True
            )
    
    async def _get_health(self) -> CallToolResult:
        """Get system health status."""
        try:
            health = await self.truenas_client.get_health()
            return CallToolResult(
                content=[TextContent(type="text", text=f"System Health: {health}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting health: {e}")],
                isError=True
            )
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="truenas-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def main() -> None:
    """Main entry point for the TrueNAS MCP server."""
    import os
    from dotenv import load_dotenv
    
    # Load configuration from environment
    load_dotenv()
    
    config = {
        "host": os.getenv("TRUENAS_HOST", "localhost"),
        "port": int(os.getenv("TRUENAS_PORT", "443")),
        "api_key": os.getenv("TRUENAS_API_KEY"),
        "username": os.getenv("TRUENAS_USERNAME"),
        "password": os.getenv("TRUENAS_PASSWORD"),
        "verify_ssl": os.getenv("TRUENAS_VERIFY_SSL", "true").lower() == "true",
    }
    
    # Validate required configuration
    if not config["api_key"] and not (config["username"] and config["password"]):
        raise ValueError("Either TRUENAS_API_KEY or TRUENAS_USERNAME/TRUENAS_PASSWORD must be set")
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run server
    server = TrueNASMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
