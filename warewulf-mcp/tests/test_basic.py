#!/usr/bin/env python3
"""
Basic tests for the Warewulf MCP Server.

These tests verify the core functionality without requiring
a live Warewulf server.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.validation import (
    validate_ip_address,
    validate_mac_address,
    validate_hostname,
    validate_port,
    validate_url,
    validate_node_config,
    validate_profile_config,
    validate_image_config,
    sanitize_config
)
from src.utils.logging import setup_logging


class TestValidation:
    """Test validation utilities."""
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        # Valid IP addresses
        assert validate_ip_address("192.168.1.1") == True
        assert validate_ip_address("10.0.0.1") == True
        assert validate_ip_address("172.16.0.1") == True
        assert validate_ip_address("::1") == True  # IPv6 localhost
        assert validate_ip_address("2001:db8::1") == True  # IPv6
        
        # Invalid IP addresses
        assert validate_ip_address("256.1.2.3") == False
        assert validate_ip_address("1.2.3.256") == False
        assert validate_ip_address("192.168.1") == False
        assert validate_ip_address("192.168.1.1.1") == False
        assert validate_ip_address("invalid") == False
        assert validate_ip_address("") == False
    
    def test_validate_mac_address(self):
        """Test MAC address validation."""
        # Valid MAC addresses
        assert validate_mac_address("00:11:22:33:44:55") == True
        assert validate_mac_address("00-11-22-33-44-55") == True
        assert validate_mac_address("001122334455") == True
        assert validate_mac_address("00:11:22:33:44:AA") == True
        
        # Invalid MAC addresses
        assert validate_mac_address("00:11:22:33:44") == False
        assert validate_mac_address("00:11:22:33:44:55:66") == False
        assert validate_mac_address("00:11:22:33:44:GG") == False
        assert validate_mac_address("invalid") == False
        assert validate_mac_address("") == False
    
    def test_validate_hostname(self):
        """Test hostname validation."""
        # Valid hostnames
        assert validate_hostname("localhost") == True
        assert validate_hostname("compute-01") == True
        assert validate_hostname("node.example.com") == True
        assert validate_hostname("test123") == True
        
        # Invalid hostnames
        assert validate_hostname("") == False
        assert validate_hostname("a" * 64) == False  # Too long label
        assert validate_hostname("." + "a" * 64 + ".example.com") == False
        assert validate_hostname("-invalid") == False  # Starts with dash
        assert validate_hostname("invalid-") == False  # Ends with dash
    
    def test_validate_port(self):
        """Test port validation."""
        # Valid ports
        assert validate_port(1) == True
        assert validate_port(80) == True
        assert validate_port(8080) == True
        assert validate_port(65535) == True
        assert validate_port("80") == True
        assert validate_port("8080") == True
        
        # Invalid ports
        assert validate_port(0) == False
        assert validate_port(65536) == False
        assert validate_port(-1) == False
        assert validate_port("invalid") == False
        assert validate_port("") == False
    
    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        assert validate_url("http://localhost:8080") == True
        assert validate_url("https://example.com") == True
        assert validate_url("http://192.168.1.1:9873") == True
        
        # Invalid URLs
        assert validate_url("not-a-url") == False
        assert validate_url("") == False
        assert validate_url("localhost:8080") == False  # Missing scheme
    
    def test_validate_node_config(self):
        """Test node configuration validation."""
        # Valid node config
        valid_config = {
            "node_name": "compute-01",
            "ipaddr": "192.168.1.101",
            "hwaddr": "00:11:22:33:44:55",
            "profile": "compute"
        }
        errors = validate_node_config(valid_config)
        assert len(errors) == 0
        
        # Invalid node config
        invalid_config = {
            "ipaddr": "invalid-ip",
            "hwaddr": "invalid-mac"
        }
        errors = validate_node_config(invalid_config)
        assert len(errors) > 0
        assert "Missing required field: node_name" in errors
        assert "Invalid IP address format" in errors
        assert "Invalid MAC address format" in errors
    
    def test_validate_profile_config(self):
        """Test profile configuration validation."""
        # Valid profile config
        valid_config = {
            "profile_name": "compute-profile"
        }
        errors = validate_profile_config(valid_config)
        assert len(errors) == 0
        
        # Invalid profile config
        invalid_config = {}
        errors = validate_profile_config(invalid_config)
        assert len(errors) > 0
        assert "Missing required field: profile_name" in errors
    
    def test_validate_image_config(self):
        """Test image configuration validation."""
        # Valid image config
        valid_config = {
            "image_name": "rocky9-compute"
        }
        errors = validate_image_config(valid_config)
        assert len(errors) == 0
        
        # Invalid image config
        invalid_config = {}
        errors = validate_image_config(invalid_config)
        assert len(errors) > 0
        assert "Missing required field: image_name" in errors
    
    def test_sanitize_config(self):
        """Test configuration sanitization."""
        config = {
            "host": "localhost",
            "username": "admin",
            "password": "secret123",
            "api_token": "token123",
            "secret_key": "key123"
        }
        
        sanitized = sanitize_config(config)
        
        # Sensitive fields should be redacted
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_token"] == "***REDACTED***"
        assert sanitized["secret_key"] == "***REDACTED***"
        
        # Non-sensitive fields should remain
        assert sanitized["host"] == "localhost"
        assert sanitized["username"] == "admin"


class TestLogging:
    """Test logging utilities."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        logger = setup_logging(level="INFO")
        assert logger is not None
        assert logger.level == 20  # INFO level
        
        # Test with different levels
        debug_logger = setup_logging(level="DEBUG")
        assert debug_logger.level == 10  # DEBUG level
        
        error_logger = setup_logging(level="ERROR")
        assert error_logger.level == 40  # ERROR level


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
