#!/usr/bin/env python3
"""Test script for multi-server iDRAC management."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_multi_server():
    """Test multi-server functionality."""
    print("🚀 Testing Multi-Server iDRAC Management")
    print("=" * 50)
    
    try:
        from multi_server_manager import MultiServerManager
        
        # Initialize manager
        manager = MultiServerManager("fleet_servers.json")
        
        # Create sample configuration if none exists
        if not manager.servers:
            print("📝 Creating sample server configuration...")
            manager.create_sample_config()
            
            # Add your current server to the fleet
            current_host = os.getenv("IDRAC_HOST", "10.0.10.11")
            current_username = os.getenv("IDRAC_USERNAME", "root")
            current_password = os.getenv("IDRAC_PASSWORD", "")
            
            if current_host and current_password:
                manager.add_server(
                    name="current_server",
                    host=current_host,
                    username=current_username,
                    password=current_password,
                    port=int(os.getenv("IDRAC_PORT", "443")),
                    protocol=os.getenv("IDRAC_PROTOCOL", "https"),
                    ssl_verify=os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
                )
        
        # List configured servers
        print(f"\n📋 Configured Servers: {manager.list_servers()}")
        
        # Test all servers
        print(f"\n🔍 Testing all servers...")
        test_results = await manager.test_all_servers()
        
        for server_name, result in test_results.items():
            if result["status"] == "success":
                print(f"✅ {server_name}: {result['message']}")
            else:
                print(f"❌ {server_name}: {result['message']}")
        
        # Get fleet system information
        print(f"\n📊 Getting fleet system information...")
        fleet_info = await manager.get_fleet_system_info()
        
        for server_name, result in fleet_info.items():
            if result["status"] == "success":
                data = result["data"]
                print(f"✅ {server_name}:")
                print(f"   - Model: {data.get('model', 'N/A')}")
                print(f"   - Serial: {data.get('serial_number', 'N/A')}")
                print(f"   - Power: {data.get('power_state', 'N/A')}")
                print(f"   - Health: {data.get('health', 'N/A')}")
            else:
                print(f"❌ {server_name}: {result['message']}")
        
        # Get fleet health status
        print(f"\n🏥 Getting fleet health status...")
        fleet_health = await manager.get_fleet_health()
        
        for server_name, result in fleet_health.items():
            if result["status"] == "success":
                data = result["data"]
                print(f"✅ {server_name}: {data.get('overall_health', 'N/A')}")
            else:
                print(f"❌ {server_name}: {result['message']}")
        
        # Get fleet power status
        print(f"\n⚡ Getting fleet power status...")
        fleet_power = await manager.get_fleet_power_status()
        
        for server_name, result in fleet_power.items():
            if result["status"] == "success":
                data = result["data"]
                print(f"✅ {server_name}: {data.get('power_state', 'N/A')}")
            else:
                print(f"❌ {server_name}: {result['message']}")
        
        print(f"\n🎉 Multi-server tests completed!")
        print(f"💡 Fleet configuration saved to: {manager.config_file}")
        print(f"💡 Add more servers by editing the configuration file")
        
    except Exception as e:
        print(f"❌ Multi-server test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_multi_server())
