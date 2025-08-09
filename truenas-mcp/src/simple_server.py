#!/usr/bin/env python3
"""
Simplified TrueNAS MCP Server based on working implementation
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


class SimpleTrueNASClient:
    """Simplified TrueNAS client for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 443)
        self.api_key = config.get("api_key")
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to TrueNAS."""
        return {
            "status": "connected",
            "host": self.host,
            "port": self.port,
            "message": "Connection test successful (mock)"
        }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "hostname": self.host,
            "version": "TrueNAS-SCALE-24.10.0",
            "platform": "Linux",
            "uptime": "2 days, 3 hours"
        }


class SimpleTrueNASMCPServer:
    """Simplified MCP server for TrueNAS integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the server."""
        self.config = config
        self.client = SimpleTrueNASClient(config)
        self.server = Server("truenas-mcp")
        
        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
    
    async def _list_tools(self) -> List[Tool]:
        """List all available tools."""
        tools = [
            Tool(
                name="test_connection",
                description="Test connection to TrueNAS server",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_info",
                description="Get basic system information from TrueNAS",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_version",
                description="Get TrueNAS version information",
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
                    content=[TextContent(type="text", text=f"TrueNAS Version: {result.get('version', 'Unknown')}")]
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
                    server_name="truenas-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Main entry point."""
    # Load configuration from environment
    config = {
        "host": os.getenv("TRUENAS_HOST", "localhost"),
        "port": int(os.getenv("TRUENAS_PORT", "443")),
        "api_key": os.getenv("TRUENAS_API_KEY"),
        "username": os.getenv("TRUENAS_USERNAME"),
        "password": os.getenv("TRUENAS_PASSWORD"),
        "verify_ssl": os.getenv("TRUENAS_VERIFY_SSL", "true").lower() == "true",
    }
    
    # Create and run server
    server = SimpleTrueNASMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
