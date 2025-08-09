#!/usr/bin/env python3
"""
Simple MCP server test to isolate Pydantic validation issues.
"""

import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp.server import Server, InitializationOptions, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    TextContent,
    ListToolsRequest,
    ListToolsResult,
    Tool
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Simple MCP server for testing."""
    
    def __init__(self):
        self.server = Server("simple-test")
        
        # Register tools
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
    
    def _list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available tools."""
        tools = [
            Tool(
                name="simple_test",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
        return ListToolsResult(tools=tools)
    
    def _call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Call a tool."""
        try:
            if request.params.name == "simple_test":
                result = {"message": "Hello from simple test tool!"}
                result_text = json.dumps(result, indent=2)
                
                # Try different approaches to create TextContent
                try:
                    # Approach 1: Direct instantiation
                    text_content = TextContent(type="text", text=result_text)
                    logger.info(f"Created TextContent: {text_content}")
                    return CallToolResult(content=[text_content])
                except Exception as e:
                    logger.error(f"Failed to create TextContent: {e}")
                    
                    # Approach 2: Dictionary
                    try:
                        return CallToolResult(content=[TextContent(type="text", text=result_text)])
                    except Exception as e2:
                        logger.error(f"Failed with dict approach: {e2}")
                        
                        # Approach 3: Raw string
                        try:
                            return CallToolResult(content=[TextContent(type="text", text=result_text)])
                        except Exception as e3:
                            logger.error(f"Failed with string approach: {e3}")
                            raise
            else:
                return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {request.params.name}")])
        except Exception as e:
            logger.error(f"Error in _call_tool: {e}")
            return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

async def main():
    """Main function."""
    server = SimpleMCPServer()
    
    logger.info("Starting simple MCP server...")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="simple-test",
                server_version="1.0.0",
                capabilities={}
            ),
            NotificationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())
