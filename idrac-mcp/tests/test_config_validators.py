"""Tests for iDRAC validation models (Pydantic v2 migration)."""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'))

from validation import IDracConfig, PowerOperation, UserConfig
from pydantic import ValidationError


class TestIDracConfigValidators:
    """Test iDRAC configuration validators."""
    
    def test_valid_idrac_config(self):
        """Test valid iDRAC configuration."""
        config = IDracConfig(
            host="idrac.example.com",
            port=443,
            protocol="https",
            username="admin",
            password="password123"
        )
        assert config.host == "idrac.example.com"
        assert config.port == 443
        assert config.protocol == "https"
    
    def test_invalid_host_with_special_chars(self):
        """Test that host with special characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IDracConfig(
                host="idrac@host!",
                username="admin",
                password="password123"
            )
        
        assert "alphanumeric characters, hyphens, and dots" in str(exc_info.value)
    
    def test_valid_host_formats(self):
        """Test various valid host formats."""
        valid_hosts = [
            "idrac",
            "idrac-1",
            "idrac.example.com",
            "192.168.1.100",
            "idrac-server-01.local",
        ]
        
        for host in valid_hosts:
            config = IDracConfig(host=host, username="admin", password="password123")
            assert config.host == host
    
    def test_invalid_port_too_low(self):
        """Test that port below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IDracConfig(
                host="idrac.example.com",
                port=0,
                username="admin",
                password="password123"
            )
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_invalid_port_too_high(self):
        """Test that port above 65535 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IDracConfig(
                host="idrac.example.com",
                port=70000,
                username="admin",
                password="password123"
            )
        
        assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_valid_port_range(self):
        """Test valid port range."""
        for port in [1, 443, 8080, 65535]:
            config = IDracConfig(
                host="idrac.example.com",
                port=port,
                username="admin",
                password="password123"
            )
            assert config.port == port
    
    def test_invalid_protocol(self):
        """Test that invalid protocol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IDracConfig(
                host="idrac.example.com",
                protocol="ftp",
                username="admin",
                password="password123"
            )
        
        assert "Protocol must be either http or https" in str(exc_info.value)
    
    def test_valid_protocols(self):
        """Test valid protocols."""
        for protocol in ["http", "https"]:
            config = IDracConfig(
                host="idrac.example.com",
                protocol=protocol,
                username="admin",
                password="password123"
            )
            assert config.protocol == protocol


class TestPowerOperationValidators:
    """Test power operation validators."""
    
    def test_valid_power_operation(self):
        """Test valid power operation."""
        config = PowerOperation(
            operation="on",
            force=False,
            timeout=60
        )
        assert config.operation == "on"
        assert config.force is False
        assert config.timeout == 60
    
    def test_invalid_operation(self):
        """Test that invalid operation is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PowerOperation(operation="restart")
        
        assert "Operation must be one of" in str(exc_info.value)
    
    def test_valid_operations(self):
        """Test all valid operations."""
        valid_operations = ['on', 'off', 'cycle', 'graceful_shutdown', 'force_off']
        
        for operation in valid_operations:
            config = PowerOperation(operation=operation)
            assert config.operation == operation
    
    def test_invalid_timeout_too_low(self):
        """Test that timeout below 10 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PowerOperation(operation="on", timeout=5)
        
        assert "Timeout must be between 10 and 300 seconds" in str(exc_info.value)
    
    def test_invalid_timeout_too_high(self):
        """Test that timeout above 300 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PowerOperation(operation="on", timeout=500)
        
        assert "Timeout must be between 10 and 300 seconds" in str(exc_info.value)
    
    def test_valid_timeout_range(self):
        """Test valid timeout range."""
        for timeout in [10, 30, 60, 120, 300]:
            config = PowerOperation(operation="on", timeout=timeout)
            assert config.timeout == timeout


class TestUserConfigValidators:
    """Test user configuration validators."""
    
    def test_valid_user_config(self):
        """Test valid user configuration."""
        config = UserConfig(
            username="testuser",
            password="password123",
            privilege="Administrator"
        )
        assert config.username == "testuser"
        assert config.password == "password123"
        assert config.privilege == "Administrator"
    
    def test_invalid_username_with_special_chars(self):
        """Test that username with special characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(
                username="test@user!",
                password="password123"
            )
        
        assert "alphanumeric characters, hyphens, and underscores" in str(exc_info.value)
    
    def test_invalid_username_too_short(self):
        """Test that username shorter than 3 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(
                username="ab",
                password="password123"
            )
        
        assert "Username must be between 3 and 16 characters" in str(exc_info.value)
    
    def test_invalid_username_too_long(self):
        """Test that username longer than 16 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(
                username="a" * 17,
                password="password123"
            )
        
        assert "Username must be between 3 and 16 characters" in str(exc_info.value)
    
    def test_valid_username_formats(self):
        """Test various valid username formats."""
        valid_usernames = [
            "abc",  # Minimum length
            "admin",
            "test-user",
            "test_user",
            "USER123",
            "a" * 16,  # Maximum length
        ]
        
        for username in valid_usernames:
            config = UserConfig(username=username, password="password123")
            assert config.username == username
    
    def test_invalid_password_too_short(self):
        """Test that password shorter than 8 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(
                username="testuser",
                password="short"
            )
        
        assert "Password must be at least 8 characters long" in str(exc_info.value)
    
    def test_valid_password_lengths(self):
        """Test valid password lengths."""
        for length in [8, 12, 16, 32]:
            password = "a" * length
            config = UserConfig(username="testuser", password=password)
            assert len(config.password) == length
    
    def test_invalid_privilege(self):
        """Test that invalid privilege is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(
                username="testuser",
                password="password123",
                privilege="SuperUser"
            )
        
        assert "Privilege must be one of" in str(exc_info.value)
    
    def test_valid_privileges(self):
        """Test all valid privileges."""
        valid_privileges = ['Administrator', 'Operator', 'ReadOnly']
        
        for privilege in valid_privileges:
            config = UserConfig(
                username="testuser",
                password="password123",
                privilege=privilege
            )
            assert config.privilege == privilege


class TestPydanticV2Migration:
    """Test that Pydantic v2 features work correctly."""
    
    def test_field_validator_decorator_works_idrac(self):
        """Test that @field_validator decorator is functioning for iDRAC config."""
        # Test host validation
        with pytest.raises(ValidationError):
            IDracConfig(host="invalid@host", username="admin", password="password123")
        
        # Test port validation
        with pytest.raises(ValidationError):
            IDracConfig(host="idrac", port=0, username="admin", password="password123")
        
        # Test protocol validation
        with pytest.raises(ValidationError):
            IDracConfig(host="idrac", protocol="ftp", username="admin", password="password123")
    
    def test_field_validator_decorator_works_power_operation(self):
        """Test that @field_validator decorator is functioning for PowerOperation."""
        # Test operation validation
        with pytest.raises(ValidationError):
            PowerOperation(operation="restart")
        
        # Test timeout validation
        with pytest.raises(ValidationError):
            PowerOperation(operation="on", timeout=5)
    
    def test_field_validator_decorator_works_user_config(self):
        """Test that @field_validator decorator is functioning for UserConfig."""
        # Test username validation
        with pytest.raises(ValidationError):
            UserConfig(username="a", password="password123")
        
        # Test password validation
        with pytest.raises(ValidationError):
            UserConfig(username="testuser", password="short")
        
        # Test privilege validation
        with pytest.raises(ValidationError):
            UserConfig(username="testuser", password="password123", privilege="Invalid")
    
    def test_classmethod_decorator_present(self):
        """Test that validators have @classmethod decorator."""
        # In Pydantic v2, validators must be classmethods
        # This is automatically enforced by the @field_validator decorator
        # We verify by ensuring validation works as expected
        
        config = IDracConfig(host="idrac", username="admin", password="password123")
        assert config.host == "idrac"
        
        with pytest.raises(ValidationError):
            IDracConfig(host="", username="admin", password="password123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
