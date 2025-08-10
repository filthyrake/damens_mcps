#!/usr/bin/env python3
"""Minimal iDRAC MCP Server that avoids import issues."""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add src to path for basic imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from mcp.server.stdio import stdio_server
    from mcp.server import Server
    from mcp.server.session import InitializationOptions
except ImportError as e:
    print(f"MCP import error: {e}", file=sys.stderr)
    sys.exit(1)

class SimpleIDracMCPServer(Server):
    """Minimal iDRAC MCP server that avoids complex imports."""
    
    def __init__(self):
        """Initialize the simple iDRAC MCP server."""
        super().__init__(
            name="idrac-mcp",
            version="1.0.0"
        )
        
        # Basic iDRAC config from environment
        self.idrac_config = {
            "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
            "port": int(os.getenv("IDRAC_PORT", "443")),
            "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
            "username": os.getenv("IDRAC_USERNAME", "root"),
            "password": os.getenv("IDRAC_PASSWORD", ""),
            "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
        }
        
        print(f"Simple iDRAC MCP Server initialized for {self.idrac_config['host']}", file=sys.stderr)
    
    async def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization."""
        print("Handling initialize request", file=sys.stderr)
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "idrac-mcp",
                "version": "1.0.0"
            }
        }
    
    async def handle_list_tools(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool listing."""
        print("Handling list_tools request", file=sys.stderr)
        return {
            "tools": [
                {
                    "name": "idrac_test_connection",
                    "description": "Test connection to iDRAC server",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }
    
    async def handle_call_tool(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        print(f"Handling tool call: {tool_name}", file=sys.stderr)
        
        if tool_name == "idrac_test_connection":
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ Connection test successful to {self.idrac_config['host']}:{self.idrac_config['port']}"
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Unknown tool: {tool_name}"
                    }
                ]
            }

async def main():
    """Main entry point."""
    try:
        server = SimpleIDracMCPServer()
        print("Starting Simple iDRAC MCP Server...", file=sys.stderr)
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)
            
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
