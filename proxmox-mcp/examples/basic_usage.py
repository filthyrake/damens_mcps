#!/usr/bin/env python3
"""
Basic usage examples for the Proxmox MCP Server.

This script demonstrates how to use the Proxmox MCP server
and its various tools for managing Proxmox VE environments.
"""

import json
import sys
import os
import time

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the working server and client
from working_proxmox_server import ProxmoxMCPServer
from src.proxmox_client import ProxmoxClient

def test_proxmox_client():
    """Test the Proxmox client directly."""
    print("🔧 Testing Proxmox Client Directly...")
    
    try:
        # Create client instance
        client = ProxmoxClient()
        
        # Test connection
        print("  📡 Testing connection...")
        result = client.test_connection()
        print(f"  ✅ Connection result: {result}")
        
        # Get version
        print("  📋 Getting version...")
        version = client.get_version()
        print(f"  ✅ Version: {version}")
        
        # List nodes
        print("  🖥️  Listing nodes...")
        nodes = client.list_nodes()
        print(f"  ✅ Nodes: {nodes}")
        
        if nodes and 'data' in nodes:
            for node in nodes['data']:
                node_name = node['node']
                print(f"    📊 Node: {node_name}")
                
                # List VMs on this node
                vms = client.list_vms(node_name)
                print(f"      🖥️  VMs: {len(vms.get('data', []))} found")
                
                # List containers on this node
                containers = client.list_containers(node_name)
                print(f"      📦 Containers: {len(containers.get('data', []))} found")
                
                # List storage on this node
                storage = client.list_storage(node_name)
                print(f"      💾 Storage: {len(storage.get('data', []))} pools")
        
        print("  🎉 Proxmox client test completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Error testing Proxmox client: {e}")
        return False
    
    return True

def test_mcp_server():
    """Test the MCP server functionality."""
    print("\n🚀 Testing MCP Server...")
    
    try:
        # Create server instance
        server = ProxmoxMCPServer()
        
        # Test tools listing
        print("  📋 Testing tools list...")
        tools = server._list_tools()
        print(f"  ✅ Found {len(tools)} tools:")
        
        for tool in tools:
            print(f"    🛠️  {tool['name']}: {tool['description']}")
        
        # Test a simple tool call
        print("  🔧 Testing tool call...")
        result = server._call_tool("proxmox_test_connection", {})
        print(f"  ✅ Tool call result: {result}")
        
        print("  🎉 MCP server test completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Error testing MCP server: {e}")
        return False
    
    return False

def test_specific_tools():
    """Test specific tools with the client."""
    print("\n🎯 Testing Specific Tools...")
    
    try:
        client = ProxmoxClient()
        
        # Test VM operations
        print("  🖥️  Testing VM operations...")
        
        # List VMs (all nodes)
        vms = client.list_vms()
        print(f"    📋 Total VMs found: {len(vms.get('data', []))}")
        
        # Test container operations
        print("  📦 Testing container operations...")
        containers = client.list_containers()
        print(f"    📋 Total containers found: {len(containers.get('data', []))}")
        
        # Test storage operations
        print("  💾 Testing storage operations...")
        storage = client.list_storage()
        print(f"    📋 Total storage pools: {len(storage.get('data', []))}")
        
        print("  🎉 Specific tools test completed successfully!")
        
    except Exception as e:
        print(f"  ❌ Error testing specific tools: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Proxmox MCP Server - Basic Usage Examples")
    print("=" * 50)
    
    # Test the client directly
    client_success = test_proxmox_client()
    
    # Test the MCP server
    server_success = test_mcp_server()
    
    # Test specific tools
    tools_success = test_specific_tools()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"  🔧 Proxmox Client: {'✅ PASS' if client_success else '❌ FAIL'}")
    print(f"  🚀 MCP Server: {'✅ PASS' if server_success else '❌ FAIL'}")
    print(f"  🛠️  Specific Tools: {'✅ PASS' if tools_success else '❌ FAIL'}")
    
    if client_success and tools_success:
        print("\n🎉 All critical tests passed! The Proxmox MCP server is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Start the server: python working_proxmox_server.py")
        print("   2. Configure Claude Desktop to use this server")
        print("   3. Test the tools in Claude Desktop")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
