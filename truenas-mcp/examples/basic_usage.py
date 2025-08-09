#!/usr/bin/env python3
"""
Basic usage example for TrueNAS MCP Server.

This example demonstrates how to use the TrueNAS MCP server
to interact with a TrueNAS Scale server.
"""

import asyncio
import json
from pathlib import Path

from src.server import TrueNASMCPServer
from src.truenas_client import TrueNASClient
from src.auth import AuthManager


async def basic_example():
    """Basic example of using the TrueNAS MCP server."""
    
    # Configuration
    config = {
        "host": "your-truenas-host",
        "port": 443,
        "api_key": "your-api-key",
        "verify_ssl": True
    }
    
    print("🔧 TrueNAS MCP Server - Basic Usage Example")
    print("=" * 50)
    
    try:
        # Create authentication manager and client
        auth_manager = AuthManager(config)
        client = TrueNASClient(config, auth_manager)
        
        # Test connection
        print("📡 Testing connection to TrueNAS...")
        if await client.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
        
        # Get system information
        print("\n📊 Getting system information...")
        system_info = await client.get_system_info()
        print(f"Hostname: {system_info.get('hostname', 'N/A')}")
        print(f"Platform: {system_info.get('platform', 'N/A')}")
        print(f"Uptime: {system_info.get('uptime', 'N/A')}")
        
        # Get version information
        print("\n📋 Getting version information...")
        version_info = await client.get_version()
        print(f"Version: {version_info.get('version', 'N/A')}")
        print(f"Build Time: {version_info.get('buildtime', 'N/A')}")
        
        # Get storage pools
        print("\n💾 Getting storage pools...")
        pools = await client.get_pools()
        print(f"Found {len(pools)} storage pool(s):")
        for pool in pools:
            print(f"  - {pool.get('name', 'N/A')} ({pool.get('status', 'N/A')})")
        
        # Get services
        print("\n🔌 Getting services...")
        services = await client.get_services()
        print(f"Found {len(services)} service(s):")
        for service in services:
            print(f"  - {service.get('service', 'N/A')} ({service.get('state', 'N/A')})")
        
        # Get users
        print("\n👥 Getting users...")
        users = await client.get_users()
        print(f"Found {len(users)} user(s):")
        for user in users:
            print(f"  - {user.get('username', 'N/A')} ({user.get('full_name', 'N/A')})")
        
        print("\n✅ Basic example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def mcp_server_example():
    """Example of using the MCP server directly."""
    
    print("\n🤖 MCP Server Example")
    print("=" * 30)
    
    # Configuration
    config = {
        "host": "your-truenas-host",
        "port": 443,
        "api_key": "your-api-key",
        "verify_ssl": True
    }
    
    try:
        # Create MCP server
        server = TrueNASMCPServer(config)
        
        # Get available tools
        tools = []
        tools.extend(server.system_resource.get_tools())
        tools.extend(server.storage_resource.get_tools())
        tools.extend(server.network_resource.get_tools())
        tools.extend(server.services_resource.get_tools())
        tools.extend(server.users_resource.get_tools())
        
        print(f"Available tools: {len(tools)}")
        
        # Example: Call a system tool
        from mcp.types import CallToolRequest
        
        # Get system info
        request = CallToolRequest(
            name="truenas_system_get_info",
            arguments={}
        )
        
        result = await server.system_resource.handle_tool(request)
        print(f"System info result: {result.content[0].text[:100]}...")
        
        print("✅ MCP server example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def configuration_example():
    """Example of different configuration methods."""
    
    print("\n⚙️ Configuration Examples")
    print("=" * 30)
    
    # Method 1: Direct configuration
    config1 = {
        "host": "truenas.example.com",
        "port": 443,
        "api_key": "your-api-key",
        "verify_ssl": True
    }
    print("1. Direct configuration:")
    print(json.dumps(config1, indent=2))
    
    # Method 2: Username/password authentication
    config2 = {
        "host": "truenas.example.com",
        "port": 443,
        "username": "admin",
        "password": "your-password",
        "verify_ssl": True
    }
    print("\n2. Username/password configuration:")
    print(json.dumps({**config2, "password": "***"}, indent=2))
    
    # Method 3: Configuration file
    config_file = Path.home() / '.truenas-mcp' / 'config.json'
    print(f"\n3. Configuration file: {config_file}")
    
    # Method 4: Environment variables
    print("\n4. Environment variables:")
    print("export TRUENAS_HOST='truenas.example.com'")
    print("export TRUENAS_PORT='443'")
    print("export TRUENAS_API_KEY='your-api-key'")
    print("export TRUENAS_VERIFY_SSL='true'")


async def main():
    """Main function to run all examples."""
    print("🚀 TrueNAS MCP Server Examples")
    print("=" * 40)
    
    # Show configuration examples
    configuration_example()
    
    # Run basic example (commented out to avoid actual API calls)
    # await basic_example()
    
    # Run MCP server example (commented out to avoid actual API calls)
    # await mcp_server_example()
    
    print("\n📝 Note: Examples are commented out to avoid actual API calls.")
    print("   Uncomment the example calls and update the configuration")
    print("   with your TrueNAS server details to run them.")


if __name__ == "__main__":
    asyncio.run(main())
