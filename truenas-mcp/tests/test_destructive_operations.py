"""Tests for destructive operations with confirmation flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.resources.storage import StorageResource
from src.resources.system import SystemResource


class MockCallToolRequest:
    """Mock CallToolRequest that matches the structure expected by resource handlers."""
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or {}


@pytest.fixture
def mock_client():
    """Create a mock TrueNAS client."""
    client = MagicMock()
    client.delete_pool = AsyncMock()
    client.delete_dataset = AsyncMock()
    client.delete_snapshot = AsyncMock()
    client.reboot_system = AsyncMock()
    client.shutdown_system = AsyncMock()
    client.get_pool = AsyncMock()
    return client


@pytest.fixture
def storage_resource(mock_client):
    """Create a StorageResource instance with mock client."""
    return StorageResource(mock_client)


@pytest.fixture
def system_resource(mock_client):
    """Create a SystemResource instance with mock client."""
    return SystemResource(mock_client)


class TestDeletePoolConfirmation:
    """Test delete pool with confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_delete_pool_without_confirmation(self, storage_resource):
        """Test that delete_pool requires confirmation."""
        request = MockCallToolRequest(name="truenas_storage_delete_pool", arguments={"pool_id": "test-pool"})
        
        result = await storage_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
        assert "confirm" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_pool_with_false_confirmation(self, storage_resource):
        """Test that delete_pool with confirm=False is rejected."""
        request = MockCallToolRequest(name="truenas_storage_delete_pool", arguments={"pool_id": "test-pool", "confirm": False})
        
        result = await storage_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_pool_with_confirmation_pool_not_found(self, storage_resource, mock_client):
        """Test delete_pool with confirmation but pool doesn't exist."""
        mock_client.get_pool.side_effect = Exception("Pool not found")
        
        request = MockCallToolRequest(name="truenas_storage_delete_pool", arguments={"pool_id": "nonexistent-pool", "confirm": True})
        
        result = await storage_resource.handle_tool(request)
        
        assert result.isError is True
        assert "not found" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_pool_with_confirmation_success(self, storage_resource, mock_client):
        """Test successful delete_pool with confirmation."""
        mock_client.get_pool.return_value = {"id": "test-pool", "name": "test-pool"}
        mock_client.delete_pool.return_value = {"status": "success", "pool_id": "test-pool"}
        
        request = MockCallToolRequest(name="truenas_storage_delete_pool", arguments={"pool_id": "test-pool", "confirm": True})
        
        result = await storage_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.get_pool.assert_called_once_with("test-pool")
        mock_client.delete_pool.assert_called_once_with("test-pool")


class TestDeleteDatasetConfirmation:
    """Test delete dataset with confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_delete_dataset_without_confirmation(self, storage_resource):
        """Test that delete_dataset requires confirmation."""
        request = MockCallToolRequest(name="truenas_storage_delete_dataset", arguments={"dataset_id": "pool/dataset"})
        
        result = await storage_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_dataset_with_confirmation_success(self, storage_resource, mock_client):
        """Test successful delete_dataset with confirmation."""
        mock_client.delete_dataset.return_value = {"status": "success"}
        
        request = MockCallToolRequest(name="truenas_storage_delete_dataset", arguments={"dataset_id": "pool/dataset", "confirm": True})
        
        result = await storage_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.delete_dataset.assert_called_once_with("pool/dataset")


class TestDeleteSnapshotConfirmation:
    """Test delete snapshot with confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_delete_snapshot_without_confirmation(self, storage_resource):
        """Test that delete_snapshot requires confirmation."""
        request = MockCallToolRequest(name="truenas_storage_delete_snapshot", arguments={"snapshot_id": "pool/dataset@snap1"})
        
        result = await storage_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_snapshot_with_confirmation_success(self, storage_resource, mock_client):
        """Test successful delete_snapshot with confirmation."""
        mock_client.delete_snapshot.return_value = {"status": "success"}
        
        request = MockCallToolRequest(name="truenas_storage_delete_snapshot", arguments={"snapshot_id": "pool/dataset@snap1", "confirm": True})
        
        result = await storage_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.delete_snapshot.assert_called_once_with("pool/dataset@snap1")


class TestRebootSystemConfirmation:
    """Test system reboot with confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_reboot_without_confirmation(self, system_resource):
        """Test that reboot requires confirmation."""
        request = MockCallToolRequest(name="truenas_system_reboot", arguments={})
        
        result = await system_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_reboot_with_confirmation_success(self, system_resource, mock_client):
        """Test successful reboot with confirmation."""
        mock_client.reboot_system.return_value = {"status": "rebooting"}
        
        request = MockCallToolRequest(name="truenas_system_reboot", arguments={"confirm": True})
        
        result = await system_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.reboot_system.assert_called_once_with(0)
    
    @pytest.mark.asyncio
    async def test_reboot_with_delay_and_confirmation(self, system_resource, mock_client):
        """Test reboot with delay and confirmation."""
        mock_client.reboot_system.return_value = {"status": "rebooting", "delay": 60}
        
        request = MockCallToolRequest(name="truenas_system_reboot", arguments={"delay": 60, "confirm": True})
        
        result = await system_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.reboot_system.assert_called_once_with(60)


class TestShutdownSystemConfirmation:
    """Test system shutdown with confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_shutdown_without_confirmation(self, system_resource):
        """Test that shutdown requires confirmation."""
        request = MockCallToolRequest(name="truenas_system_shutdown", arguments={})
        
        result = await system_resource.handle_tool(request)
        
        assert result.isError is True
        assert "confirmation" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_confirmation_success(self, system_resource, mock_client):
        """Test successful shutdown with confirmation."""
        mock_client.shutdown_system.return_value = {"status": "shutting_down"}
        
        request = MockCallToolRequest(name="truenas_system_shutdown", arguments={"confirm": True})
        
        result = await system_resource.handle_tool(request)
        
        assert not result.isError
        mock_client.shutdown_system.assert_called_once_with(0)


class TestClientMethods:
    """Test client methods for reboot and shutdown."""
    
    @pytest.mark.asyncio
    async def test_client_reboot_method(self):
        """Test that client has reboot_system method."""
        from src.truenas_client import TrueNASClient
        
        # Check method exists
        assert hasattr(TrueNASClient, 'reboot_system')
    
    @pytest.mark.asyncio
    async def test_client_shutdown_method(self):
        """Test that client has shutdown_system method."""
        from src.truenas_client import TrueNASClient
        
        # Check method exists
        assert hasattr(TrueNASClient, 'shutdown_system')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
