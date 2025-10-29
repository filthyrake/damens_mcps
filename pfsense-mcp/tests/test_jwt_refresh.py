"""Unit tests for JWT token refresh mechanism."""

import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from src.pfsense_client import HTTPPfSenseClient
from src.auth import PfSenseAuthError
from src.exceptions import PfSenseConfigurationError

# Test constant: 4 minutes in seconds (within the 5-minute default refresh buffer)
WITHIN_REFRESH_BUFFER_SECONDS = 240


class TestJWTTokenRefresh:
    """Test cases for JWT token refresh functionality."""
    
    @pytest.fixture
    def jwt_config(self):
        """Configuration with username/password for JWT auth."""
        return {
            "host": "192.168.1.1",
            "port": 443,
            "protocol": "https",
            "username": "admin",
            "password": "password",
            "ssl_verify": "false"
        }
    
    @pytest.fixture
    def api_key_config(self):
        """Configuration with API key auth."""
        return {
            "host": "192.168.1.1",
            "port": 443,
            "protocol": "https",
            "api_key": "test-api-key",
            "ssl_verify": "false"
        }
    
    @pytest.mark.asyncio
    async def test_token_expired_returns_true_when_no_expiry(self, jwt_config):
        """Test that _token_expired returns True when jwt_token_expiry is None."""
        client = HTTPPfSenseClient(jwt_config)
        assert client._token_expired() is True
    
    @pytest.mark.asyncio
    async def test_token_expired_returns_false_for_valid_token(self, jwt_config):
        """Test that _token_expired returns False for valid token."""
        client = HTTPPfSenseClient(jwt_config)
        # Set expiry to 1 hour from now
        client.jwt_token_expiry = time.time() + 3600
        assert client._token_expired() is False
    
    @pytest.mark.asyncio
    async def test_token_expired_returns_true_when_expired(self, jwt_config):
        """Test that _token_expired returns True for expired token."""
        client = HTTPPfSenseClient(jwt_config)
        # Set expiry to the past
        client.jwt_token_expiry = time.time() - 100
        assert client._token_expired() is True
    
    @pytest.mark.asyncio
    async def test_token_expired_returns_true_within_refresh_buffer(self, jwt_config):
        """Test that _token_expired returns True within refresh buffer."""
        client = HTTPPfSenseClient(jwt_config)
        # Set expiry to 4 minutes from now (within 5 minute buffer)
        client.jwt_token_expiry = time.time() + WITHIN_REFRESH_BUFFER_SECONDS
        assert client._token_expired() is True
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_skips_for_api_key_auth(self, api_key_config):
        """Test that _ensure_valid_token does nothing when using API key."""
        client = HTTPPfSenseClient(api_key_config)
        
        # Should not attempt to get JWT token
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            await client._ensure_valid_token()
            mock_get_jwt.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_skips_when_no_credentials(self):
        """Test that _ensure_valid_token does nothing without username/password."""
        config = {
            "host": "192.168.1.1",
            "port": 443,
            "protocol": "https",
            "api_key": None,  # No API key
            "ssl_verify": "false"
        }
        
        # This should raise an error during initialization
        with pytest.raises(PfSenseConfigurationError):
            HTTPPfSenseClient(config)
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_reuses_valid_token(self, jwt_config):
        """Test that _ensure_valid_token reuses valid token without refresh."""
        client = HTTPPfSenseClient(jwt_config)
        
        # Set a valid token
        client.jwt_token = "valid-token"
        client.jwt_token_expiry = time.time() + 3600
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            await client._ensure_valid_token()
            # Should not call get_jwt_token since token is valid
            mock_get_jwt.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_refreshes_expired_token(self, jwt_config):
        """Test that _ensure_valid_token refreshes expired token."""
        client = HTTPPfSenseClient(jwt_config)
        
        # Set an expired token
        client.jwt_token = "expired-token"
        client.jwt_token_expiry = time.time() - 100
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            mock_get_jwt.return_value = "new-token"
            
            await client._ensure_valid_token()
            
            # Should have called get_jwt_token to refresh
            mock_get_jwt.assert_called_once()
            assert client.jwt_token == "new-token"
            assert client.jwt_token_expiry is not None
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_acquires_new_token(self, jwt_config):
        """Test that _ensure_valid_token acquires new token when none exists."""
        client = HTTPPfSenseClient(jwt_config)
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            mock_get_jwt.return_value = "new-token"
            
            await client._ensure_valid_token()
            
            mock_get_jwt.assert_called_once()
            assert client.jwt_token == "new-token"
            assert client.jwt_token_expiry is not None
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_retries_on_failure(self, jwt_config):
        """Test that _ensure_valid_token retries on transient failures."""
        client = HTTPPfSenseClient(jwt_config)
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            # Fail first two attempts, succeed on third
            mock_get_jwt.side_effect = [
                PfSenseAuthError("Transient error 1"),
                PfSenseAuthError("Transient error 2"),
                "new-token"
            ]
            
            await client._ensure_valid_token()
            
            # Should have retried and eventually succeeded
            assert mock_get_jwt.call_count == 3
            assert client.jwt_token == "new-token"
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_falls_back_after_max_retries(self, jwt_config):
        """Test that _ensure_valid_token falls back after max retries."""
        client = HTTPPfSenseClient(jwt_config)
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            # Always fail
            mock_get_jwt.side_effect = PfSenseAuthError("Persistent error")
            
            # Should not raise, but fall back to basic auth
            await client._ensure_valid_token()
            
            # Should have tried 3 times
            assert mock_get_jwt.call_count == 3
            # Token should remain None (fallback to basic auth)
            assert client.jwt_token is None
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_exponential_backoff(self, jwt_config):
        """Test that _ensure_valid_token uses exponential backoff."""
        client = HTTPPfSenseClient(jwt_config)
        
        sleep_times = []
        
        async def mock_sleep(delay):
            sleep_times.append(delay)
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            with patch('asyncio.sleep', side_effect=mock_sleep):
                # Fail all attempts
                mock_get_jwt.side_effect = PfSenseAuthError("Error")
                
                await client._ensure_valid_token()
                
                # Should have exponential backoff: 2^0=1, 2^1=2
                # (no sleep after last attempt)
                assert sleep_times == [1, 2]
    
    @pytest.mark.asyncio
    async def test_make_request_ensures_valid_token(self, jwt_config):
        """Test that _make_request calls _ensure_valid_token."""
        client = HTTPPfSenseClient(jwt_config)
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        mock_response.headers = {"content-type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_response)
        mock_session.request.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.request.return_value.__aexit__ = AsyncMock(return_value=None)
        
        client.session = mock_session
        
        with patch.object(client, '_ensure_valid_token', new_callable=AsyncMock) as mock_ensure:
            with patch.object(client.auth, 'get_jwt_headers') as mock_jwt_headers:
                mock_jwt_headers.return_value = {"Authorization": "Bearer token"}
                client.jwt_token = "test-token"
                
                await client._make_request("GET", "/api/v2/test")
                
                # Should have called _ensure_valid_token
                mock_ensure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_initialization_sets_defaults(self, jwt_config):
        """Test that client initializes with correct defaults."""
        client = HTTPPfSenseClient(jwt_config)
        
        assert client.jwt_token is None
        assert client.jwt_token_expiry is None
        assert client.jwt_token_lifetime == 3600
        assert client.jwt_token_refresh_buffer == 300
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_handles_client_error(self, jwt_config):
        """Test that _ensure_valid_token handles aiohttp.ClientError."""
        client = HTTPPfSenseClient(jwt_config)
        
        with patch.object(client.auth, 'get_jwt_token', new_callable=AsyncMock) as mock_get_jwt:
            # Fail with ClientError
            mock_get_jwt.side_effect = [
                aiohttp.ClientError("Network error"),
                "new-token"
            ]
            
            await client._ensure_valid_token()
            
            # Should have retried and succeeded
            assert mock_get_jwt.call_count == 2
            assert client.jwt_token == "new-token"
    
    @pytest.mark.asyncio
    async def test_configurable_token_lifetime(self):
        """Test that JWT token lifetime can be configured."""
        config = {
            "host": "192.168.1.1",
            "port": 443,
            "protocol": "https",
            "username": "admin",
            "password": "password",
            "ssl_verify": "false",
            "jwt_token_lifetime": 7200,  # 2 hours
            "jwt_token_refresh_buffer": 600  # 10 minutes
        }
        
        client = HTTPPfSenseClient(config)
        
        assert client.jwt_token_lifetime == 7200
        assert client.jwt_token_refresh_buffer == 600
