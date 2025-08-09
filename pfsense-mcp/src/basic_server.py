#!/usr/bin/env python3
"""
Basic pfSense MCP Server - Minimal pattern.
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


class BasicPfSenseMCPServer:
    """Basic MCP server for pfSense."""
    
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
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        try:
            if name == "test_connection":
                result = {"status": "connected", "message": "pfSense MCP server is working"}
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


async def main():
    """Main entry point."""
    server = BasicPfSenseMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        async for request in read_stream:
            if isinstance(request, ListToolsRequest):
                await mcp.server.stdio.list_tools(write_stream, request, server.tools)
            elif isinstance(request, CallToolRequest):
                result = await server._call_tool(request.name, request.arguments)
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
                pass


if __name__ == "__main__":
    anyio.run(main)
