"""Unit tests for PfSenseAuth context manager behavior.

This test suite verifies that:
1. PfSenseAuth properly implements async context manager (__aenter__/__aexit__)
2. PfSenseAuth does NOT support sync context manager (__enter__/__exit__)
3. Session resources are properly created and cleaned up
4. Cleanup occurs even when exceptions are raised

The sync context manager was removed because it cannot properly handle
async resource cleanup (aiohttp.ClientSession), which would cause resource
leaks and runtime warnings.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from src.auth import PfSenseAuth, PfSenseAuthError


class TestPfSenseAuthContextManager:
    """Test cases for PfSenseAuth context manager functionality."""
    
    @pytest.fixture
    def auth_config(self):
        """Configuration for PfSenseAuth."""
        return {
            "host": "192.168.1.1",
            "port": 443,
            "protocol": "https",
            "api_key": "test-api-key",
            "ssl_verify": "false"
        }
    
    @pytest.mark.asyncio
    async def test_async_context_manager_creates_and_closes_session(self, auth_config):
        """Test that async context manager properly creates and closes session."""
        auth = PfSenseAuth(auth_config)
        
        # Session should not exist initially
        assert auth.session is None
        
        # Use async context manager
        async with auth as auth_ctx:
            # Session should be created
            assert auth_ctx.session is not None
            assert isinstance(auth_ctx.session, aiohttp.ClientSession)
            assert not auth_ctx.session.closed
        
        # Session should be closed after exiting context
        # Note: The session is set to None in close()
        assert auth.session is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager_closes_on_exception(self, auth_config):
        """Test that async context manager closes session even on exception."""
        auth = PfSenseAuth(auth_config)
        
        try:
            async with auth as auth_ctx:
                # Session should be created
                assert auth_ctx.session is not None
                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Session should still be closed after exception
        assert auth.session is None
    
    @pytest.mark.asyncio
    async def test_manual_close_method(self, auth_config):
        """Test that manual close method properly closes session."""
        auth = PfSenseAuth(auth_config)
        
        # Create session
        await auth.create_session()
        assert auth.session is not None
        assert isinstance(auth.session, aiohttp.ClientSession)
        
        # Close manually
        await auth.close()
        
        # Session should be None
        assert auth.session is None
    
    def test_sync_context_manager_not_supported(self, auth_config):
        """Test that synchronous context manager is not available."""
        auth = PfSenseAuth(auth_config)
        
        # Check that __enter__ and __exit__ do not exist
        assert not hasattr(auth, '__enter__')
        assert not hasattr(auth, '__exit__')
    
    @pytest.mark.asyncio
    async def test_async_context_manager_methods_exist(self, auth_config):
        """Test that async context manager methods exist."""
        auth = PfSenseAuth(auth_config)
        
        # Check that __aenter__ and __aexit__ exist and are callable
        assert hasattr(auth, '__aenter__')
        assert callable(auth.__aenter__)
        assert hasattr(auth, '__aexit__')
        assert callable(auth.__aexit__)
    
    @pytest.mark.asyncio
    async def test_close_handles_no_session(self, auth_config):
        """Test that close method handles case when session is None."""
        auth = PfSenseAuth(auth_config)
        
        # Session should be None
        assert auth.session is None
        
        # Close should not raise an error
        await auth.close()
        
        # Session should still be None
        assert auth.session is None
    
    @pytest.mark.asyncio
    async def test_multiple_async_context_uses(self, auth_config):
        """Test that auth can be used with async context manager multiple times."""
        auth = PfSenseAuth(auth_config)
        
        # First use
        async with auth:
            assert auth.session is not None
        assert auth.session is None
        
        # Second use - should work again
        async with auth:
            assert auth.session is not None
        assert auth.session is None
