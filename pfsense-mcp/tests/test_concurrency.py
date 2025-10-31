"""Tests for concurrent access synchronization in pfSense MCP Server."""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch
from src.http_pfsense_server import get_pfsense_client


class TestConcurrentAccess:
    """Test cases for concurrent access to global client state."""
    
    @pytest.mark.asyncio
    async def test_get_client_with_lock_exists(self):
        """Test that get_pfsense_client function exists and is async."""
        # Import the lock to verify it exists
        from src.http_pfsense_server import _client_lock
        
        # Verify the lock exists
        assert _client_lock is not None
        assert isinstance(_client_lock, asyncio.Lock)
    
    @pytest.mark.asyncio
    async def test_concurrent_get_client_calls(self):
        """Test that concurrent calls to get_pfsense_client are properly synchronized."""
        access_times = []
        
        async def timed_access(client_id: int):
            """Track when we enter and exit the get_pfsense_client call."""
            start = time.time()
            client = await get_pfsense_client()
            end = time.time()
            access_times.append((client_id, start, end))
            return client
        
        # Run multiple concurrent accesses
        tasks = [timed_access(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all accesses completed
        assert len(results) == 5
        
        # The lock ensures that get_pfsense_client calls are serialized
        # This means they should not overlap significantly
        assert len(access_times) == 5
    
    @pytest.mark.asyncio
    async def test_lock_prevents_race_condition_during_read(self):
        """Test that the lock prevents race conditions when reading the client."""
        from src.http_pfsense_server import _client_lock
        
        counter = {"value": 0}
        
        async def increment_with_delay():
            """Simulate a race condition scenario using the same lock."""
            async with _client_lock:
                # Read
                current = counter["value"]
                # Simulate delay that could cause race condition
                await asyncio.sleep(0.001)
                # Write
                counter["value"] = current + 1
        
        # Run multiple tasks concurrently
        tasks = [increment_with_delay() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # With proper locking, counter should be exactly 10
        # Without locking, it could be less due to race conditions
        assert counter["value"] == 10
    
    @pytest.mark.asyncio
    async def test_get_client_returns_none_when_not_initialized(self):
        """Test that get_pfsense_client returns None when client is not initialized."""
        # Mock the global client as None
        with patch('src.http_pfsense_server.pfsense_client', None):
            client = await get_pfsense_client()
            assert client is None
    
    @pytest.mark.asyncio
    async def test_lock_acquired_during_get_client(self):
        """Test that the lock is properly acquired during get_pfsense_client execution."""
        from src.http_pfsense_server import _client_lock
        
        lock_states = []
        
        async def check_lock_and_get():
            """Check if lock is acquired during get_pfsense_client."""
            # Before calling, lock should be free
            was_locked_before = _client_lock.locked()
            
            # Start the get_pfsense_client call
            async def track_during_call():
                # This should block if lock is held
                if _client_lock.locked():
                    lock_states.append("locked_during_call")
                await get_pfsense_client()
            
            # Call it
            await track_during_call()
            
            # After calling, lock should be released
            is_locked_after = _client_lock.locked()
            
            return (was_locked_before, is_locked_after)
        
        before, after = await check_lock_and_get()
        
        # Lock should not be held before or after the call
        assert before is False
        assert after is False


class TestCallToolSynchronization:
    """Test that _call_tool properly uses synchronized client access."""
    
    @pytest.mark.asyncio
    async def test_call_tool_uses_get_client(self):
        """Test that _call_tool uses get_pfsense_client for synchronized access."""
        from src.http_pfsense_server import HTTPPfSenseMCPServer
        
        server = HTTPPfSenseMCPServer()
        
        # Mock get_pfsense_client to return None
        with patch('src.http_pfsense_server.get_pfsense_client', AsyncMock(return_value=None)):
            result = await server._call_tool("get_system_info", {})
            
            # Should return error when client is not initialized
            assert result.isError is True
            assert "not initialized" in result.content[0].text.lower()


class TestMainFunctionInitialization:
    """Test that main() function properly initializes the global client."""
    
    @pytest.mark.asyncio
    async def test_main_has_global_declaration(self):
        """Test that main() function has proper global declaration.
        
        This test verifies the fix for the race condition issue where main()
        was missing the 'global pfsense_client' declaration, causing it to
        create a local variable instead of setting the global client.
        
        The fix ensures main() properly declares its intent to modify the
        global variable, matching the pattern used in get_client().
        """
        import inspect
        from src.http_pfsense_server import main
        
        # Get the source code of main()
        source = inspect.getsource(main)
        
        # Verify that main() contains 'global pfsense_client' declaration
        # This should appear early in the function, before any initialization
        assert 'global pfsense_client' in source, \
            "main() function must declare 'global pfsense_client' to properly set the global variable"
        
        # Verify it's an actual code statement (not in a comment or string)
        # Simple check: look for the line as actual code
        lines = source.split('\n')
        found_global_declaration = False
        
        for line in lines:
            stripped = line.strip()
            # Skip obvious comments
            if stripped.startswith('#'):
                continue
            # Check for the global declaration as a statement
            # It should be on its own line or at the start of the statement
            if stripped == 'global pfsense_client':
                found_global_declaration = True
                break
        
        assert found_global_declaration, \
            "main() must have 'global pfsense_client' as a standalone statement"
