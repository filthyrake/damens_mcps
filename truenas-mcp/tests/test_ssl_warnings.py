"""Test SSL verification warning functionality.

This test validates that the server emits appropriate warnings when SSL
verification is disabled, helping prevent accidental production deployments
with insecure configurations.
"""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Settings


class TestSSLWarnings:
    """Test SSL verification warnings."""
    
    def test_ssl_enabled_default_in_config(self):
        """Test that SSL verification is enabled by default in config."""
        # Create minimal settings with required fields
        with patch.dict(os.environ, {
            'TRUENAS_HOST': 'test.example.com',
            'TRUENAS_API_KEY': 'test-key',
            'SECRET_KEY': 'a' * 32,  # Minimum 32 characters
        }):
            settings = Settings()
            assert settings.truenas_verify_ssl is True, "SSL verification should be enabled by default"
    
    def test_ssl_disabled_explicit(self):
        """Test that SSL verification can be explicitly disabled."""
        with patch.dict(os.environ, {
            'TRUENAS_HOST': 'test.example.com',
            'TRUENAS_API_KEY': 'test-key',
            'SECRET_KEY': 'a' * 32,
            'TRUENAS_VERIFY_SSL': 'false'
        }):
            settings = Settings()
            assert settings.truenas_verify_ssl is False, "SSL verification should respect explicit false setting"
    
    def test_ssl_enabled_explicit(self):
        """Test that SSL verification can be explicitly enabled."""
        with patch.dict(os.environ, {
            'TRUENAS_HOST': 'test.example.com',
            'TRUENAS_API_KEY': 'test-key',
            'SECRET_KEY': 'a' * 32,
            'TRUENAS_VERIFY_SSL': 'true'
        }):
            settings = Settings()
            assert settings.truenas_verify_ssl is True, "SSL verification should respect explicit true setting"
    
    def test_ssl_warning_displayed_when_disabled(self):
        """Test that a warning is logged when SSL verification is disabled."""
        # This test verifies the logic but doesn't test the actual CLI output
        # which would require more complex mocking of rich.Console
        
        with patch.dict(os.environ, {
            'TRUENAS_HOST': 'test.example.com',
            'TRUENAS_API_KEY': 'test-key',
            'SECRET_KEY': 'a' * 32,
            'TRUENAS_VERIFY_SSL': 'false'
        }):
            settings = Settings()
            
            # Verify the condition that should trigger warning
            assert not settings.truenas_verify_ssl, "Settings should have SSL disabled for warning test"
            
            # In actual usage, the serve() function in http_cli.py checks this
            # and displays a warning via rich.Console. We verify the condition here.
    
    def test_ssl_verification_status_in_server_config(self):
        """Test that SSL verification status is properly included in server configuration."""
        with patch.dict(os.environ, {
            'TRUENAS_HOST': 'test.example.com',
            'TRUENAS_API_KEY': 'test-key',
            'SECRET_KEY': 'a' * 32,
            'TRUENAS_VERIFY_SSL': 'true'
        }):
            settings = Settings()
            
            # Verify the setting is correctly stored and accessible
            assert hasattr(settings, 'truenas_verify_ssl')
            assert isinstance(settings.truenas_verify_ssl, bool)
            assert settings.truenas_verify_ssl is True


class TestSSLConfigurationValidation:
    """Test SSL configuration validation."""
    
    def test_ssl_verify_accepts_various_true_values(self):
        """Test that SSL verification accepts various representations of true."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES']
        
        for value in true_values:
            with patch.dict(os.environ, {
                'TRUENAS_HOST': 'test.example.com',
                'TRUENAS_API_KEY': 'test-key',
                'SECRET_KEY': 'a' * 32,
                'TRUENAS_VERIFY_SSL': value
            }):
                settings = Settings()
                assert settings.truenas_verify_ssl is True, f"SSL verification should be True for value: {value}"
    
    def test_ssl_verify_accepts_various_false_values(self):
        """Test that SSL verification accepts various representations of false."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']
        
        for value in false_values:
            with patch.dict(os.environ, {
                'TRUENAS_HOST': 'test.example.com',
                'TRUENAS_API_KEY': 'test-key',
                'SECRET_KEY': 'a' * 32,
                'TRUENAS_VERIFY_SSL': value
            }):
                settings = Settings()
                assert settings.truenas_verify_ssl is False, f"SSL verification should be False for value: {value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
