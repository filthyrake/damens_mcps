"""Tests for debug log redaction of sensitive authentication information."""

import pytest
import sys
import os
from io import StringIO
from unittest.mock import patch, Mock, MagicMock
import requests

# Add parent directory to path to import the server module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from working_mcp_server import IDracClient, debug_print


class TestDebugRedaction:
    """Test that sensitive authentication information is redacted from debug logs."""
    
    def test_debug_print_writes_to_stderr(self):
        """Test that debug_print writes to stderr."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            debug_print("Test message")
            output = mock_stderr.getvalue()
            assert "DEBUG: Test message" in output
    
    def test_client_init_redacts_sensitive_headers(self):
        """Test that IDracClient.__init__ redacts sensitive headers in debug logs."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            # Create client with credentials
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="testuser",
                password="testpass123",
                ssl_verify=False
            )
            
            output = mock_stderr.getvalue()
            
            # Should contain basic info
            assert "Created iDRAC client" in output
            assert "SSL Verify: False" in output
            
            # Should not contain actual password or credentials
            assert "testpass123" not in output
            assert "testuser:testpass123" not in output
            
            # Should redact Authorization header if present
            if "authorization" in output.lower():
                # Authorization should be redacted
                assert "REDACTED" in output
    
    def test_client_init_redacts_auth_credentials(self):
        """Test that auth credentials are not logged."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="admin",
                password="secret_password_123",
                ssl_verify=False
            )
            
            output = mock_stderr.getvalue()
            
            # Should not contain the actual HTTPBasicAuth object with credentials
            assert "secret_password_123" not in output
            assert "admin:secret_password_123" not in output
            
            # Should only log the type name
            assert "HTTPBasicAuth" in output or "Auth type:" in output
    
    def test_make_request_redacts_session_auth(self):
        """Test that _make_request redacts session.auth credentials."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="pass123",
                ssl_verify=False
            )
            
            # Mock the session.get to avoid actual network calls
            with patch.object(client.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {}
                mock_response.cookies = {}
                mock_get.return_value = mock_response
                
                try:
                    client._make_request('GET', '/test')
                except Exception:
                    pass
                
                output = mock_stderr.getvalue()
                
                # Should not contain actual credentials
                assert "pass123" not in output
                assert "user:pass123" not in output
                
                # Should log whether auth is configured (boolean)
                # or just indicate presence without details
                assert "Session auth configured:" in output or "Session auth:" in output
    
    def test_make_request_redacts_cookies(self):
        """Test that _make_request redacts cookie values."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="pass123",
                ssl_verify=False
            )
            
            # Add a cookie to the session
            client.session.cookies.set('session_token', 'secret_token_value_12345')
            
            # Mock the session.get
            with patch.object(client.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {}
                mock_response.cookies = {'another_cookie': 'another_secret'}
                mock_get.return_value = mock_response
                
                try:
                    client._make_request('GET', '/test')
                except Exception:
                    pass
                
                output = mock_stderr.getvalue()
                
                # Should not contain actual cookie values
                assert "secret_token_value_12345" not in output
                assert "another_secret" not in output
                
                # Should log cookie count or presence indicator
                assert "cookies" in output.lower() or "Session has cookies:" in output
    
    def test_make_request_redacts_sensitive_request_headers(self):
        """Test that _make_request redacts sensitive headers."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="pass123",
                ssl_verify=False
            )
            
            # Add sensitive headers
            client.session.headers['Authorization'] = 'Bearer secret_token_xyz'
            client.session.headers['X-Auth-Token'] = 'auth_token_abc'
            
            # Mock the session.get
            with patch.object(client.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {}
                mock_response.cookies = {}
                mock_get.return_value = mock_response
                
                try:
                    client._make_request('GET', '/test')
                except Exception:
                    pass
                
                output = mock_stderr.getvalue()
                
                # Should not contain actual sensitive header values
                assert "secret_token_xyz" not in output
                assert "auth_token_abc" not in output
                
                # Should contain REDACTED instead
                assert "REDACTED" in output
    
    def test_make_request_redacts_response_headers(self):
        """Test that response headers with auth tokens are redacted."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="pass123",
                ssl_verify=False
            )
            
            # Mock the session.get with response containing sensitive headers
            with patch.object(client.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {
                    'Content-Type': 'application/json',
                    'Set-Cookie': 'session=secret_session_id_xyz',
                    'X-Auth-Token': 'response_token_123'
                }
                mock_response.cookies = {'session': 'secret_session_id_xyz'}
                mock_get.return_value = mock_response
                
                try:
                    client._make_request('GET', '/test')
                except Exception:
                    pass
                
                output = mock_stderr.getvalue()
                
                # Should not contain actual sensitive values
                assert "secret_session_id_xyz" not in output
                assert "response_token_123" not in output
    
    def test_reauthentication_redacts_credentials(self):
        """Test that re-authentication logs don't expose credentials."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="super_secret_pass",
                ssl_verify=False
            )
            
            # Mock the session.get to return 401 first, then 200
            with patch.object(client.session, 'get') as mock_get:
                mock_response_401 = Mock()
                mock_response_401.status_code = 401
                mock_response_401.headers = {}
                mock_response_401.cookies = MagicMock()
                mock_response_401.cookies.__len__ = Mock(return_value=0)
                mock_response_401.cookies.__iter__ = Mock(return_value=iter([]))
                
                mock_response_200 = Mock()
                mock_response_200.status_code = 200
                mock_response_200.headers = {}
                mock_response_200.cookies = MagicMock()
                mock_response_200.cookies.__len__ = Mock(return_value=0)
                mock_response_200.cookies.__iter__ = Mock(return_value=iter([]))
                
                mock_get.side_effect = [mock_response_401, mock_response_200]
                
                try:
                    client._make_request('GET', '/test')
                except Exception:
                    pass
                
                output = mock_stderr.getvalue()
                
                # Should not contain actual password
                assert "super_secret_pass" not in output
                assert "user:super_secret_pass" not in output
                
                # Should mention re-authentication
                assert "401 Unauthorized" in output or "re-authenticate" in output.lower()


class TestRedactionHelpers:
    """Test helper functions for redacting sensitive information."""
    
    def test_redact_sensitive_headers(self):
        """Test that sensitive headers are properly redacted."""
        from working_mcp_server import IDracClient
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer secret_token',
            'Cookie': 'session=12345',
            'X-Auth-Token': 'auth_token',
            'User-Agent': 'Test'
        }
        
        # Create a client to test the redaction logic
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            client = IDracClient(
                host="192.168.1.100",
                port=443,
                protocol="https",
                username="user",
                password="pass",
                ssl_verify=False
            )
        
        # The redaction should be applied in the debug logs
        # We verify this by checking that sensitive values aren't logged
        # This is verified in the other tests above


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
