#!/usr/bin/env python3
"""
Standalone test to verify ProxmoxClient initialization pattern.

This test verifies that the client can be initialized from a config dictionary
using the pattern shown in examples/basic_usage.py.
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the resilience module to avoid logger issues
sys.modules['src.utils.resilience'] = MagicMock()
sys.modules['src.utils.resilience'].create_circuit_breaker = MagicMock(return_value=None)
sys.modules['src.utils.resilience'].create_retry_decorator = MagicMock(return_value=lambda f: f)

from src.proxmox_client import ProxmoxClient


def test_client_initialization_from_config():
    """Test that client can be initialized from config dict as shown in basic_usage.py."""
    
    # Simulated config dictionary (as loaded from config.json)
    config = {
        'host': '192.168.1.100',
        'port': 8006,
        'protocol': 'https',
        'username': 'root',
        'password': 'testpassword',
        'realm': 'pam',
        'ssl_verify': False
    }
    
    print("Testing ProxmoxClient initialization from config dict...")
    
    # Mock the authentication to avoid actual API calls
    with patch.object(ProxmoxClient, '_authenticate'):
        # This pattern matches what's in basic_usage.py
        client = ProxmoxClient(
            host=config['host'],
            port=config['port'],
            protocol=config['protocol'],
            username=config['username'],
            password=config['password'],
            realm=config.get('realm', 'pve'),
            ssl_verify=config.get('ssl_verify', False)
        )
        
        # Verify the client was initialized correctly
        assert client is not None, "Client should not be None"
        assert client.host == '192.168.1.100', f"Expected host 192.168.1.100, got {client.host}"
        assert client.port == 8006, f"Expected port 8006, got {client.port}"
        assert client.protocol == 'https', f"Expected protocol https, got {client.protocol}"
        assert client.username == 'root', f"Expected username root, got {client.username}"
        assert client.realm == 'pam', f"Expected realm pam, got {client.realm}"
        assert client.ssl_verify == False, f"Expected ssl_verify False, got {client.ssl_verify}"
        
        print("✅ All assertions passed!")
        return True


def test_client_initialization_with_defaults():
    """Test that client can be initialized with default values from .get()."""
    
    # Config with minimal required fields (realm and ssl_verify use defaults)
    config = {
        'host': '192.168.1.101',
        'port': 8006,
        'protocol': 'https',
        'username': 'admin',
        'password': 'secret123'
    }
    
    print("\nTesting ProxmoxClient initialization with default values...")
    
    with patch.object(ProxmoxClient, '_authenticate'):
        client = ProxmoxClient(
            host=config['host'],
            port=config['port'],
            protocol=config['protocol'],
            username=config['username'],
            password=config['password'],
            realm=config.get('realm', 'pve'),  # Should default to 'pve'
            ssl_verify=config.get('ssl_verify', False)  # Should default to False
        )
        
        assert client.realm == 'pve', f"Expected default realm pve, got {client.realm}"
        assert client.ssl_verify == False, f"Expected default ssl_verify False, got {client.ssl_verify}"
        
        print("✅ Default values work correctly!")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("ProxmoxClient Initialization Tests")
    print("=" * 60)
    
    try:
        test_client_initialization_from_config()
        test_client_initialization_with_defaults()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
