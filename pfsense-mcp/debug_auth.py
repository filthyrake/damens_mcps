#!/usr/bin/env python3
"""
Debug pfSense 2.8.0 API authentication.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from auth import PfSenseAuth

async def debug_auth():
    """Debug authentication step by step."""
    
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
    
    print(f"Debugging pfSense authentication on {config['host']}:{config['port']}")
    print(f"Username: {config['username']}")
    print(f"Password: {'*' * len(config['password']) if config['password'] else 'NOT SET'}")
    print(f"API Key: {config['api_key'][:10]}..." if config['api_key'] else 'NOT SET')
    print("=" * 60)
    
    auth = PfSenseAuth(config)
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    try:
        session = await auth.create_session()
        url = f"{auth.get_base_url()}/"
        async with session.get(url, allow_redirects=False) as response:
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            if response.status == 200:
                print("   ✅ Basic connectivity works")
            else:
                print("   ❌ Basic connectivity failed")
    except Exception as e:
        print(f"   ❌ Basic connectivity error: {e}")
    
    # Test 2: API key authentication
    print("\n2. Testing API key authentication...")
    try:
        headers = auth.get_auth_headers()
        print(f"   Headers: {headers}")
        
        url = f"{auth.get_base_url()}/api/v2/diagnostics/arp_table"
        async with session.get(url, headers=headers, allow_redirects=False) as response:
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            text = await response.text()
            print(f"   Response: {text[:200]}...")
            
            if response.status == 200:
                print("   ✅ API key authentication works")
            else:
                print("   ❌ API key authentication failed")
    except Exception as e:
        print(f"   ❌ API key authentication error: {e}")
    
    # Test 3: JWT authentication
    print("\n3. Testing JWT authentication...")
    try:
        print("   Getting JWT token...")
        token = await auth.get_jwt_token()
        print(f"   JWT Token: {token[:50]}...")
        
        jwt_headers = auth.get_jwt_headers(token)
        print(f"   JWT Headers: {jwt_headers}")
        
        url = f"{auth.get_base_url()}/api/v2/diagnostics/arp_table"
        async with session.get(url, headers=jwt_headers, allow_redirects=False) as response:
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            text = await response.text()
            print(f"   Response: {text[:200]}...")
            
            if response.status == 200:
                print("   ✅ JWT authentication works")
            else:
                print("   ❌ JWT authentication failed")
    except Exception as e:
        print(f"   ❌ JWT authentication error: {e}")
    
    # Test 4: Try different header formats
    print("\n4. Testing different header formats...")
    try:
        # Test without Bearer prefix
        headers_no_bearer = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": config['api_key']
        }
        print(f"   Testing without Bearer: {headers_no_bearer}")
        
        url = f"{auth.get_base_url()}/api/v2/diagnostics/arp_table"
        async with session.get(url, headers=headers_no_bearer, allow_redirects=False) as response:
            print(f"   Status: {response.status}")
            text = await response.text()
            print(f"   Response: {text[:200]}...")
            
            if response.status == 200:
                print("   ✅ No Bearer prefix works")
            else:
                print("   ❌ No Bearer prefix failed")
    except Exception as e:
        print(f"   ❌ No Bearer prefix error: {e}")
    
    # Test 5: Try X-API-Key header
    print("\n5. Testing X-API-Key header...")
    try:
        headers_x_api_key = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": config['api_key']
        }
        print(f"   Testing X-API-Key: {headers_x_api_key}")
        
        url = f"{auth.get_base_url()}/api/v2/diagnostics/arp_table"
        async with session.get(url, headers=headers_x_api_key, allow_redirects=False) as response:
            print(f"   Status: {response.status}")
            text = await response.text()
            print(f"   Response: {text[:200]}...")
            
            if response.status == 200:
                print("   ✅ X-API-Key header works")
            else:
                print("   ❌ X-API-Key header failed")
    except Exception as e:
        print(f"   ❌ X-API-Key header error: {e}")
    
    await session.close()

if __name__ == "__main__":
    asyncio.run(debug_auth())
