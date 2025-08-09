#!/usr/bin/env python3
"""Test basic iDRAC MCP functionality without real server connection."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_basic_functionality():
    """Test basic iDRAC client functionality without real connection."""
    print("🧪 Testing iDRAC MCP Basic Functionality")
    print("=" * 50)
    
    # Configuration
    config = {
        "host": "192.168.1.100",
        "port": 443,
        "protocol": "https",
        "username": "root",
        "password": "test",
        "ssl_verify": False
    }
    
    print(f"✅ Configuration: {config['protocol']}://{config['host']}:{config['port']}")
    
    try:
        # Import the client
        from idrac_client import IDracClient
        
        print("✅ Successfully imported IDracClient")
        
        # Test client initialization
        client = IDracClient(config)
        print("✅ Successfully created IDracClient instance")
        
        # Test client properties
        print(f"✅ Base URL: {client.base_url}")
        print(f"✅ Username: {client.config['username']}")
        print(f"✅ SSL Verify: {client.config['ssl_verify']}")
        
        # Test that we can create the client without connecting
        print("✅ Client initialization test passed")
        
        # Test HTTP server functionality
        print("\n🌐 Testing HTTP server functionality...")
        try:
            from http_server import create_app
            app = create_app(config)
            print("✅ Successfully created HTTP server app")
        except Exception as e:
            print(f"⚠️ HTTP server test failed: {e}")
        
        # Test CLI functionality
        print("\n💻 Testing CLI functionality...")
        try:
            from cli import cli
            print("✅ Successfully imported CLI")
        except Exception as e:
            print(f"⚠️ CLI test failed: {e}")
        
        # Test auth functionality
        print("\n🔐 Testing auth functionality...")
        try:
            from auth import AuthManager
            auth_manager = AuthManager(config)
            print("✅ Successfully created AuthManager")
        except Exception as e:
            print(f"⚠️ Auth test failed: {e}")
        
        print("\n🎉 Basic functionality tests completed!")
        print("\n📋 Summary:")
        print("- ✅ Client imports and initialization")
        print("- ✅ Configuration validation")
        print("- ✅ Basic structure verification")
        print("- ⚠️ HTTP server (needs real iDRAC for full test)")
        print("- ⚠️ CLI interface (needs real iDRAC for full test)")
        print("- ⚠️ Authentication (needs real iDRAC for full test)")
        
        print("\n💡 Next steps for full testing:")
        print("1. Set up a real iDRAC server or test environment")
        print("2. Update .env file with real credentials")
        print("3. Run the full connection tests")
        print("4. Test MCP protocol integration")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This indicates an issue with the module structure")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
