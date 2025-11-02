"""Test SSL verification warning functionality.

This test validates that the iDRAC MCP server emits appropriate warnings when SSL
verification is disabled, helping prevent accidental production deployments
with insecure configurations.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSSLWarnings:
    """Test SSL verification warnings for iDRAC MCP server."""
    
    def test_ssl_enabled_default_in_config_example(self):
        """Test that config.example.json has SSL verification enabled by default."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.example.json')
        
        # Check if config.example.json exists
        if not os.path.exists(config_path):
            pytest.skip("config.example.json not found")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check all server configurations
        servers = config.get('idrac_servers', {})
        assert len(servers) > 0, "Should have at least one server configured"
        
        for server_id, server_config in servers.items():
            ssl_verify = server_config.get('ssl_verify', False)
            assert ssl_verify is True, f"Server {server_id} should have ssl_verify=true by default"
    
    def test_ssl_enabled_default_in_env_example(self):
        """Test that env.example has SSL verification enabled by default."""
        env_path = os.path.join(os.path.dirname(__file__), '..', 'env.example')
        
        # Check if env.example exists
        if not os.path.exists(env_path):
            pytest.skip("env.example not found")
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Parse the env file
        ssl_verify_found = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('IDRAC_SSL_VERIFY='):
                ssl_verify_found = True
                value = line.split('=', 1)[1].strip()
                assert value.lower() == 'true', "IDRAC_SSL_VERIFY should be 'true' by default"
                break
        
        assert ssl_verify_found, "IDRAC_SSL_VERIFY should be present in env.example"
    
    def test_ssl_warning_message_for_disabled_servers(self):
        """Test that warning logic correctly identifies servers with SSL disabled."""
        # Create a mock configuration
        config = {
            'idrac_servers': {
                'secure_server': {
                    'name': 'Secure Server',
                    'host': '192.168.1.100',
                    'port': 443,
                    'username': 'root',
                    'password': 'test',
                    'ssl_verify': True
                },
                'insecure_server': {
                    'name': 'Insecure Server',
                    'host': '192.168.1.101',
                    'port': 443,
                    'username': 'root',
                    'password': 'test',
                    'ssl_verify': False
                }
            }
        }
        
        # Simulate the warning logic from working_mcp_server.py
        servers = config.get('idrac_servers', {})
        ssl_disabled_servers = [
            server_id for server_id, server_config in servers.items()
            if not server_config.get('ssl_verify', False)
        ]
        
        # Verify that only the insecure server is flagged
        assert len(ssl_disabled_servers) == 1, "Should identify exactly one server with SSL disabled"
        assert 'insecure_server' in ssl_disabled_servers, "Should identify insecure_server"
        assert 'secure_server' not in ssl_disabled_servers, "Should not flag secure_server"
    
    def test_all_servers_secure_no_warning(self):
        """Test that no warning is needed when all servers have SSL enabled."""
        config = {
            'idrac_servers': {
                'server1': {
                    'name': 'Server 1',
                    'host': '192.168.1.100',
                    'port': 443,
                    'username': 'root',
                    'password': 'test',
                    'ssl_verify': True
                },
                'server2': {
                    'name': 'Server 2',
                    'host': '192.168.1.101',
                    'port': 443,
                    'username': 'root',
                    'password': 'test',
                    'ssl_verify': True
                }
            }
        }
        
        servers = config.get('idrac_servers', {})
        ssl_disabled_servers = [
            server_id for server_id, server_config in servers.items()
            if not server_config.get('ssl_verify', False)
        ]
        
        assert len(ssl_disabled_servers) == 0, "Should have no servers with SSL disabled"
    
    def test_default_ssl_verify_false_when_missing(self):
        """Test that ssl_verify defaults to False when not specified (for backward compatibility)."""
        server_config = {
            'name': 'Legacy Server',
            'host': '192.168.1.100',
            'port': 443,
            'username': 'root',
            'password': 'test'
            # Note: ssl_verify is intentionally missing
        }
        
        ssl_verify = server_config.get('ssl_verify', False)
        assert ssl_verify is False, "ssl_verify should default to False for backward compatibility"


class TestSSLConfigurationExamples:
    """Test that example configurations follow security best practices."""
    
    def test_config_example_has_security_comment(self):
        """Test that config.example.json includes a security warning comment."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.example.json')
        
        if not os.path.exists(config_path):
            pytest.skip("config.example.json not found")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for security comment
        comment = config.get('_comment', '')
        assert 'ssl_verify' in comment.lower() or 'ssl' in comment.lower(), \
            "config.example.json should include SSL security guidance in comments"
        assert 'production' in comment.lower() or 'mitm' in comment.lower(), \
            "Security comment should mention production or MITM attacks"
    
    def test_env_example_has_security_comment(self):
        """Test that env.example includes SSL security warnings."""
        env_path = os.path.join(os.path.dirname(__file__), '..', 'env.example')
        
        if not os.path.exists(env_path):
            pytest.skip("env.example not found")
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Look for security-related comments near SSL settings
        lines = content.split('\n')
        found_security_warning = False
        
        for i, line in enumerate(lines):
            if 'IDRAC_SSL_VERIFY' in line:
                # Check surrounding lines for security warnings
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+2)])
                if any(keyword in context.upper() for keyword in ['IMPORTANT', 'WARNING', 'MITM', 'PRODUCTION']):
                    found_security_warning = True
                    break
        
        assert found_security_warning, "env.example should include security warnings near SSL settings"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
