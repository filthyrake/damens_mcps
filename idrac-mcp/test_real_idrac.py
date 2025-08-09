#!/usr/bin/env python3
"""Safe test script for real iDRAC server - READ ONLY COMMANDS ONLY."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_real_idrac():
    """Test real iDRAC server with READ-ONLY commands only."""
    print("🔒 Testing Real iDRAC Server - READ ONLY MODE")
    print("=" * 55)
    print("⚠️  SAFETY: Only read-only commands will be executed")
    print("⚠️  NO power operations, reboots, or configuration changes")
    print()
    
    # Load configuration from .env
    config = {
        "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
        "port": int(os.getenv("IDRAC_PORT", "443")),
        "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
        "username": os.getenv("IDRAC_USERNAME", "root"),
        "password": os.getenv("IDRAC_PASSWORD", ""),
        "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
    }
    
    # Validate that we have the required values
    if not config["host"] or config["host"] == "192.168.1.100":
        print("❌ Error: IDRAC_HOST not set or using default value")
        print("Please update your .env file with your real iDRAC server IP")
        return
    
    if not config["password"] or config["password"] == "your-password":
        print("❌ Error: IDRAC_PASSWORD not set or using default value")
        print("Please update your .env file with your real iDRAC password")
        return
    
    print(f"🎯 Target: {config['protocol']}://{config['host']}:{config['port']}")
    print(f"👤 Username: {config['username']}")
    print(f"🔒 SSL Verify: {config['ssl_verify']}")
    print()
    
    try:
        from idrac_client import IDracClient
        
        print("🔌 Connecting to iDRAC...")
        async with IDracClient(config) as client:
            print("✅ Connected successfully!")
            
            # Test 1: Basic connection test
            print("\n🔍 Test 1: Connection Test")
            result = await client.test_connection()
            print(f"✅ Connection test: {result.get('message', 'Success')}")
            
            # Test 2: System Information (READ ONLY)
            print("\n📊 Test 2: System Information")
            try:
                system_info = await client.get_system_info()
                print(f"✅ System info retrieved: {system_info.get('message', 'Success')}")
                if 'data' in system_info:
                    data = system_info['data']
                    print(f"   - Model: {data.get('model', 'N/A')}")
                    print(f"   - Manufacturer: {data.get('manufacturer', 'N/A')}")
                    print(f"   - Serial Number: {data.get('serial_number', 'N/A')}")
            except Exception as e:
                print(f"⚠️ System info failed: {e}")
            
            # Test 3: System Health (READ ONLY)
            print("\n🏥 Test 3: System Health")
            try:
                health = await client.get_system_health()
                print(f"✅ Health check: {health.get('message', 'Success')}")
                if 'data' in health:
                    data = health['data']
                    print(f"   - Overall Health: {data.get('overall_health', 'N/A')}")
                    print(f"   - Status: {data.get('status', 'N/A')}")
            except Exception as e:
                print(f"⚠️ Health check failed: {e}")
            
            # Test 4: Power Status (READ ONLY)
            print("\n⚡ Test 4: Power Status")
            try:
                power = await client.get_power_status()
                print(f"✅ Power status: {power.get('message', 'Success')}")
                if 'data' in power:
                    data = power['data']
                    print(f"   - Power State: {data.get('power_state', 'N/A')}")
                    print(f"   - Power Consumption: {data.get('power_consumption', 'N/A')}")
            except Exception as e:
                print(f"⚠️ Power status failed: {e}")
            
            # Test 5: Hardware Inventory (READ ONLY)
            print("\n🔧 Test 5: Hardware Inventory")
            try:
                inventory = await client.get_hardware_inventory()
                print(f"✅ Hardware inventory: {inventory.get('message', 'Success')}")
                if 'data' in inventory:
                    data = inventory['data']
                    print(f"   - CPU Count: {len(data.get('processors', []))}")
                    print(f"   - Memory Modules: {len(data.get('memory_modules', []))}")
                    print(f"   - Storage Drives: {len(data.get('storage_drives', []))}")
            except Exception as e:
                print(f"⚠️ Hardware inventory failed: {e}")
            
            # Test 6: Thermal Status (READ ONLY)
            print("\n🌡️ Test 6: Thermal Status")
            try:
                thermal = await client.get_thermal_status()
                print(f"✅ Thermal status: {thermal.get('message', 'Success')}")
                if 'data' in thermal:
                    data = thermal['data']
                    print(f"   - Temperature: {data.get('temperature', 'N/A')}")
                    print(f"   - Fan Status: {data.get('fan_status', 'N/A')}")
            except Exception as e:
                print(f"⚠️ Thermal status failed: {e}")
            
            # Test 7: Network Configuration (READ ONLY)
            print("\n🌐 Test 7: Network Configuration")
            try:
                network = await client.get_network_config()
                print(f"✅ Network config: {network.get('message', 'Success')}")
                if 'data' in network:
                    data = network['data']
                    print(f"   - IP Address: {data.get('ip_address', 'N/A')}")
                    print(f"   - Subnet Mask: {data.get('subnet_mask', 'N/A')}")
            except Exception as e:
                print(f"⚠️ Network config failed: {e}")
            
            # Test 8: Storage Controllers (READ ONLY)
            print("\n💾 Test 8: Storage Controllers")
            try:
                storage = await client.get_storage_controllers()
                print(f"✅ Storage controllers: {storage.get('message', 'Success')}")
                if 'data' in storage:
                    data = storage['data']
                    print(f"   - Controller Count: {len(data.get('controllers', []))}")
            except Exception as e:
                print(f"⚠️ Storage controllers failed: {e}")
            
            # Test 9: Firmware Versions (READ ONLY)
            print("\n📦 Test 9: Firmware Versions")
            try:
                firmware = await client.get_firmware_versions()
                print(f"✅ Firmware versions: {firmware.get('message', 'Success')}")
                if 'data' in firmware:
                    data = firmware['data']
                    print(f"   - Firmware Count: {len(data.get('firmware', []))}")
            except Exception as e:
                print(f"⚠️ Firmware versions failed: {e}")
            
            # Test 10: Users (READ ONLY)
            print("\n👥 Test 10: Users")
            try:
                users = await client.get_users()
                print(f"✅ Users: {users.get('message', 'Success')}")
                if 'data' in users:
                    data = users['data']
                    print(f"   - User Count: {len(data.get('users', []))}")
            except Exception as e:
                print(f"⚠️ Users failed: {e}")
            
            print("\n🎉 All READ-ONLY tests completed!")
            print("✅ No power operations or configuration changes were made")
            print("✅ Server remains in its original state")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your .env configuration and network connectivity")

if __name__ == "__main__":
    asyncio.run(test_real_idrac())
