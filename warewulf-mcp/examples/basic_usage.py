#!/usr/bin/env python3
"""
Basic usage example for the Warewulf MCP Server.

This example demonstrates how to interact with the MCP server
and perform basic operations.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.warewulf_client import WarewulfClient
from src.utils.logging import setup_logging


async def main():
    """Main example function."""
    print("🚀 Warewulf MCP Server - Basic Usage Example")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging(level="INFO")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        print("❌ Configuration file not found")
        print("   Please copy config.example.json to config.json and edit it")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    print("✅ Configuration loaded")
    
    # Initialize client
    try:
        client = WarewulfClient(config)
        print("✅ Warewulf client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Test connection
    print("\n🔍 Testing connection...")
    try:
        result = client.test_connection()
        if result.get('success'):
            print("✅ Connection successful")
        else:
            print(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return
    
    # Get server version
    print("\n📋 Getting server version...")
    try:
        result = client.get_version()
        if result.get('success'):
            version = result.get('data', {}).get('version', 'Unknown')
            api_version = result.get('data', {}).get('api_version', 'Unknown')
            print(f"✅ Version: {version} (API: {api_version})")
        else:
            print(f"❌ Failed to get version: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Version retrieval failed: {e}")
    
    # List nodes
    print("\n🖥️  Listing nodes...")
    try:
        result = client.list_nodes()
        if result.get('success'):
            nodes = result.get('data', [])
            print(f"✅ Found {len(nodes)} nodes:")
            for node in nodes:
                print(f"   - {node.get('name', 'Unknown')} ({node.get('id', 'Unknown')})")
                print(f"     IP: {node.get('ipaddr', 'N/A')}")
                print(f"     Status: {node.get('status', 'Unknown')}")
                print(f"     Profile: {node.get('profile', 'N/A')}")
                print()
        else:
            print(f"❌ Failed to list nodes: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Node listing failed: {e}")
    
    # List profiles
    print("\n📁 Listing profiles...")
    try:
        result = client.list_profiles()
        if result.get('success'):
            profiles = result.get('data', [])
            print(f"✅ Found {len(profiles)} profiles:")
            for profile in profiles:
                print(f"   - {profile.get('name', 'Unknown')} ({profile.get('id', 'Unknown')})")
                print(f"     Description: {profile.get('description', 'N/A')}")
                print(f"     Kernel: {profile.get('kernel', 'N/A')}")
                print()
        else:
            print(f"❌ Failed to list profiles: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Profile listing failed: {e}")
    
    # List images
    print("\n🖼️  Listing images...")
    try:
        result = client.list_images()
        if result.get('success'):
            images = result.get('data', [])
            print(f"✅ Found {len(images)} images:")
            for image in images:
                print(f"   - {image.get('name', 'Unknown')}")
                print(f"     Size: {image.get('size', 'N/A')}")
                print(f"     Status: {image.get('status', 'N/A')}")
                print(f"     Created: {image.get('created', 'N/A')}")
                print()
        else:
            print(f"❌ Failed to list images: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Image listing failed: {e}")
    
    # List overlays
    print("\n📂 Listing overlays...")
    try:
        result = client.list_overlays()
        if result.get('success'):
            overlays = result.get('data', [])
            print(f"✅ Found {len(overlays)} overlays:")
            for overlay in overlays:
                print(f"   - {overlay.get('name', 'Unknown')}")
                print(f"     Description: {overlay.get('description', 'N/A')}")
                files = overlay.get('files', [])
                if files:
                    print(f"     Files: {', '.join(files)}")
                print()
        else:
            print(f"❌ Failed to list overlays: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Overlay listing failed: {e}")
    
    print("\n🎉 Basic usage example completed!")
    print("\n💡 Next steps:")
    print("   1. Explore specific node details with get_node()")
    print("   2. Create or update nodes with create_node()/update_node()")
    print("   3. Manage profiles and images")
    print("   4. Use the MCP server for AI-assisted management")


if __name__ == "__main__":
    asyncio.run(main())
