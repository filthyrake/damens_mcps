"""Basic tests for TrueNAS MCP Server."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.auth import AuthManager
from src.truenas_client import TrueNASClient, TrueNASConfig
from src.resources.system import SystemResource
from src.resources.storage import StorageResource
from src.resources.network import NetworkResource
from src.resources.services import ServicesResource
from src.resources.users import UsersResource


class TestAuthManager:
    """Test authentication manager."""
    
    def test_auth_manager_init(self):
        """Test AuthManager initialization."""
        config = {
            "api_key": "test-key",
            "username": "test-user",
            "password": "test-pass"
        }
        
        auth_manager = AuthManager(config)
        assert auth_manager.config.api_key == "test-key"
        assert auth_manager.config.username == "test-user"
        assert auth_manager.config.password == "test-pass"
    
    def test_auth_method_detection(self):
        """Test authentication method detection."""
        # API key auth
        config = {"api_key": "test-key"}
        auth_manager = AuthManager(config)
        assert auth_manager.get_auth_method() == "api_key"
        
        # Username/password auth
        config = {"username": "user", "password": "pass"}
        auth_manager = AuthManager(config)
        assert auth_manager.get_auth_method() == "username_password"
        
        # No auth
        config = {}
        auth_manager = AuthManager(config)
        assert auth_manager.get_auth_method() == "none"


class TestTrueNASConfig:
    """Test TrueNAS configuration."""
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = {
            "host": "test.example.com",
            "port": 443,
            "api_key": "test-key"
        }
        
        truenas_config = TrueNASConfig(**config)
        assert truenas_config.host == "test.example.com"
        assert truenas_config.port == 443
        assert truenas_config.api_key == "test-key"
        assert truenas_config.base_url == "https://test.example.com:443/api/v2.0"
    
    def test_config_port_http(self):
        """Test HTTP port configuration."""
        config = {
            "host": "test.example.com",
            "port": 80,
            "api_key": "test-key"
        }
        
        truenas_config = TrueNASConfig(**config)
        assert truenas_config.base_url == "http://test.example.com:80/api/v2.0"


class TestResourceHandlers:
    """Test resource handlers."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock TrueNAS client."""
        client = MagicMock()
        client.get_system_info = AsyncMock(return_value={"hostname": "test"})
        client.get_pools = AsyncMock(return_value=[{"name": "test-pool"}])
        client.get_interfaces = AsyncMock(return_value=[{"name": "eth0"}])
        client.get_services = AsyncMock(return_value=[{"service": "smb"}])
        client.get_users = AsyncMock(return_value=[{"username": "test"}])
        return client
    
    def test_system_resource_tools(self, mock_client):
        """Test system resource tools."""
        resource = SystemResource(mock_client)
        tools = resource.get_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        assert "truenas_system_get_info" in tool_names
        assert "truenas_system_get_version" in tool_names
    
    def test_storage_resource_tools(self, mock_client):
        """Test storage resource tools."""
        resource = StorageResource(mock_client)
        tools = resource.get_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        assert "truenas_storage_get_pools" in tool_names
        assert "truenas_storage_create_pool" in tool_names
    
    def test_network_resource_tools(self, mock_client):
        """Test network resource tools."""
        resource = NetworkResource(mock_client)
        tools = resource.get_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        assert "truenas_network_get_interfaces" in tool_names
    
    def test_services_resource_tools(self, mock_client):
        """Test services resource tools."""
        resource = ServicesResource(mock_client)
        tools = resource.get_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        assert "truenas_services_get_all" in tool_names
    
    def test_users_resource_tools(self, mock_client):
        """Test users resource tools."""
        resource = UsersResource(mock_client)
        tools = resource.get_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        assert "truenas_users_get_all" in tool_names


class TestValidation:
    """Test validation utilities."""
    
    def test_validate_config(self):
        """Test configuration validation."""
        from src.utils.validation import validate_config
        
        config = {
            "host": "test.example.com",
            "port": 443,
            "api_key": "test-key"
        }
        
        validated = validate_config(config)
        assert validated["host"] == "test.example.com"
        assert validated["port"] == 443
    
    def test_validate_config_invalid(self):
        """Test invalid configuration validation."""
        from src.utils.validation import validate_config
        
        config = {
            "host": "test.example.com",
            "port": 99999,  # Invalid port
            "api_key": "test-key"
        }
        
        with pytest.raises(ValueError):
            validate_config(config)
    
    def test_validate_pool_config(self):
        """Test pool configuration validation."""
        from src.utils.validation import validate_pool_config
        
        valid_config = {
            "name": "test-pool",
            "disks": ["sda", "sdb"],
            "raid_type": "mirror"
        }
        
        assert validate_pool_config(valid_config) is True
        
        invalid_config = {
            "name": "test-pool",
            "disks": [],  # Empty disks list
            "raid_type": "mirror"
        }
        
        assert validate_pool_config(invalid_config) is False
    
    def test_validate_dataset_config(self):
        """Test dataset configuration validation."""
        from src.utils.validation import validate_dataset_config
        
        valid_config = {
            "name": "test-dataset",
            "pool": "test-pool",
            "type": "FILESYSTEM"
        }
        
        assert validate_dataset_config(valid_config) is True
        
        invalid_config = {
            "name": "test-dataset",
            "pool": "test-pool",
            "type": "INVALID_TYPE"
        }
        
        assert validate_dataset_config(invalid_config) is False


class TestLogging:
    """Test logging utilities."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        from src.utils.logging import setup_logging, get_logger
        
        setup_logging(level="DEBUG")
        logger = get_logger("test")
        
        assert logger.level <= 10  # DEBUG level
        assert logger.name == "test"
    
    def test_logger_creation(self):
        """Test logger creation."""
        from src.utils.logging import get_logger
        
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"


if __name__ == "__main__":
    pytest.main([__file__])
