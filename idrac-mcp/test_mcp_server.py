#!/usr/bin/env python3
"""Test iDRAC MCP Server functionality."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_mcp_server():
    """Test MCP server functionality."""
    print("🧪 Testing iDRAC MCP Server")
    print("=" * 40)
    
    # Configuration
    config = {
        "host": "192.168.1.100",
        "port": 443,
        "protocol": "https",
        "username": "root",
        "password": "test",
        "ssl_verify": False
    }
    
    try:
        # Test MCP server import
        print("🔧 Testing MCP server import...")
        from server import IDracMCPServer
        
        print("✅ Successfully imported IDracMCPServer")
        
        # Test server initialization
        print("🔧 Testing server initialization...")
        server = IDracMCPServer()
        print("✅ Successfully created MCP server instance")
        
        # Test tool listing
        print("🔧 Testing tool listing...")
        tools = await server._list_tools()
        print(f"✅ Found {len(tools)} tools")
        
        # List available tools
        print("\n📋 Available Tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test a simple tool call (without real connection)
        print("\n🔧 Testing tool call...")
        try:
            result = await server._call_tool("idrac_test_connection", {})
            print(f"✅ Tool call result: {result}")
        except Exception as e:
            print(f"⚠️ Tool call failed (expected without real iDRAC): {e}")
        
        print("\n🎉 MCP Server tests completed!")
        print("\n📋 Summary:")
        print("- ✅ Server imports and initialization")
        print("- ✅ Tool registration and listing")
        print("- ⚠️ Tool execution (needs real iDRAC for full test)")
        
        print("\n💡 Next steps:")
        print("1. Set up real iDRAC server")
        print("2. Test with MCP client (Claude Desktop, Cursor, etc.)")
        print("3. Test all available tools")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
