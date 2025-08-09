#!/usr/bin/env python3
"""
Working pfSense MCP Server - Based on TrueNAS pattern.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import the real pfSense client
try:
    from .pfsense_client import HTTPPfSenseClient
    from .auth import PfSenseAuth
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from pfsense_client import HTTPPfSenseClient
    from auth import PfSenseAuth

class RealPfSenseClient:
    """Real pfSense client using the HTTP API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 443)
        self.protocol = config.get("protocol", "https")
        self.api_key = config.get("api_key")
        self.username = config.get("username")
        self.password = config.get("password")
        self.verify_ssl = config.get("verify_ssl", True)
        
        # Initialize the real pfSense client
        self.client = HTTPPfSenseClient(config)
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to pfSense."""
        try:
            result = await self.client.test_connection()
            return {
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "message": "pfSense MCP server is working",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "host": self.host,
                "port": self.port,
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            result = await self.client.get_system_info()
            return result
        except Exception as e:
            return {
                "error": f"Failed to get system info: {str(e)}"
            }


class WorkingPfSenseMCPServer:
    """Working MCP server for pfSense integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the server."""
        self.config = config
        self.client = RealPfSenseClient(config)
        self.server = Server("pfsense-mcp")
        
        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
    
    async def _list_tools(self) -> List[Tool]:
        """List all available tools."""
        tools = [
            Tool(
                name="test_connection",
                description="Test connection to pfSense server",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_info",
                description="Get basic system information from pfSense",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_version",
                description="Get pfSense version information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
        
        return tools
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""
        tool_name = name
        
        try:
            if tool_name == "test_connection":
                result = await self.client.test_connection()
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Connection test: {json.dumps(result, indent=2)}")]
                )
            elif tool_name == "get_system_info":
                result = await self.client.get_system_info()
                return CallToolResult(
                    content=[TextContent(type="text", text=f"System Info: {json.dumps(result, indent=2)}")]
                )
            elif tool_name == "get_version":
                result = await self.client.get_system_info()
                return CallToolResult(
                    content=[TextContent(type="text", text=f"pfSense Version: {result.get('version', 'Unknown')}")]
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pfsense-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Load configuration from environment
    config = {
        "host": os.getenv("PFSENSE_HOST", "localhost"),
        "port": int(os.getenv("PFSENSE_PORT", "443")),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "verify_ssl": os.getenv("PFSENSE_SSL_VERIFY", "true").lower() == "true",
    }
    
    # Create and run server
    server = WorkingPfSenseMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
