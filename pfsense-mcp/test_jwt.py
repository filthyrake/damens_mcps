#!/usr/bin/env python3
"""
Test JWT authentication with pfSense 2.8.0 API.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from auth import PfSenseAuth

async def test_jwt():
    """Test JWT authentication."""
    
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
    
    print(f"Testing JWT authentication on {config['host']}:{config['port']}")
    print(f"Username: {config['username']}")
    print(f"Password: {'*' * len(config['password']) if config['password'] else 'NOT SET'}")
    print("=" * 60)
    
    auth = PfSenseAuth(config)
    
    try:
        # Test JWT endpoint
        print("Testing JWT endpoint...")
        token = await auth.get_jwt_token()
        print(f"✅ JWT Token obtained: {token[:50]}...")
        
        # Test using the token
        print("\nTesting API call with JWT token...")
        headers = auth.get_jwt_headers(token)
        print(f"Headers: {headers}")
        
        # Test a simple API call
        session = await auth.create_session()
        url = f"{auth.get_base_url()}/api/v2/diagnostics/arp_table"
        
        async with session.get(url, headers=headers, allow_redirects=False) as response:
            print(f"Response status: {response.status}")
            if response.status == 200:
                result = await response.json()
                print(f"✅ API call successful: {str(result)[:100]}...")
            else:
                text = await response.text()
                print(f"❌ API call failed: {text}")
                
    except Exception as e:
        print(f"❌ JWT authentication failed: {str(e)}")
        
        # Try to get more details about the error
        try:
            session = await auth.create_session()
            url = f"{auth.get_base_url()}/api/v2/auth/jwt"
            
            jwt_data = {
                "username": config["username"],
                "password": config["password"]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with session.post(url, json=jwt_data, headers=headers) as response:
                print(f"JWT endpoint response status: {response.status}")
                text = await response.text()
                print(f"JWT endpoint response: {text}")
                
        except Exception as e2:
            print(f"Failed to test JWT endpoint: {str(e2)}")

if __name__ == "__main__":
    asyncio.run(test_jwt())
