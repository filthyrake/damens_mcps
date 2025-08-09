"""Basic tests for iDRAC MCP Server."""

import pytest
import os
from unittest.mock import Mock, patch

from src.idrac_client import IDracClient
from src.auth import AuthManager
from src.utils.validation import validate_idrac_config, validate_power_operation, validate_user_config


class TestIDracClient:
    """Test iDRAC client functionality."""
    
    def test_client_initialization(self):
        """Test client initialization with valid config."""
        config = {
            "host": "192.168.1.100",  # Test IP - change in production
            "port": 443,
            "protocol": "https",
            "username": "root",
            "password": "password",
            "ssl_verify": False
        }
        
        client = IDracClient(config)
        assert client.config["host"] == "192.168.1.100"
        assert client.config["port"] == 443
        assert client.config["protocol"] == "https"
    
    def test_client_invalid_config(self):
        """Test client initialization with invalid config."""
        config = {
            "host": "invalid-host!",
            "port": 99999,  # Invalid port
            "protocol": "ftp",  # Invalid protocol
            "username": "root",
            "password": "password"
        }
        
        with pytest.raises(ValueError):
            IDracClient(config)


class TestAuthManager:
    """Test authentication manager functionality."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        config = {"secret_key": "test-secret-key"}
        auth_manager = AuthManager(config)
        
        password = "test-password"
        hashed = auth_manager.get_password_hash(password)
        
        assert hashed != password
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("wrong-password", hashed) is False
    
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        config = {"secret_key": "test-secret-key"}
        auth_manager = AuthManager(config)
        
        token_data = {"sub": "test-user", "type": "user"}
        token = auth_manager.create_access_token(token_data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user"
        assert payload["type"] == "user"
    
    def test_invalid_token_verification(self):
        """Test invalid token verification."""
        config = {"secret_key": "test-secret-key"}
        auth_manager = AuthManager(config)
        
        # Test with invalid token
        payload = auth_manager.verify_token("invalid-token")
        assert payload is None


class TestValidation:
    """Test validation utilities."""
    
    def test_validate_idrac_config(self):
        """Test iDRAC configuration validation."""
        valid_config = {
            "host": "192.168.1.100",  # Test IP - change in production
            "port": 443,
            "protocol": "https",
            "username": "root",
            "password": "password"
        }
        
        result = validate_idrac_config(valid_config)
        assert result["host"] == "192.168.1.100"
        assert result["port"] == 443
    
    def test_validate_idrac_config_invalid(self):
        """Test iDRAC configuration validation with invalid data."""
        invalid_config = {
            "host": "invalid-host!",
            "port": 99999,
            "protocol": "ftp",
            "username": "root",
            "password": "password"
        }
        
        with pytest.raises(ValueError):
            validate_idrac_config(invalid_config)
    
    def test_validate_power_operation(self):
        """Test power operation validation."""
        valid_operation = {
            "operation": "on",
            "force": False,
            "timeout": 60
        }
        
        result = validate_power_operation(valid_operation)
        assert result["operation"] == "on"
        assert result["force"] is False
    
    def test_validate_power_operation_invalid(self):
        """Test power operation validation with invalid data."""
        invalid_operation = {
            "operation": "invalid-operation",
            "timeout": 999
        }
        
        with pytest.raises(ValueError):
            validate_power_operation(invalid_operation)
    
    def test_validate_user_config(self):
        """Test user configuration validation."""
        valid_user = {
            "username": "testuser",
            "password": "securepassword123",
            "privilege": "Administrator",
            "enabled": True
        }
        
        result = validate_user_config(valid_user)
        assert result["username"] == "testuser"
        assert result["privilege"] == "Administrator"
    
    def test_validate_user_config_invalid(self):
        """Test user configuration validation with invalid data."""
        invalid_user = {
            "username": "a",  # Too short
            "password": "123",  # Too short
            "privilege": "InvalidPrivilege"
        }
        
        with pytest.raises(ValueError):
            validate_user_config(invalid_user)


if __name__ == "__main__":
    pytest.main([__file__])
