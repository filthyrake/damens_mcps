"""Tests for TrueNAS config validators (Pydantic v2 migration)."""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import TrueNASConfig, ServerConfig, AuthConfig, validate_secret_key_strength
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
    
    def test_valid_auth_config_with_strong_key(self):
        """Test valid auth configuration with strong key."""
        # Strong key with mixed characters (at least 32 chars)
        secret = "MyS3cureP@ssw0rd!WithMixedChars123"
        config = AuthConfig(secret_key=secret)
        assert config.secret_key == secret
        assert config.algorithm == "HS256"
    
    def test_secret_key_too_short(self):
        """Test that short secret key is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(secret_key="tooshort")
        
        assert "sufficient entropy" in str(exc_info.value)
    
    def test_secret_key_weak_all_lowercase(self):
        """Test that weak key with only lowercase is rejected."""
        weak_key = "a" * 32  # Only lowercase letters, no diversity
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(secret_key=weak_key)
        
        assert "sufficient entropy" in str(exc_info.value)
        assert "Generate with:" in str(exc_info.value)
    
    def test_secret_key_weak_all_zeros(self):
        """Test that weak key with all zeros is rejected."""
        weak_key = "0" * 32
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(secret_key=weak_key)
        
        assert "sufficient entropy" in str(exc_info.value)
    
    def test_secret_key_weak_repetitive(self):
        """Test that repetitive weak key is rejected."""
        weak_key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # 32 'a' characters
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(secret_key=weak_key)
        
        assert "sufficient entropy" in str(exc_info.value)


class TestSecretKeyEntropyValidation:
    """Test secret key entropy validation function."""
    
    def test_validate_secret_key_strength_function(self):
        """Test the validate_secret_key_strength helper function directly."""
        # Strong keys should pass (at least 32 characters)
        assert validate_secret_key_strength("MyS3cureP@ssw0rd!WithMixedChars123") is True
        assert validate_secret_key_strength("Abcd1234!@#$efgh5678%^&*IJKL9876") is True
        
        # Weak keys should fail
        assert validate_secret_key_strength("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") is False
        assert validate_secret_key_strength("00000000000000000000000000000000") is False
        assert validate_secret_key_strength("short") is False
    
    def test_weak_key_insufficient_diversity(self):
        """Test that keys with insufficient character diversity are rejected."""
        # Only lowercase and uppercase (2 types)
        weak_key = "abcdefghijklmnopqrstuvwxyzABCDE"
        assert validate_secret_key_strength(weak_key) is False
        
        # Only lowercase and digits (2 types)
        weak_key = "abcdefghijklmnopqrstuvw1234567"
        assert validate_secret_key_strength(weak_key) is False
    
    def test_weak_key_too_repetitive(self):
        """Test that keys with too much repetition are rejected."""
        # More than half the characters are the same
        weak_key = "aaaaaaaaaaaaaaaaaaBBBccccDDDD12!"
        assert validate_secret_key_strength(weak_key) is False
    
    def test_strong_key_with_three_types(self):
        """Test that keys with 3 character types are accepted."""
        # Lowercase, uppercase, and digits (3 types, at least 32 chars)
        strong_key = "AbCdEfGh1234567890IjKlMnOpQrStUv"
        assert validate_secret_key_strength(strong_key) is True
        
        # Lowercase, uppercase, and special (3 types, at least 32 chars)
        strong_key = "AbCdEfGh!@#$%^&*()IjKlMnOpQrStUv"
        assert validate_secret_key_strength(strong_key) is True
        
        # Lowercase, digits, and special (3 types, at least 32 chars)
        strong_key = "abcdefgh1234567890!@#$%^&*()xyzw"
        assert validate_secret_key_strength(strong_key) is True
    
    def test_strong_key_with_four_types(self):
        """Test that keys with all 4 character types are accepted."""
        strong_key = "Abc123!@#DefGhi456$%^JklMno789Xyz"
        assert validate_secret_key_strength(strong_key) is True
    
    def test_strong_key_generated_by_secrets(self):
        """Test that keys generated by secrets module pass validation."""
        import secrets
        generated_key = secrets.token_urlsafe(32)
        assert validate_secret_key_strength(generated_key) is True
    
    def test_config_with_strong_keys_accepted(self):
        """Test that AuthConfig accepts strong keys."""
        strong_keys = [
            "MyS3cureP@ssw0rd!WithMixedChars123",
            "Abcd1234!@#$efgh5678%^&*IJKL9876",
            "P@ssw0rd123!SecureKeyHere$456Extra",
        ]
        
        for key in strong_keys:
            config = AuthConfig(secret_key=key)
            assert config.secret_key == key
    
    def test_config_with_weak_keys_rejected(self):
        """Test that AuthConfig rejects weak keys."""
        weak_keys = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # All same character
            "00000000000000000000000000000000",  # All zeros
            "abcdefghijklmnopqrstuvwxyzabcde",  # Only lowercase
            "12345678901234567890123456789012",  # Only digits
            "abcdefghijklmnopqrstuvwx12345678",  # Only 2 types
        ]
        
        for key in weak_keys:
            with pytest.raises(ValidationError) as exc_info:
                AuthConfig(secret_key=key)
            assert "sufficient entropy" in str(exc_info.value)


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
        
        # Test secret key validation (should fail due to insufficient entropy)
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
        
        # Test that strong secret keys work (at least 32 chars)
        strong_key = "MyS3cureP@ssw0rd!WithMixedChars123"
        config = AuthConfig(secret_key=strong_key)
        assert config.secret_key == strong_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
