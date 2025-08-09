#!/usr/bin/env python3
"""Simple test script for iDRAC MCP Client."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_idrac_client():
    """Test basic iDRAC client functionality."""
    print("🧪 Testing iDRAC MCP Client")
    print("=" * 40)
    
    # Configuration
    config = {
        "host": os.getenv("IDRAC_HOST", "192.168.1.100"),
        "port": int(os.getenv("IDRAC_PORT", "443")),
        "protocol": os.getenv("IDRAC_PROTOCOL", "https"),
        "username": os.getenv("IDRAC_USERNAME", "root"),
        "password": os.getenv("IDRAC_PASSWORD", "test"),
        "ssl_verify": os.getenv("IDRAC_SSL_VERIFY", "false").lower() == "true"
    }
    
    print(f"Target iDRAC: {config['protocol']}://{config['host']}:{config['port']}")
    print(f"Username: {config['username']}")
    print(f"SSL Verify: {config['ssl_verify']}")
    
    try:
        # Import the client
        from idrac_client import IDracClient
        
        print("\n✅ Successfully imported IDracClient")
        
        # Test client initialization
        client = IDracClient(config)
        print("✅ Successfully created IDracClient instance")
        
        # Test connection (this will fail without a real iDRAC, but we can see the error)
        print("\n🔌 Testing connection...")
        try:
            async with client as c:
                result = await c.test_connection()
                print(f"✅ Connection successful: {result}")
        except Exception as e:
            print(f"❌ Connection failed (expected without real iDRAC): {e}")
            print("This is normal - we don't have a real iDRAC server to test against")
        
        print("\n✅ Basic client functionality test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This indicates an issue with the module structure")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_idrac_client())
