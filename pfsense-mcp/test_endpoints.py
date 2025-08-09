#!/usr/bin/env python3
"""
Test script to discover working pfSense 2.8.0 API endpoints.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from pfsense_client import HTTPPfSenseClient

async def test_endpoints():
    """Test various pfSense API endpoints to see which ones work."""
    
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
    
    print(f"Testing pfSense API endpoints on {config['host']}:{config['port']}")
    print("=" * 60)
    
    client = HTTPPfSenseClient(config)
    
    # List of endpoints to test
    endpoints_to_test = [
        # System endpoints
        ("GET", "/api/v2/diagnostics/system", "System Diagnostics"),
        ("GET", "/api/v2/system/status", "System Status"),
        ("GET", "/api/v2/system/info", "System Info"),
        ("GET", "/api/v2/system/version", "System Version"),
        
        # Health endpoints
        ("GET", "/api/v2/diagnostics/health", "System Health"),
        ("GET", "/api/v2/system/health", "System Health Alt"),
        
        # ARP table (we know this works)
        ("GET", "/api/v2/diagnostics/arp_table", "ARP Table"),
        
        # Interface endpoints
        ("GET", "/api/v2/interfaces", "Interfaces"),
        ("GET", "/api/v2/diagnostics/interfaces", "Interfaces Diagnostics"),
        
        # Service endpoints
        ("GET", "/api/v2/services", "Services"),
        ("GET", "/api/v2/system/services", "System Services"),
        
        # Firewall endpoints
        ("GET", "/api/v2/firewall/rules", "Firewall Rules"),
        ("GET", "/api/v2/firewall", "Firewall Config"),
        
        # DHCP endpoints
        ("GET", "/api/v2/dhcp/leases", "DHCP Leases"),
        ("GET", "/api/v2/dhcp/status", "DHCP Status"),
        
        # VPN endpoints
        ("GET", "/api/v2/vpn/status", "VPN Status"),
        ("GET", "/api/v2/vpn/connections", "VPN Connections"),
        
        # Auth endpoints
        ("GET", "/api/v2/auth/keys", "Auth Keys"),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for method, endpoint, description in endpoints_to_test:
        try:
            print(f"Testing {method} {endpoint} ({description})...", end=" ")
            result = await client._make_request(method, endpoint)
            print("✅ WORKING")
            working_endpoints.append((method, endpoint, description))
            print(f"   Response: {str(result)[:100]}...")
        except Exception as e:
            print("❌ FAILED")
            failed_endpoints.append((method, endpoint, description, str(e)))
            print(f"   Error: {str(e)[:100]}...")
        print()
    
    print("=" * 60)
    print("SUMMARY:")
    print(f"Working endpoints: {len(working_endpoints)}")
    print(f"Failed endpoints: {len(failed_endpoints)}")
    
    if working_endpoints:
        print("\n✅ WORKING ENDPOINTS:")
        for method, endpoint, description in working_endpoints:
            print(f"  {method} {endpoint} - {description}")
    
    if failed_endpoints:
        print("\n❌ FAILED ENDPOINTS:")
        for method, endpoint, description, error in failed_endpoints:
            print(f"  {method} {endpoint} - {description}")
            print(f"    Error: {error}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
