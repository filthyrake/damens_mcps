"""Unit tests for TrueNAS MCP Server resource methods."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestStorageResource:
    """Test storage resource methods."""
    
    @pytest.mark.asyncio
    async def test_get_pools(self, mock_client, mock_truenas_api_responses):
        """Test getting storage pools."""
        from src.resources.storage import StorageResource
        
        mock_client.get_pools = AsyncMock(return_value=mock_truenas_api_responses["pools"])
        resource = StorageResource(mock_client)
        
        result = await resource.get_pools()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "tank"
    
    @pytest.mark.asyncio
    async def test_get_datasets(self, mock_client, mock_truenas_api_responses):
        """Test getting datasets."""
        from src.resources.storage import StorageResource
        
        mock_client.get_datasets = AsyncMock(return_value=mock_truenas_api_responses["datasets"])
        resource = StorageResource(mock_client)
        
        result = await resource.get_datasets()
        assert isinstance(result, list)
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_create_pool(self, mock_client, sample_pool_config):
        """Test creating a storage pool."""
        from src.resources.storage import StorageResource
        
        mock_client.create_pool = AsyncMock(return_value={"status": "success"})
        resource = StorageResource(mock_client)
        
        result = await resource.create_pool(sample_pool_config)
        assert result["status"] == "success"


class TestNetworkResource:
    """Test network resource methods."""
    
    @pytest.mark.asyncio
    async def test_get_interfaces(self, mock_client, mock_truenas_api_responses):
        """Test getting network interfaces."""
        from src.resources.network import NetworkResource
        
        mock_client.get_interfaces = AsyncMock(return_value=mock_truenas_api_responses["interfaces"])
        resource = NetworkResource(mock_client)
        
        result = await resource.get_interfaces()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "em0"
    
    @pytest.mark.asyncio
    async def test_interface_state(self, mock_client, mock_truenas_api_responses):
        """Test checking interface state."""
        from src.resources.network import NetworkResource
        
        mock_client.get_interfaces = AsyncMock(return_value=mock_truenas_api_responses["interfaces"])
        resource = NetworkResource(mock_client)
        
        interfaces = await resource.get_interfaces()
        assert interfaces[0]["state"]["link_state"] == "LINK_STATE_UP"
        assert interfaces[1]["state"]["link_state"] == "LINK_STATE_DOWN"


class TestServicesResource:
    """Test services resource methods."""
    
    @pytest.mark.asyncio
    async def test_get_services(self, mock_client, mock_truenas_api_responses):
        """Test getting services."""
        from src.resources.services import ServicesResource
        
        mock_client.get_services = AsyncMock(return_value=mock_truenas_api_responses["services"])
        resource = ServicesResource(mock_client)
        
        result = await resource.get_services()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["service"] == "ssh"
    
    @pytest.mark.asyncio
    async def test_service_state(self, mock_client, mock_truenas_api_responses):
        """Test checking service state."""
        from src.resources.services import ServicesResource
        
        mock_client.get_services = AsyncMock(return_value=mock_truenas_api_responses["services"])
        resource = ServicesResource(mock_client)
        
        services = await resource.get_services()
        ssh_service = next(s for s in services if s["service"] == "ssh")
        assert ssh_service["state"] == "RUNNING"
        
        nfs_service = next(s for s in services if s["service"] == "nfs")
        assert nfs_service["state"] == "STOPPED"
    
    @pytest.mark.asyncio
    async def test_start_service(self, mock_client):
        """Test starting a service."""
        from src.resources.services import ServicesResource
        
        mock_client.start_service = AsyncMock(return_value={"status": "started"})
        resource = ServicesResource(mock_client)
        
        result = await resource.start_service("nfs")
        assert result["status"] == "started"
    
    @pytest.mark.asyncio
    async def test_stop_service(self, mock_client):
        """Test stopping a service."""
        from src.resources.services import ServicesResource
        
        mock_client.stop_service = AsyncMock(return_value={"status": "stopped"})
        resource = ServicesResource(mock_client)
        
        result = await resource.stop_service("ssh")
        assert result["status"] == "stopped"


class TestSystemResource:
    """Test system resource methods."""
    
    @pytest.mark.asyncio
    async def test_get_system_info(self, mock_client):
        """Test getting system information."""
        from src.resources.system import SystemResource
        
        mock_client.get_system_info = AsyncMock(return_value={
            "hostname": "truenas-test",
            "version": "TrueNAS-SCALE-22.12.0"
        })
        resource = SystemResource(mock_client)
        
        result = await resource.get_system_info()
        assert result["hostname"] == "truenas-test"
        assert "version" in result
    
    @pytest.mark.asyncio
    async def test_get_version(self, mock_client):
        """Test getting TrueNAS version."""
        from src.resources.system import SystemResource
        
        mock_client.get_version = AsyncMock(return_value="TrueNAS-SCALE-22.12.0")
        resource = SystemResource(mock_client)
        
        result = await resource.get_version()
        assert "TrueNAS" in result


class TestUsersResource:
    """Test users resource methods."""
    
    @pytest.mark.asyncio
    async def test_get_users(self, mock_client):
        """Test getting users."""
        from src.resources.users import UsersResource
        
        mock_client.get_users = AsyncMock(return_value=[
            {"username": "root", "uid": 0},
            {"username": "testuser", "uid": 1001}
        ])
        resource = UsersResource(mock_client)
        
        result = await resource.get_users()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["username"] == "root"
    
    @pytest.mark.asyncio
    async def test_create_user(self, mock_client):
        """Test creating a user."""
        from src.resources.users import UsersResource
        
        user_config = {
            "username": "newuser",
            "full_name": "New User",
            "password": "securepassword",
            "uid": 1002
        }
        
        mock_client.create_user = AsyncMock(return_value={"id": 1002})
        resource = UsersResource(mock_client)
        
        result = await resource.create_user(user_config)
        assert result["id"] == 1002


class TestValidation:
    """Test validation for TrueNAS configurations."""
    
    def test_validate_pool_config(self, sample_pool_config):
        """Test pool configuration validation."""
        from src.utils.validation import validate_pool_config
        
        result = validate_pool_config(sample_pool_config)
        assert result is True
    
    def test_invalid_pool_config_empty_disks(self):
        """Test pool configuration with no disks."""
        from src.utils.validation import validate_pool_config
        
        invalid_config = {
            "name": "test-pool",
            "disks": [],  # Empty disks list
            "raid_type": "mirror"
        }
        
        result = validate_pool_config(invalid_config)
        assert result is False
    
    def test_validate_dataset_config(self, sample_dataset_config):
        """Test dataset configuration validation."""
        from src.utils.validation import validate_dataset_config
        
        result = validate_dataset_config(sample_dataset_config)
        assert result is True
    
    def test_invalid_dataset_type(self):
        """Test dataset configuration with invalid type."""
        from src.utils.validation import validate_dataset_config
        
        invalid_config = {
            "name": "test-dataset",
            "pool": "test-pool",
            "type": "INVALID_TYPE"
        }
        
        result = validate_dataset_config(invalid_config)
        assert result is False
