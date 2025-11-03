#!/usr/bin/env python3
"""
Basic usage examples for the Proxmox MCP Server.

This script demonstrates how to use the Proxmox MCP server
and its various tools for managing Proxmox VE environments.

NOTE: This example requires a valid config.json file with Proxmox credentials.
Copy config.example.json to config.json and update with your settings.
"""

import json
import sys
import os

def load_config():
    """Load configuration from config.json."""
    config_paths = [
        'config.json',
        os.path.join(os.path.dirname(__file__), '..', 'config.json'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json'),
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
    
    print("❌ Error: config.json not found!")
    print("Please copy config.example.json to config.json and update with your Proxmox settings.")
    sys.exit(1)

def test_proxmox_client():
    """Test the Proxmox client directly."""
    print("🔧 Testing Proxmox Client Directly...")
    
    # Add parent directory to path to import modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        # Load configuration
        config = load_config()
        
        # Create client instance
        print("  📡 Creating Proxmox client...")
        client = ProxmoxClient(
            host=config['host'],
            port=config['port'],
            protocol=config['protocol'],
            username=config['username'],
            password=config['password'],
            realm=config.get('realm', 'pve'),
            ssl_verify=config.get('ssl_verify', False)
        )
        
        # Test connection
        print("  🔌 Testing connection...")
        result = client.test_connection()
        print(f"  ✅ Connection result: {result}")
        
        # Get version info
        print("  📊 Getting Proxmox version...")
        version_info = client.get_version()
        print(f"  ✅ Version info: {version_info.get('status', 'unknown')}")
        
        # List nodes
        print("  🖥️  Listing nodes...")
        nodes = client.list_nodes()
        print(f"  ✅ Nodes found: {len(nodes) if isinstance(nodes, list) else 'N/A'}")
        
        if isinstance(nodes, list):
            for node in nodes:
                node_name = node.get('node', 'unknown')
                status = node.get('status', 'unknown')
                print(f"    📍 Node: {node_name} - Status: {status}")
        
        print("  🎉 Proxmox client test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  💡 Make sure you're in the proxmox-mcp directory and src/ exists")
        return False
    except FileNotFoundError as e:
        print(f"  ❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error testing Proxmox client: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vm_operations():
    """Test VM operations."""
    print("\n🖥️  Testing VM Operations...")
    
    # Add parent directory to path to import modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        # Load configuration
        config = load_config()
        
        # Create client
        client = ProxmoxClient(
            host=config['host'],
            port=config['port'],
            protocol=config['protocol'],
            username=config['username'],
            password=config['password'],
            realm=config.get('realm', 'pve'),
            ssl_verify=config.get('ssl_verify', False)
        )
        
        # List VMs
        print("  📋 Listing all VMs...")
        vms = client.list_vms()
        print(f"  ✅ Total VMs: {len(vms) if isinstance(vms, list) else 'N/A'}")
        
        if isinstance(vms, list) and vms:
            for vm in vms[:3]:  # Show first 3 VMs
                vmid = vm.get('vmid', 'N/A')
                name = vm.get('name', 'unnamed')
                status = vm.get('status', 'unknown')
                print(f"    🖥️  VM {vmid}: {name} ({status})")
        
        print("  🎉 VM operations test completed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing VM operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_operations():
    """Test storage operations."""
    print("\n💾 Testing Storage Operations...")
    
    # Add parent directory to path to import modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        from src.proxmox_client import ProxmoxClient
        
        # Load configuration
        config = load_config()
        
        # Create client
        client = ProxmoxClient(
            host=config['host'],
            port=config['port'],
            protocol=config['protocol'],
            username=config['username'],
            password=config['password'],
            realm=config.get('realm', 'pve'),
            ssl_verify=config.get('ssl_verify', False)
        )
        
        # List storage
        print("  📋 Listing storage...")
        storage = client.list_storage()
        print(f"  ✅ Storage pools: {len(storage) if isinstance(storage, list) else 'N/A'}")
        
        if isinstance(storage, list) and storage:
            for stor in storage[:3]:  # Show first 3 storage pools
                storage_id = stor.get('storage', 'N/A')
                storage_type = stor.get('type', 'unknown')
                status = stor.get('status', 'unknown')
                print(f"    💾 Storage: {storage_id} ({storage_type}) - {status}")
        
        print("  🎉 Storage operations test completed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing storage operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Proxmox MCP Server - Basic Usage Examples")
    print("=" * 60)
    print()
    
    # Check for config file first
    if not any(os.path.exists(p) for p in ['config.json', '../config.json']):
        print("⚠️  Configuration file not found!")
        print()
        print("Please create config.json from config.example.json:")
        print("  1. Copy: cp config.example.json config.json")
        print("  2. Edit config.json with your Proxmox credentials")
        print("  3. Run this example again")
        print()
        sys.exit(1)
    
    # Run tests
    results = {}
    
    results['client'] = test_proxmox_client()
    results['vms'] = test_vm_operations()
    results['storage'] = test_storage_operations()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"  🔧 Proxmox Client:   {'✅ PASS' if results.get('client') else '❌ FAIL'}")
    print(f"  🖥️  VM Operations:    {'✅ PASS' if results.get('vms') else '❌ FAIL'}")
    print(f"  💾 Storage Ops:      {'✅ PASS' if results.get('storage') else '❌ FAIL'}")
    print()
    
    if all(results.values()):
        print("🎉 All tests passed! The Proxmox MCP client is working correctly.")
        print()
        print("💡 Next steps:")
        print("   1. Start the MCP server:")
        print("      python working_proxmox_server.py")
        print()
        print("   2. Configure Claude Desktop to use this server")
        print("      Edit ~/.config/claude/mcp.json (see README.md)")
        print()
        print("   3. Test the tools in Claude Desktop")
        print()
    else:
        print("⚠️  Some tests failed. Please check:")
        print("   • config.json has correct Proxmox credentials")
        print("   • Proxmox server is accessible from this machine")
        print("   • Network connectivity and firewall rules")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
