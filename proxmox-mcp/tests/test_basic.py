"""Basic tests for Proxmox MCP Server."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.proxmox_client import ProxmoxClient
from src.auth import AuthManager
from src.utils.validation import validate_vm_config, validate_container_config


class TestProxmoxClient:
    """Test Proxmox client functionality."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        config = {
            "host": "test.example.com",
            "port": 8006,
            "username": "testuser",
            "password": "testpass",
            "realm": "pve"
        }
        
        with patch('src.proxmox_client.ProxmoxAPI'):
            client = ProxmoxClient(config)
            assert client.host == "test.example.com"
            assert client.port == 8006
            assert client.username == "testuser"
            assert client.password == "testpass"
            assert client.realm == "pve"


class TestAuthManager:
    """Test authentication manager functionality."""
    
    def test_auth_manager_initialization(self):
        """Test auth manager initialization."""
        config = {
            "secret_key": "test-secret-key"
        }
        
        auth_manager = AuthManager(config)
        assert auth_manager.secret_key == "test-secret-key"
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        config = {"secret_key": "test-secret-key"}
        auth_manager = AuthManager(config)
        
        password = "testpassword"
        hashed = auth_manager.get_password_hash(password)
        
        assert hashed != password
        assert auth_manager.verify_password(password, hashed)
        assert not auth_manager.verify_password("wrongpassword", hashed)
    
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        config = {"secret_key": "test-secret-key"}
        auth_manager = AuthManager(config)
        
        data = {"user": "testuser", "role": "admin"}
        token = auth_manager.create_access_token(data)
        
        # Verify token
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload["user"] == "testuser"
        assert payload["role"] == "admin"


class TestValidation:
    """Test input validation functionality."""
    
    def test_vm_config_validation(self):
        """Test VM configuration validation."""
        valid_config = {
            "name": "test-vm",
            "node": "pve",
            "cores": 2,
            "memory": 1024,
            "storage": "local-lvm",
            "disk_size": "20G"
        }
        
        result = validate_vm_config(valid_config)
        assert result["name"] == "test-vm"
        assert result["cores"] == 2
        assert result["memory"] == 1024
    
    def test_vm_config_validation_invalid_name(self):
        """Test VM configuration validation with invalid name."""
        invalid_config = {
            "name": "test vm with spaces",
            "node": "pve",
            "cores": 2,
            "memory": 1024
        }
        
        with pytest.raises(ValueError, match="VM name must contain only alphanumeric characters"):
            validate_vm_config(invalid_config)
    
    def test_container_config_validation(self):
        """Test container configuration validation."""
        valid_config = {
            "name": "test-container",
            "node": "pve",
            "ostemplate": "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz",
            "cores": 1,
            "memory": 512
        }
        
        result = validate_container_config(valid_config)
        assert result["name"] == "test-container"
        assert result["ostemplate"] == "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz"
    
    def test_container_config_validation_missing_ostemplate(self):
        """Test container configuration validation with missing ostemplate."""
        invalid_config = {
            "name": "test-container",
            "node": "pve",
            "cores": 1,
            "memory": 512
        }
        
        with pytest.raises(ValueError, match="OS template is required"):
            validate_container_config(invalid_config)


if __name__ == "__main__":
    pytest.main([__file__])
