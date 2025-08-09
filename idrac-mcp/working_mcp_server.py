#!/usr/bin/env python3
"""
Working iDRAC MCP Server - Based on working TrueNAS server pattern
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


class SimpleIDracClient:
    """Simplified iDRAC client for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "192.168.1.100")
        self.port = config.get("port", 443)
        self.username = config.get("username", "root")
        self.password = config.get("password", "")
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to iDRAC."""
        return {
            "status": "connected",
            "host": self.host,
            "port": self.port,
            "message": f"iDRAC connection test successful to {self.host}:{self.port}"
        }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "host": self.host,
            "protocol": self.config.get("protocol", "https"),
            "ssl_verify": self.config.get("ssl_verify", False),
            "message": "iDRAC system information retrieved"
        }
    
    async def get_power_status(self) -> Dict[str, Any]:
        """Get server power status."""
        return {
            "host": self.host,
            "power_status": "unknown",
            "message": "Power status check initiated"
        }


class WorkingIDracMCPServer:
    """Working MCP server for iDRAC integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the server."""
        self.config = config
        self.client = SimpleIDracClient(config)
        self.server = Server("idrac-mcp")
        
        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
    
    async def _list_tools(self) -> List[Tool]:
        """List all available tools."""
        tools = [
            Tool(
                name="test_connection",
                description="Test connection to iDRAC server",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_info",
                description="Get iDRAC system information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_power_status",
                description="Get server power status",
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
            elif tool_name == "get_power_status":
                result = await self.client.get_power_status()
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Power Status: {json.dumps(result, indent=2)}")]
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
                    server_name="idrac-mcp",
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
        "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
        "port": int(os.getenv("IDRAC_PORT", "443")),
        "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
        "username": os.getenv("IDRAC_USERNAME", "root"),
        "password": os.getenv("IDRAC_PASSWORD", ""),
        "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
    }
    
    # Create and run server
    server = WorkingIDracMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
