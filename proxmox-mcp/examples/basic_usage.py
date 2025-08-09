#!/usr/bin/env python3
"""Basic usage example for Proxmox MCP Server."""

import asyncio
import json
import os
from typing import Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
config = {
    "host": os.getenv("PROXMOX_HOST"),
    "port": int(os.getenv("PROXMOX_PORT", "8006")),
    "protocol": os.getenv("PROXMOX_PROTOCOL", "https"),
    "username": os.getenv("PROXMOX_USERNAME"),
    "password": os.getenv("PROXMOX_PASSWORD"),
    "api_token": os.getenv("PROXMOX_API_TOKEN"),
    "realm": os.getenv("PROXMOX_REALM", "pve"),
    "verify_ssl": os.getenv("PROXMOX_SSL_VERIFY", "true").lower() == "true",
    "secret_key": os.getenv("SECRET_KEY"),
}

async def test_connection():
    """Test connection to Proxmox."""
    print("🔗 Testing Proxmox connection...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        result = await client.test_connection()
        
        if result["status"] == "success":
            print("✅ Connection successful!")
            print(f"   Version: {result['version']}")
        else:
            print("❌ Connection failed!")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

async def list_nodes():
    """List all nodes."""
    print("\n🏗️  Listing cluster nodes...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        nodes = await client.list_nodes()
        
        print(f"✅ Found {len(nodes)} nodes:")
        for node in nodes:
            print(f"   • {node['node']} - {node.get('status', 'unknown')}")
            
    except Exception as e:
        print(f"❌ Failed to list nodes: {e}")

async def list_vms():
    """List all virtual machines."""
    print("\n🖥️  Listing virtual machines...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        vms = await client.list_vms()
        
        print(f"✅ Found {len(vms)} virtual machines:")
        for vm in vms:
            status = vm.get('status', 'unknown')
            name = vm.get('name', f"VM {vm.get('vmid', 'unknown')}")
            node = vm.get('node', 'unknown')
            print(f"   • {name} (ID: {vm.get('vmid')}) - {status} on {node}")
            
    except Exception as e:
        print(f"❌ Failed to list VMs: {e}")

async def list_containers():
    """List all containers."""
    print("\n📦 Listing containers...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        containers = await client.list_containers()
        
        print(f"✅ Found {len(containers)} containers:")
        for container in containers:
            status = container.get('status', 'unknown')
            name = container.get('name', f"CT {container.get('vmid', 'unknown')}")
            node = container.get('node', 'unknown')
            print(f"   • {name} (ID: {container.get('vmid')}) - {status} on {node}")
            
    except Exception as e:
        print(f"❌ Failed to list containers: {e}")

async def list_storage():
    """List all storage pools."""
    print("\n💾 Listing storage pools...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        storage = await client.list_storage()
        
        print(f"✅ Found {len(storage)} storage pools:")
        for st in storage:
            storage_type = st.get('type', 'unknown')
            content = st.get('content', [])
            node = st.get('node', 'unknown')
            print(f"   • {st['storage']} ({storage_type}) - {', '.join(content)} on {node}")
            
    except Exception as e:
        print(f"❌ Failed to list storage: {e}")

async def get_version():
    """Get Proxmox version."""
    print("\n📋 Getting Proxmox version...")
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        client = ProxmoxClient(config)
        version = await client.get_version()
        
        print("✅ Proxmox version information:")
        for key, value in version.items():
            print(f"   • {key}: {value}")
            
    except Exception as e:
        print(f"❌ Failed to get version: {e}")

async def main():
    """Main function."""
    print("🚀 Proxmox MCP Server - Basic Usage Example")
    print("=" * 50)
    
    # Validate configuration
    if not config["host"]:
        print("❌ PROXMOX_HOST environment variable is required")
        return
    
    if not config["api_token"] and (not config["username"] or not config["password"]):
        print("❌ Either PROXMOX_API_TOKEN or PROXMOX_USERNAME/PROXMOX_PASSWORD is required")
        return
    
    print(f"📡 Connecting to Proxmox at {config['host']}:{config['port']}")
    
    # Run tests
    await test_connection()
    await get_version()
    await list_nodes()
    await list_vms()
    await list_containers()
    await list_storage()
    
    print("\n✅ Basic usage example completed!")

if __name__ == "__main__":
    asyncio.run(main())
