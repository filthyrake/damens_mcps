#!/usr/bin/env python3
"""Simple entry point for iDRAC MCP Server that can be run directly."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the server
from server import IDracMCPServer
from mcp.server.stdio import stdio_server
import asyncio

async def main():
    """Main entry point."""
    server = IDracMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
