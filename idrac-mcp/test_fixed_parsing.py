#!/usr/bin/env python3
"""Test script with fixed parsing logic for iDRAC Redfish API."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_fixed_parsing():
    """Test with fixed parsing logic."""
    print("🔧 Testing Fixed iDRAC Parsing")
    print("=" * 40)
    
    # Load configuration from .env
    config = {
        "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
        "port": int(os.getenv("IDRAC_PORT", "443")),
        "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
        "username": os.getenv("IDRAC_USERNAME", "root"),
        "password": os.getenv("IDRAC_PASSWORD", ""),
        "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
    }
    
    print(f"🎯 Target: {config['protocol']}://{config['host']}:{config['port']}")
    print()
    
    try:
        from idrac_client import IDracClient
        
        print("🔌 Connecting to iDRAC...")
        async with IDracClient(config) as client:
            print("✅ Connected successfully!")
            
            # Test 1: Fixed System Information
            print("\n📊 Test 1: System Information (Fixed)")
            print("-" * 40)
            try:
                raw_result = await client._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
                
                # Extract actual fields from Redfish response
                system_info = {
                    "model": raw_result.get('Model', 'N/A'),
                    "manufacturer": raw_result.get('Manufacturer', 'N/A'),
                    "serial_number": raw_result.get('SerialNumber', 'N/A'),
                    "part_number": raw_result.get('PartNumber', 'N/A'),
                    "sku": raw_result.get('SKU', 'N/A'),
                    "system_type": raw_result.get('SystemType', 'N/A'),
                    "bios_version": raw_result.get('BiosVersion', 'N/A'),
                    "power_state": raw_result.get('PowerState', 'N/A'),
                    "health": raw_result.get('Status', {}).get('Health', 'N/A'),
                    "state": raw_result.get('Status', {}).get('State', 'N/A')
                }
                
                print("✅ System Information:")
                for key, value in system_info.items():
                    print(f"   - {key.replace('_', ' ').title()}: {value}")
                    
            except Exception as e:
                print(f"❌ System info failed: {e}")
            
            # Test 2: Fixed Hardware Inventory
            print("\n🔧 Test 2: Hardware Inventory (Fixed)")
            print("-" * 40)
            try:
                # Get processors
                processors_result = await client._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Processors')
                processors = processors_result.get('Members', [])
                
                # Get memory
                memory_result = await client._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Memory')
                memory_modules = memory_result.get('Members', [])
                
                # Get storage
                storage_result = await client._make_request('GET', '/redfish/v1/Systems/System.Embedded.1/Storage')
                storage_controllers = storage_result.get('Members', [])
                
                print(f"✅ Hardware Inventory:")
                print(f"   - Processors: {len(processors)}")
                print(f"   - Memory Modules: {len(memory_modules)}")
                print(f"   - Storage Controllers: {len(storage_controllers)}")
                
                # Show processor details
                for i, proc in enumerate(processors):
                    proc_id = proc.get('@odata.id', '').split('/')[-1]
                    print(f"   - Processor {i+1}: {proc_id}")
                    
            except Exception as e:
                print(f"❌ Hardware inventory failed: {e}")
            
            # Test 3: Fixed Thermal Status
            print("\n🌡️ Test 3: Thermal Status (Fixed)")
            print("-" * 40)
            try:
                thermal_result = await client._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Thermal')
                
                temperatures = thermal_result.get('Temperatures', [])
                fans = thermal_result.get('Fans', [])
                
                print(f"✅ Thermal Status:")
                print(f"   - Temperature Sensors: {len(temperatures)}")
                print(f"   - Fans: {len(fans)}")
                
                # Show temperature readings
                for temp in temperatures:
                    name = temp.get('Name', 'Unknown')
                    reading = temp.get('ReadingCelsius', 'N/A')
                    health = temp.get('Status', {}).get('Health', 'N/A')
                    print(f"   - {name}: {reading}°C ({health})")
                
                # Show fan readings
                for fan in fans:
                    name = fan.get('Name', 'Unknown')
                    reading = fan.get('Reading', 'N/A')
                    health = fan.get('Status', {}).get('Health', 'N/A')
                    print(f"   - {name}: {reading} RPM ({health})")
                    
            except Exception as e:
                print(f"❌ Thermal status failed: {e}")
            
            # Test 4: Fixed Power Status
            print("\n⚡ Test 4: Power Status (Fixed)")
            print("-" * 40)
            try:
                power_result = await client._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Power')
                
                power_supplies = power_result.get('PowerSupplies', [])
                voltages = power_result.get('Voltages', [])
                
                print(f"✅ Power Status:")
                print(f"   - Power Supplies: {len(power_supplies)}")
                print(f"   - Voltage Sensors: {len(voltages)}")
                
                # Show power supply details
                for i, ps in enumerate(power_supplies):
                    name = ps.get('Name', f'PSU {i+1}')
                    state = ps.get('Status', {}).get('State', 'N/A')
                    health = ps.get('Status', {}).get('Health', 'N/A')
                    print(f"   - {name}: {state} ({health})")
                    
            except Exception as e:
                print(f"❌ Power status failed: {e}")
            
            print("\n🎉 Fixed parsing tests completed!")
            print("✅ Now showing actual data from your iDRAC server")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_parsing())
