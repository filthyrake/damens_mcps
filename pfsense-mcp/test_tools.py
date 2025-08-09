#!/usr/bin/env python3
"""
Test script to verify tools are properly defined.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from minimal_working_server import MinimalPfSenseMCPServer

async def test_tools():
    """Test that tools are properly defined."""
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    config = {
        "host": os.getenv("PFSENSE_HOST", "localhost"),
        "port": int(os.getenv("PFSENSE_PORT", "443")),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME", "admin"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true"),
    }
    
    # Create server instance
    server = MinimalPfSenseMCPServer(config)
    
    # Get tools list
    tools = await server._list_tools()
    
    print("Available tools:")
    print("=" * 50)
    
    # Check for get_firewall_rules specifically
    firewall_rules_found = False
    
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        if tool.name == "get_firewall_rules":
            firewall_rules_found = True
            print(f"  ✅ Found get_firewall_rules tool!")
    
    print(f"\nTotal tools: {len(tools)}")
    
    if firewall_rules_found:
        print("✅ get_firewall_rules tool is properly defined!")
    else:
        print("❌ get_firewall_rules tool is MISSING!")
    
    # Test the tool call
    if firewall_rules_found:
        print("\nTesting get_firewall_rules call...")
        try:
            result = await server._call_tool("get_firewall_rules", {})
            print("✅ Tool call successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Tool call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tools())
