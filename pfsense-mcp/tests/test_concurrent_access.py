"""Tests for concurrent access to global pfSense client."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock


class TestConcurrentAccess:
    """Test cases for concurrent access to the global client."""
    
    @pytest.mark.asyncio
    async def test_concurrent_get_client_calls(self):
        """Test that multiple concurrent get_client() calls are properly synchronized."""
        import src.http_pfsense_server
        from src.http_pfsense_server import get_client
        
        # Reset global state for test
        src.http_pfsense_server.pfsense_client = None
        src.http_pfsense_server._client_lock = asyncio.Lock()
        
        # Mock the initialize_pfsense_client function
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(return_value=True)
        
        call_count = 0
        
        async def mock_initialize():
            """Mock initialization that tracks calls and simulates slow init."""
            nonlocal call_count
            call_count += 1
            # Simulate a slow initialization
            await asyncio.sleep(0.1)
            return mock_client
        
        with patch('src.http_pfsense_server.initialize_pfsense_client', side_effect=mock_initialize):
            # Make 10 concurrent calls to get_client
            tasks = [get_client() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All should return the same client instance
            assert all(r == results[0] for r in results), "All calls should return the same client"
            
            # Initialize should only be called once due to locking
            assert call_count == 1, f"Expected 1 initialization call, got {call_count}"
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test that concurrent tool calls don't corrupt client state."""
        import src.http_pfsense_server
        from src.http_pfsense_server import HTTPPfSenseMCPServer
        
        # Create a mock client
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(return_value=True)
        mock_client.get_system_info = AsyncMock(return_value={"version": "2.7.0"})
        mock_client.get_interfaces = AsyncMock(return_value=[{"name": "wan"}])
        mock_client.get_services = AsyncMock(return_value=[{"name": "dhcp"}])
        
        # Set the global client to our mock
        src.http_pfsense_server.pfsense_client = mock_client
        src.http_pfsense_server._client_lock = asyncio.Lock()
        
        # Initialize server
        server = HTTPPfSenseMCPServer()
        
        # Make concurrent tool calls
        tasks = [
            server._call_tool("get_system_info", {}),
            server._call_tool("get_interfaces", {}),
            server._call_tool("get_services", {}),
            server._call_tool("get_system_info", {}),
            server._call_tool("get_interfaces", {}),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        failed_results = [(i, r) for i, r in enumerate(results) if r.isError]
        assert not failed_results, \
            f"Expected all tool calls to succeed, but {len(failed_results)} failed: " + \
            ", ".join([f"task {i}: {r.content[0].text if r.content and len(r.content) > 0 else 'unknown error'}" 
                      for i, r in failed_results])
        
        # Verify the mock client methods were called
        assert mock_client.get_system_info.call_count == 2
        assert mock_client.get_interfaces.call_count == 2
        assert mock_client.get_services.call_count == 1
    
    @pytest.mark.asyncio
    async def test_lock_prevents_race_condition(self):
        """Test that the lock prevents race conditions during initialization."""
        import src.http_pfsense_server
        from src.http_pfsense_server import get_client
        
        # Reset global state for test
        src.http_pfsense_server.pfsense_client = None
        src.http_pfsense_server._client_lock = asyncio.Lock()  # Reset the lock too
        
        initialization_order = []
        
        async def mock_initialize():
            """Mock that records when initialization starts and ends."""
            initialization_order.append("start")
            await asyncio.sleep(0.05)
            initialization_order.append("end")
            mock = AsyncMock()
            mock.test_connection = AsyncMock(return_value=True)
            return mock
        
        with patch('src.http_pfsense_server.initialize_pfsense_client', side_effect=mock_initialize):
            # Start multiple concurrent calls
            tasks = [get_client() for _ in range(3)]
            await asyncio.gather(*tasks)
            
            # Should only see one start/end pair (initialization happened only once)
            assert initialization_order == ["start", "end"], \
                f"Expected single initialization, got: {initialization_order}"
    
    @pytest.mark.asyncio
    async def test_get_client_returns_none_on_failure(self):
        """Test that get_client returns None when initialization fails."""
        import src.http_pfsense_server
        from src.http_pfsense_server import get_client
        
        # Reset global state for test
        src.http_pfsense_server.pfsense_client = None
        src.http_pfsense_server._client_lock = asyncio.Lock()
        
        # Mock initialize to return None (failed initialization)
        with patch('src.http_pfsense_server.initialize_pfsense_client', return_value=None):
            client = await get_client()
            assert client is None, "get_client should return None when initialization fails"
    
    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self):
        """Test that get_client reuses an already initialized client."""
        import src.http_pfsense_server
        from src.http_pfsense_server import get_client
        
        # Reset global state for test
        src.http_pfsense_server.pfsense_client = None
        src.http_pfsense_server._client_lock = asyncio.Lock()
        
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(return_value=True)
        
        initialization_count = 0
        
        async def mock_initialize():
            nonlocal initialization_count
            initialization_count += 1
            return mock_client
        
        with patch('src.http_pfsense_server.initialize_pfsense_client', side_effect=mock_initialize):
            # First call should initialize
            client1 = await get_client()
            assert client1 is not None
            assert initialization_count == 1
            
            # Second call should reuse
            prev_count = initialization_count
            client2 = await get_client()
            assert client2 is client1
            assert initialization_count == prev_count, "Should not reinitialize"
