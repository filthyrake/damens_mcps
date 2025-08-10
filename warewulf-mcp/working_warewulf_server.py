#!/usr/bin/env python3
"""
Working Warewulf MCP Server.

This is the main entry point for running the Warewulf MCP server.
It can be used for both development and production deployment.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.server import WarewulfMCPServer
from src.utils.logging import setup_logging


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"⚠️  Configuration file not found: {config_path}")
            print("   Copy config.example.json to config.json and edit as needed")
            return {}
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"📁 Configuration loaded from {config_path}")
        return config
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return {}
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return {}


def load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    # Warewulf connection settings
    if os.getenv('WAREWULF_HOST'):
        config['host'] = os.getenv('WAREWULF_HOST')
    if os.getenv('WAREWULF_PORT'):
        config['port'] = int(os.getenv('WAREWULF_PORT'))
    if os.getenv('WAREWULF_PROTOCOL'):
        config['protocol'] = os.getenv('WAREWULF_PROTOCOL')
    
    # Authentication
    if os.getenv('WAREWULF_USERNAME'):
        config['username'] = os.getenv('WAREWULF_USERNAME')
    if os.getenv('WAREWULF_PASSWORD'):
        config['password'] = os.getenv('WAREWULF_PASSWORD')
    if os.getenv('WAREWULF_API_TOKEN'):
        config['api_token'] = os.getenv('WAREWULF_API_TOKEN')
    
    # SSL settings
    if os.getenv('WAREWULF_SSL_VERIFY'):
        config['ssl_verify'] = os.getenv('WAREWULF_SSL_VERIFY').lower() == 'true'
    
    # Timeout
    if os.getenv('WAREWULF_TIMEOUT'):
        config['timeout'] = int(os.getenv('WAREWULF_TIMEOUT'))
    
    return config


async def main():
    """Main entry point."""
    print("🚀 Starting Warewulf MCP Server...")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Override with environment variables if present
    env_config = load_env_config()
    config.update(env_config)
    
    if not config:
        print("❌ No configuration available. Please set up config.json or environment variables.")
        print("\nQuick setup:")
        print("1. Copy config.example.json to config.json")
        print("2. Edit config.json with your Warewulf server details")
        print("3. Or set environment variables (see env.example)")
        sys.exit(1)
    
    # Validate required configuration
    required_fields = ['host', 'port', 'protocol']
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        print(f"❌ Missing required configuration fields: {', '.join(missing_fields)}")
        sys.exit(1)
    
    # Check authentication
    has_auth = (
        (config.get('username') and config.get('password')) or 
        config.get('api_token')
    )
    
    if not has_auth:
        print("❌ No authentication credentials provided")
        print("   Set either username/password or api_token in configuration")
        sys.exit(1)
    
    print("✅ Configuration validated")
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   Protocol: {config['protocol']}")
    print(f"   SSL Verify: {config.get('ssl_verify', True)}")
    print(f"   Timeout: {config.get('timeout', 30)}s")
    
    # Create and run server
    try:
        print("\n🔧 Initializing MCP server...")
        server = WarewulfMCPServer(config)
        
        print("✅ MCP server initialized successfully")
        print("\n📋 Available tools:")
        tools = server.get_tools()
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
        
        print(f"\n🚀 Starting MCP server...")
        print("   Press Ctrl+C to stop")
        
        # Run the server
        await server.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check your Warewulf server is running and accessible")
        print("   2. Verify your credentials are correct")
        print("   3. Check network connectivity and firewall settings")
        print("   4. Run test_server.py to test with mock data")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
