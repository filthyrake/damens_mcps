#!/usr/bin/env python3
"""Basic usage example for iDRAC MCP Client."""

import asyncio
import os
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from idrac_client import IDracClient

# Load environment variables
load_dotenv()


async def main():
    """Main function demonstrating basic iDRAC operations."""
    print("🚀 iDRAC MCP Client - Basic Usage Example")
    print("=" * 50)
    
    # Initialize iDRAC client
    idrac_config = {
        "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
        "port": int(os.getenv("IDRAC_PORT", "443")),
        "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
        "username": os.getenv("IDRAC_USERNAME", "root"),
        "password": os.getenv("IDRAC_PASSWORD", ""),
        "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
    }
    
    print(f"Connecting to iDRAC at {idrac_config['protocol']}://{idrac_config['host']}:{idrac_config['port']}")
    
    try:
        async with IDracClient(idrac_config) as client:
            print("✅ Connected to iDRAC")
            
            # Test connection
            print("\n🔍 Testing connection...")
            result = await client.test_connection()
            print(f"Connection test: {result['message']}")
            
            if result['status'] == 'success':
                # Get system information
                print("\n📊 Getting system information...")
                system_info = await client.get_system_info()
                print(f"System info: {system_info['message']}")
                
                # Get system health
                print("\n🏥 Getting system health...")
                health = await client.get_system_health()
                print(f"System health: {health['message']}")
                print(f"Health status: {health['data']['overall_health']}")
                
                # Get power status
                print("\n⚡ Getting power status...")
                power = await client.get_power_status()
                print(f"Power status: {power['message']}")
                print(f"Power state: {power['data']['power_state']}")
                
                # Get hardware inventory
                print("\n🔧 Getting hardware inventory...")
                inventory = await client.get_hardware_inventory()
                print(f"Hardware inventory: {inventory['message']}")
                
                # Get thermal status
                print("\n🌡️ Getting thermal status...")
                thermal = await client.get_thermal_status()
                print(f"Thermal status: {thermal['message']}")
                
                # Get network configuration
                print("\n🌐 Getting network configuration...")
                network = await client.get_network_config()
                print(f"Network config: {network['message']}")
                
                # Get storage controllers
                print("\n💾 Getting storage controllers...")
                storage = await client.get_storage_controllers()
                print(f"Storage controllers: {storage['message']}")
                
                # Get firmware versions
                print("\n📦 Getting firmware versions...")
                firmware = await client.get_firmware_versions()
                print(f"Firmware versions: {firmware['message']}")
                
                # Get users
                print("\n👥 Getting users...")
                users = await client.get_users()
                print(f"Users: {users['message']}")
                
            else:
                print(f"❌ Connection failed: {result['data']['error']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
