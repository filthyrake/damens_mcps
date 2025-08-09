#!/usr/bin/env python3
"""
Discover all available pfSense 2.8.0 API endpoints.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from auth import PfSenseAuth

async def discover_endpoints():
    """Discover all available pfSense API endpoints."""
    
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
    
    print(f"Discovering pfSense API endpoints on {config['host']}:{config['port']}")
    print("=" * 60)
    
    auth = PfSenseAuth(config)
    session = await auth.create_session()
    
    # Comprehensive list of potential endpoints to test
    endpoints_to_test = [
        # System endpoints
        ("GET", "/api/v2/system/version", "System Version"),
        ("GET", "/api/v2/system/status", "System Status"),
        ("GET", "/api/v2/system/info", "System Info"),
        ("GET", "/api/v2/system/health", "System Health"),
        ("GET", "/api/v2/system/services", "System Services"),
        ("GET", "/api/v2/system/logs", "System Logs"),
        ("GET", "/api/v2/system/backup", "System Backup"),
        ("GET", "/api/v2/system/restore", "System Restore"),
        
        # Diagnostics endpoints
        ("GET", "/api/v2/diagnostics/system", "System Diagnostics"),
        ("GET", "/api/v2/diagnostics/health", "Health Diagnostics"),
        ("GET", "/api/v2/diagnostics/arp_table", "ARP Table"),
        ("GET", "/api/v2/diagnostics/interfaces", "Interface Diagnostics"),
        ("GET", "/api/v2/diagnostics/routing", "Routing Diagnostics"),
        ("GET", "/api/v2/diagnostics/dns", "DNS Diagnostics"),
        ("GET", "/api/v2/diagnostics/ntp", "NTP Diagnostics"),
        
        # Interface endpoints
        ("GET", "/api/v2/interfaces", "Interfaces"),
        ("GET", "/api/v2/interfaces/wan", "WAN Interface"),
        ("GET", "/api/v2/interfaces/lan", "LAN Interface"),
        ("GET", "/api/v2/interfaces/opt1", "OPT1 Interface"),
        ("GET", "/api/v2/interfaces/opt2", "OPT2 Interface"),
        
        # Firewall endpoints
        ("GET", "/api/v2/firewall", "Firewall Config"),
        ("GET", "/api/v2/firewall/rules", "Firewall Rules"),
        ("GET", "/api/v2/firewall/aliases", "Firewall Aliases"),
        ("GET", "/api/v2/firewall/nat", "Firewall NAT"),
        ("GET", "/api/v2/firewall/logs", "Firewall Logs"),
        
        # Service endpoints
        ("GET", "/api/v2/services", "Services"),
        ("GET", "/api/v2/services/dhcp", "DHCP Service"),
        ("GET", "/api/v2/services/dns", "DNS Service"),
        ("GET", "/api/v2/services/ntp", "NTP Service"),
        ("GET", "/api/v2/services/snmp", "SNMP Service"),
        
        # DHCP endpoints
        ("GET", "/api/v2/dhcp", "DHCP Config"),
        ("GET", "/api/v2/dhcp/leases", "DHCP Leases"),
        ("GET", "/api/v2/dhcp/status", "DHCP Status"),
        ("GET", "/api/v2/dhcp/static", "DHCP Static"),
        
        # VPN endpoints
        ("GET", "/api/v2/vpn", "VPN Config"),
        ("GET", "/api/v2/vpn/status", "VPN Status"),
        ("GET", "/api/v2/vpn/connections", "VPN Connections"),
        ("GET", "/api/v2/vpn/openvpn", "OpenVPN"),
        ("GET", "/api/v2/vpn/ipsec", "IPSec"),
        
        # Auth endpoints
        ("GET", "/api/v2/auth/keys", "Auth Keys"),
        ("GET", "/api/v2/auth/users", "Auth Users"),
        ("GET", "/api/v2/auth/groups", "Auth Groups"),
        
        # Package endpoints
        ("GET", "/api/v2/packages", "Packages"),
        ("GET", "/api/v2/packages/installed", "Installed Packages"),
        ("GET", "/api/v2/packages/available", "Available Packages"),
        
        # Status endpoints
        ("GET", "/api/v2/status", "Status"),
        ("GET", "/api/v2/status/system", "System Status"),
        ("GET", "/api/v2/status/interfaces", "Interface Status"),
        ("GET", "/api/v2/status/services", "Service Status"),
        
        # Configuration endpoints
        ("GET", "/api/v2/config", "Config"),
        ("GET", "/api/v2/config/system", "System Config"),
        ("GET", "/api/v2/config/interfaces", "Interface Config"),
        ("GET", "/api/v2/config/firewall", "Firewall Config"),
        
        # Try different HTTP methods
        ("POST", "/api/v2/system/restart", "System Restart"),
        ("POST", "/api/v2/system/reboot", "System Reboot"),
        ("POST", "/api/v2/services/restart", "Restart Services"),
        
        # Try some common variations
        ("GET", "/api/v2/system", "System Root"),
        ("GET", "/api/v2/diagnostics", "Diagnostics Root"),
        ("GET", "/api/v2/firewall/rules", "Firewall Rules"),
        ("GET", "/api/v2/firewall/rule", "Firewall Rule (singular)"),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for method, endpoint, description in endpoints_to_test:
        try:
            print(f"Testing {method} {endpoint} ({description})...", end=" ")
            
            # Use X-API-Key header (we know this works)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-Key": config['api_key']
            }
            
            url = f"{auth.get_base_url()}{endpoint}"
            
            if method == "GET":
                async with session.get(url, headers=headers, allow_redirects=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ WORKING")
                        working_endpoints.append((method, endpoint, description, result))
                        print(f"   Response: {str(result)[:100]}...")
                    else:
                        print("❌ FAILED")
                        failed_endpoints.append((method, endpoint, description, f"Status {response.status}"))
            elif method == "POST":
                async with session.post(url, headers=headers, allow_redirects=False) as response:
                    if response.status in [200, 201, 202]:
                        result = await response.json()
                        print("✅ WORKING")
                        working_endpoints.append((method, endpoint, description, result))
                        print(f"   Response: {str(result)[:100]}...")
                    else:
                        print("❌ FAILED")
                        failed_endpoints.append((method, endpoint, description, f"Status {response.status}"))
                        
        except Exception as e:
            print("❌ FAILED")
            failed_endpoints.append((method, endpoint, description, str(e)))
        
        print()
    
    print("=" * 60)
    print("SUMMARY:")
    print(f"Working endpoints: {len(working_endpoints)}")
    print(f"Failed endpoints: {len(failed_endpoints)}")
    
    if working_endpoints:
        print("\n✅ WORKING ENDPOINTS:")
        for method, endpoint, description, result in working_endpoints:
            print(f"  {method} {endpoint} - {description}")
            if isinstance(result, dict) and 'data' in result:
                data_type = type(result['data']).__name__
                if isinstance(result['data'], list):
                    print(f"    Returns: List with {len(result['data'])} items")
                else:
                    print(f"    Returns: {data_type}")
    
    await session.close()

if __name__ == "__main__":
    asyncio.run(discover_endpoints())
