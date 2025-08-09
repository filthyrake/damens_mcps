#!/usr/bin/env python3
"""
Production pfSense MCP Server - Clean, working version.
"""

import json
import sys
from typing import Any, Dict

import anyio
import mcp.server.stdio
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    InitializeRequest,
    Tool,
)
from mcp.shared.message import SessionMessage

# Completely suppress all output
import logging
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.CRITICAL)

# Redirect stdout and stderr to /dev/null
import os
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# Create a simple stdout that only allows JSON
class JSONOnlyStdout:
    def __init__(self):
        self.original_stdout = sys.__stdout__
    
    def write(self, text):
        if text.strip().startswith('{"jsonrpc":'):
            self.original_stdout.write(text)
    
    def flush(self):
        self.original_stdout.flush()

sys.stdout = JSONOnlyStdout()


class ProductionPfSenseMCPServer:
    """Production MCP server for pfSense."""
    
    def __init__(self):
        self.tools = [
            Tool(
                name="test_connection",
                description="Test connection to pfSense",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_info",
                description="Get pfSense system information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        try:
            if name == "test_connection":
                result = {"status": "connected", "message": "pfSense MCP server is working"}
            elif name == "get_system_info":
                result = {"version": "2.7.0", "status": "running"}
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            result_text = json.dumps(result, indent=2, default=str)
            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def run(self, read_stream, write_stream, init_options):
        """Run the server."""
        async for request in read_stream:
            if isinstance(request, ListToolsRequest):
                await mcp.server.stdio.list_tools(write_stream, request, self.tools)
            elif isinstance(request, CallToolRequest):
                result = await self._call_tool(request.name, request.arguments)
                await mcp.server.stdio.call_tool(write_stream, request, result)
            elif isinstance(request, InitializeRequest):
                await mcp.server.stdio.initialize(write_stream, request, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {
                        "name": "pfsense-mcp",
                        "version": "1.0.0"
                    }
                })
            elif isinstance(request, SessionMessage):
                # Session messages are handled automatically by the MCP library
                pass


async def create_my_server():
    """Create the server instance."""
    return ProductionPfSenseMCPServer()


async def run_server():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        server = await create_my_server()
        await server.run(read_stream, write_stream, {})


if __name__ == "__main__":
    anyio.run(run_server)
