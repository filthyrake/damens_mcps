#!/usr/bin/env python3
"""Debug script to see raw iDRAC API responses."""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def debug_raw_responses():
    """Debug raw iDRAC API responses."""
    print("🔍 Debug Raw iDRAC API Responses")
    print("=" * 45)
    
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
            
            # Test 1: Raw Redfish root response
            print("\n🔍 Test 1: Redfish Root Response")
            print("-" * 30)
            try:
                raw_response = await client._make_request('GET', '/redfish/v1/')
                print("Raw response:")
                print(json.dumps(raw_response, indent=2))
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 2: Raw System response
            print("\n🔍 Test 2: System Response")
            print("-" * 30)
            try:
                raw_response = await client._make_request('GET', '/redfish/v1/Systems/System.Embedded.1')
                print("Raw response:")
                print(json.dumps(raw_response, indent=2))
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 3: Raw Chassis response
            print("\n🔍 Test 3: Chassis Response")
            print("-" * 30)
            try:
                raw_response = await client._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1')
                print("Raw response:")
                print(json.dumps(raw_response, indent=2))
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 4: Raw Power response
            print("\n🔍 Test 4: Power Response")
            print("-" * 30)
            try:
                raw_response = await client._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Power')
                print("Raw response:")
                print(json.dumps(raw_response, indent=2))
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            # Test 5: Raw Thermal response
            print("\n🔍 Test 5: Thermal Response")
            print("-" * 30)
            try:
                raw_response = await client._make_request('GET', '/redfish/v1/Chassis/System.Embedded.1/Thermal')
                print("Raw response:")
                print(json.dumps(raw_response, indent=2))
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            print("\n🎉 Raw response debugging completed!")
            print("💡 Check the responses above to see what the actual API is returning")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_raw_responses())
