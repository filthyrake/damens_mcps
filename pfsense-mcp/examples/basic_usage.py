#!/usr/bin/env python3
"""
Basic usage example for pfSense MCP Server.
This script demonstrates how to use the pfSense client directly.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pfsense_client import HTTPPfSenseClient, PfSenseAPIError


async def test_pfsense_connection():
    """Test basic connection to pfSense."""
    print("🔌 Testing pfSense connection...")
    
    config = {
        "host": os.getenv("PFSENSE_HOST", "192.168.1.1"),  # Change this to your pfSense IP
        "port": os.getenv("PFSENSE_PORT", "443"),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true")
    }
    
    try:
        async with HTTPPfSenseClient(config) as client:
            # Test connection
            if await client.test_connection():
                print("✅ Successfully connected to pfSense!")
                
                # Get system info
                print("\n📊 Getting system information...")
                system_info = await client.get_system_info()
                print(f"System Info: {system_info}")
                
                # Get interfaces
                print("\n🌐 Getting network interfaces...")
                interfaces = await client.get_interfaces()
                print(f"Interfaces: {interfaces}")
                
                # Get firewall rules
                print("\n🔥 Getting firewall rules...")
                firewall_rules = await client.get_firewall_rules()
                print(f"Firewall Rules: {firewall_rules}")
                
                return True
            else:
                print("❌ Failed to connect to pfSense")
                return False
                
    except PfSenseAPIError as e:
        print(f"❌ pfSense API error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


async def demonstrate_firewall_management():
    """Demonstrate firewall rule management."""
    print("\n🔥 Demonstrating firewall management...")
    
    config = {
        "host": os.getenv("PFSENSE_HOST", "192.168.1.1"),  # Change this to your pfSense IP
        "port": os.getenv("PFSENSE_PORT", "443"),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true")
    }
    
    try:
        async with HTTPPfSenseClient(config) as client:
            # Get current firewall rules
            print("📋 Current firewall rules:")
            rules = await client.get_firewall_rules()
            print(f"Found {len(rules.get('data', []))} rules")
            
            # Example: Create a test firewall rule (commented out for safety)
            # print("\n➕ Creating test firewall rule...")
            # test_rule = {
            #     "action": "pass",
            #     "interface": "wan",
            #     "direction": "in",
            #     "source": "any",
            #     "destination": "any",
            #     "description": "Test rule from MCP server"
            # }
            # result = await client.create_firewall_rule(test_rule)
            # print(f"Created rule: {result}")
            
    except Exception as e:
        print(f"❌ Error in firewall management: {str(e)}")


async def demonstrate_system_management():
    """Demonstrate system management features."""
    print("\n⚙️ Demonstrating system management...")
    
    config = {
        "host": os.getenv("PFSENSE_HOST", "192.168.1.1"),  # Change this to your pfSense IP
        "port": os.getenv("PFSENSE_PORT", "443"),
        "protocol": os.getenv("PFSENSE_PROTOCOL", "https"),
        "api_key": os.getenv("PFSENSE_API_KEY"),
        "username": os.getenv("PFSENSE_USERNAME"),
        "password": os.getenv("PFSENSE_PASSWORD"),
        "ssl_verify": os.getenv("PFSENSE_SSL_VERIFY", "true")
    }
    
    try:
        async with HTTPPfSenseClient(config) as client:
            # Get system health
            print("💓 System health:")
            health = await client.get_system_health()
            print(f"Health: {health}")
            
            # Get services
            print("\n🔧 Running services:")
            services = await client.get_services()
            print(f"Services: {services}")
            
            # Get DHCP leases
            print("\n📋 DHCP leases:")
            leases = await client.get_dhcp_leases()
            print(f"DHCP Leases: {leases}")
            
    except Exception as e:
        print(f"❌ Error in system management: {str(e)}")


async def main():
    """Main function to run all demonstrations."""
    print("🚀 pfSense MCP Server - Basic Usage Example")
    print("=" * 50)
    
    # Check if environment variables are set
    if not os.getenv("PFSENSE_HOST"):
        print("⚠️  Warning: PFSENSE_HOST not set. Using default: 192.168.1.1")
    
    if not os.getenv("PFSENSE_API_KEY") and not os.getenv("PFSENSE_USERNAME"):
        print("⚠️  Warning: No authentication credentials found.")
        print("   Set either PFSENSE_API_KEY or PFSENSE_USERNAME/PFSENSE_PASSWORD")
    
    # Test connection
    success = await test_pfsense_connection()
    
    if success:
        # Demonstrate features
        await demonstrate_system_management()
        await demonstrate_firewall_management()
        
        print("\n✅ All demonstrations completed successfully!")
    else:
        print("\n❌ Connection failed. Please check your configuration.")
        print("   Make sure to set the correct environment variables:")
        print("   - PFSENSE_HOST")
        print("   - PFSENSE_API_KEY (or PFSENSE_USERNAME/PFSENSE_PASSWORD)")


if __name__ == "__main__":
    asyncio.run(main())
