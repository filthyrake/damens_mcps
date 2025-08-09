#!/usr/bin/env python3
"""
Working pfSense MCP Server - Based on MCP library patterns.
"""

import asyncio
import json
import sys
from typing import Any, Dict

import mcp.server.stdio
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    InitializeRequest,
    Tool,
)
from mcp.shared.message import SessionMessage

# Print debug info to stderr
def debug_print(msg):
    print(f"DEBUG: {msg}", file=sys.stderr)

debug_print("Server starting...")

class WorkingPfSenseMCPServer:
    """Working MCP server for pfSense."""
    
    def __init__(self):
        debug_print("Initializing server...")
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
        debug_print(f"Created {len(self.tools)} tools")
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        debug_print(f"Calling tool: {name}")
        try:
            if name == "test_connection":
                result = {"status": "connected", "message": "pfSense MCP server is working"}
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            result_text = json.dumps(result, indent=2, default=str)
            debug_print(f"Tool result: {result_text}")
            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
        except Exception as e:
            debug_print(f"Tool error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }


async def main():
    """Main entry point."""
    try:
        debug_print("Creating server...")
        server = WorkingPfSenseMCPServer()
        
        debug_print("Creating stdio server...")
        async with stdio_server() as (read_stream, write_stream):
            debug_print("Server ready, waiting for requests...")
            
            async for request in read_stream:
                debug_print(f"Received request: {type(request).__name__}")
                
                if isinstance(request, ListToolsRequest):
                    debug_print("Handling ListToolsRequest")
                    await mcp.server.stdio.list_tools(write_stream, request, server.tools)
                    debug_print("ListToolsRequest handled")
                    
                elif isinstance(request, CallToolRequest):
                    debug_print(f"Handling CallToolRequest: {request.name}")
                    result = await server._call_tool(request.name, request.arguments)
                    await mcp.server.stdio.call_tool(write_stream, request, result)
                    debug_print("CallToolRequest handled")
                    
                elif isinstance(request, InitializeRequest):
                    debug_print("Handling InitializeRequest")
                    await mcp.server.stdio.initialize(write_stream, request, {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {
                            "name": "pfsense-mcp",
                            "version": "1.0.0"
                        }
                    })
                    debug_print("InitializeRequest handled")
                    
                elif isinstance(request, SessionMessage):
                    debug_print("Handling SessionMessage")
                    # Session messages are handled automatically by the MCP library
                    pass
                else:
                    debug_print(f"Unknown request type: {type(request)}")
                    
    except Exception as e:
        debug_print(f"Main error: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    debug_print("Starting main...")
    asyncio.run(main())
