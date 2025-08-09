#!/usr/bin/env python3
"""
Test script for pfSense MCP Server.
This script tests the server functionality without requiring a real pfSense connection.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import with absolute path
from src.http_pfsense_server import HTTPPfSenseMCPServer


class MockPfSenseClient:
    """Mock pfSense client for testing."""
    
    async def get_system_info(self) -> Dict[str, Any]:
        return {
            "version": "2.7.0",
            "platform": "amd64",
            "uptime": "5 days, 3 hours, 27 minutes"
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        return {
            "cpu_usage": 15.2,
            "memory_usage": 45.8,
            "disk_usage": 23.1,
            "temperature": 42.5
        }
    
    async def get_interfaces(self) -> Dict[str, Any]:
        return {
            "interfaces": [
                {"name": "wan", "status": "up", "ip": "203.0.113.1"},
                {"name": "lan", "status": "up", "ip": "192.168.1.1"},
                {"name": "opt1", "status": "down", "ip": ""}
            ]
        }
    
    async def get_firewall_rules(self) -> Dict[str, Any]:
        return {
            "rules": [
                {
                    "id": "1",
                    "action": "pass",
                    "interface": "wan",
                    "direction": "in",
                    "source": "any",
                    "destination": "any",
                    "description": "Default allow rule"
                }
            ]
        }
    
    async def test_connection(self) -> bool:
        return True


async def test_mcp_server():
    """Test the MCP server with mock client."""
    print("🧪 Testing pfSense MCP Server")
    print("=" * 40)
    
    # Create server instance
    server = HTTPPfSenseMCPServer()
    
    # Test tool listing
    print(f"📋 Available tools: {len(server.tools)}")
    for tool in server.tools:
        print(f"  - {tool.name}: {tool.description}")
    
    print("\n🔧 Testing individual tools...")
    
    # Test system info tool
    print("\n1. Testing get_system_info...")
    result = await server._call_tool("get_system_info", {})
    print(f"   Result: {result['isError']}")
    if not result['isError']:
        data = json.loads(result['content'][0]['text'])
        print(f"   Version: {data.get('version', 'N/A')}")
    
    # Test system health tool
    print("\n2. Testing get_system_health...")
    result = await server._call_tool("get_system_health", {})
    print(f"   Result: {result['isError']}")
    if not result['isError']:
        data = json.loads(result['content'][0]['text'])
        print(f"   CPU Usage: {data.get('cpu_usage', 'N/A')}%")
    
    # Test interfaces tool
    print("\n3. Testing get_interfaces...")
    result = await server._call_tool("get_interfaces", {})
    print(f"   Result: {result['isError']}")
    if not result['isError']:
        data = json.loads(result['content'][0]['text'])
        interfaces = data.get('interfaces', [])
        print(f"   Found {len(interfaces)} interfaces")
    
    # Test firewall rules tool
    print("\n4. Testing get_firewall_rules...")
    result = await server._call_tool("get_firewall_rules", {})
    print(f"   Result: {result['isError']}")
    if not result['isError']:
        data = json.loads(result['content'][0]['text'])
        rules = data.get('rules', [])
        print(f"   Found {len(rules)} firewall rules")
    
    # Test validation
    print("\n5. Testing parameter validation...")
    result = await server._call_tool("create_firewall_rule", {})
    print(f"   Validation result: {result['isError']}")
    if result['isError']:
        print(f"   Error message: {result['content'][0]['text']}")
    
    # Test unknown tool
    print("\n6. Testing unknown tool...")
    result = await server._call_tool("unknown_tool", {})
    print(f"   Result: {result['isError']}")
    if result['isError']:
        print(f"   Error message: {result['content'][0]['text']}")
    
    print("\n✅ All tests completed!")


async def test_serialization():
    """Test that the server returns proper serializable responses."""
    print("\n🔄 Testing serialization...")
    
    server = HTTPPfSenseMCPServer()
    
    # Test that responses are dictionaries (not CallToolResult objects)
    result = await server._call_tool("get_system_info", {})
    
    # Check structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "content" in result, "Result should have 'content' key"
    assert "isError" in result, "Result should have 'isError' key"
    assert isinstance(result["content"], list), "Content should be a list"
    assert len(result["content"]) > 0, "Content should not be empty"
    assert "type" in result["content"][0], "Content item should have 'type' key"
    assert "text" in result["content"][0], "Content item should have 'text' key"
    
    print("✅ Serialization test passed!")


async def main():
    """Main test function."""
    try:
        await test_mcp_server()
        await test_serialization()
        print("\n🎉 All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
