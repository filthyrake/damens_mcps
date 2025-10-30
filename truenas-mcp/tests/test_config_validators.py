"""Tests for TrueNAS config validators (Pydantic v2 migration)."""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import TrueNASConfig, ServerConfig, AuthConfig
from pydantic import ValidationError


class TestTrueNASConfigValidators:
    """Test TrueNAS configuration validators."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = TrueNASConfig(
            host="truenas.example.com",
            port=443,
            api_key="test-api-key"
        )
        assert config.host == "truenas.example.com"
        assert config.port == 443
    
    def test_empty_host_rejected(self):
        """Test that empty host is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrueNASConfig(host="", api_key="test-api-key")
        
        assert "Host cannot be empty" in str(exc_info.value)
    
    def test_invalid_port_too_low(self):
        """Test that port below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrueNASConfig(host="truenas.example.com", port=0, api_key="test")
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_invalid_port_too_high(self):
        """Test that port above 65535 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrueNASConfig(host="truenas.example.com", port=70000, api_key="test")
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_valid_port_range(self):
        """Test valid port range."""
        # Minimum valid port
        config1 = TrueNASConfig(host="test.com", port=1, api_key="test")
        assert config1.port == 1
        
        # Maximum valid port
        config2 = TrueNASConfig(host="test.com", port=65535, api_key="test")
        assert config2.port == 65535
        
        # Common port
        config3 = TrueNASConfig(host="test.com", port=8080, api_key="test")
        assert config3.port == 8080


class TestServerConfigValidators:
    """Test server configuration validators."""
    
    def test_valid_server_config(self):
        """Test valid server configuration."""
        config = ServerConfig(host="0.0.0.0", port=8000)
        assert config.host == "0.0.0.0"
        assert config.port == 8000
    
    def test_invalid_server_port_too_low(self):
        """Test that server port below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(host="0.0.0.0", port=-1)
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_invalid_server_port_too_high(self):
        """Test that server port above 65535 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(host="0.0.0.0", port=100000)
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_default_values(self):
        """Test default values."""
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.reload is False


class TestAuthConfigValidators:
    """Test authentication configuration validators."""
    
    def test_valid_auth_config(self):
        """Test valid auth configuration."""
        secret = "a" * 32  # 32 characters minimum
        config = AuthConfig(secret_key=secret)
        assert config.secret_key == secret
        assert config.algorithm == "HS256"
    
    def test_secret_key_too_short(self):
        """Test that short secret key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(secret_key="tooshort")
        
        assert "Secret key must be at least 32 characters long" in str(exc_info.value)
    
    def test_secret_key_exactly_32_chars(self):
        """Test that exactly 32 character secret key is accepted."""
        secret = "a" * 32
        config = AuthConfig(secret_key=secret)
        assert len(config.secret_key) == 32
    
    def test_secret_key_longer_than_32_chars(self):
        """Test that longer secret key is accepted."""
        secret = "a" * 64
        config = AuthConfig(secret_key=secret)
        assert len(config.secret_key) == 64


class TestPydanticV2Migration:
    """Test that Pydantic v2 features work correctly."""
    
    def test_field_validator_decorator_works(self):
        """Test that @field_validator decorator is functioning."""
        # This test verifies the migration to Pydantic v2 syntax
        # If validators weren't working, invalid values would pass through
        
        # Test host validation
        with pytest.raises(ValidationError):
            TrueNASConfig(host="", api_key="test")
        
        # Test port validation
        with pytest.raises(ValidationError):
            TrueNASConfig(host="test.com", port=0, api_key="test")
        
        # Test secret key validation
        with pytest.raises(ValidationError):
            AuthConfig(secret_key="short")
    
    def test_classmethod_decorator_present(self):
        """Test that validators have @classmethod decorator."""
        # In Pydantic v2, validators must be classmethods
        # This is automatically enforced by the @field_validator decorator
        # We verify by ensuring validation works as expected
        
        config = TrueNASConfig(host="test.com", port=443, api_key="test")
        assert config.host == "test.com"
        
        with pytest.raises(ValidationError):
            TrueNASConfig(host="", api_key="test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
