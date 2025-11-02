"""
Authentication utilities for pfSense MCP Server.
"""

import base64
import ssl
from typing import Dict, Optional
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession, ClientTimeout

try:
    from .utils.logging import get_logger
except ImportError:
    # Fallback for direct execution
    from utils.logging import get_logger

logger = get_logger(__name__)


class PfSenseAuthError(Exception):
    """Exception raised for pfSense authentication errors."""
    pass


class PfSenseAuth:
    """
    Handles authentication for pfSense API requests.
    
    This class supports async context manager usage only (use 'async with').
    The synchronous context manager is not supported as it cannot properly
    clean up async resources like aiohttp.ClientSession.
    
    Example:
        async with PfSenseAuth(config) as auth:
            # Use auth object
            pass
    """
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize authentication with configuration.
        
        Args:
            config: Configuration dictionary containing auth parameters
        """
        self.host = config.get("host", "localhost")
        self.port = int(config.get("port", "443"))
        self.protocol = config.get("protocol", "https")
        self.api_key = config.get("api_key")
        self.username = config.get("username")
        self.password = config.get("password")
        self.ssl_verify = config.get("ssl_verify", "true").lower() == "true"
        self.session: Optional[ClientSession] = None
        
        # Validate configuration
        if not self.api_key and (not self.username or not self.password):
            raise PfSenseAuthError("Either api_key or username/password must be provided")
    
    async def create_session(self) -> ClientSession:
        """
        Create an authenticated aiohttp session.
        
        Returns:
            Configured aiohttp ClientSession
        """
        # SSL context configuration
        ssl_context = None
        if self.protocol == "https":
            ssl_context = ssl.create_default_context()
            if not self.ssl_verify:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create session with timeout
        timeout = ClientTimeout(total=30, connect=10)
        self.session = ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        
        return self.session
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary containing authentication headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            # pfSense 2.8.0 API expects X-API-Key header
            headers["X-API-Key"] = self.api_key
        elif self.username and self.password:
            # Basic authentication
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        return headers
    
    async def get_jwt_token(self) -> str:
        """
        Get JWT token for pfSense 2.8.0 API v2 authentication.
        
        Returns:
            JWT token string
        """
        if not self.session:
            self.session = await self.create_session()
        
        # Get JWT token using username/password
        jwt_data = {
            "username": self.username,
            "password": self.password
        }
        
        url = urljoin(self.get_base_url(), "/api/v2/auth/jwt")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with self.session.post(url, json=jwt_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("token", "")
            else:
                raise PfSenseAuthError(f"Failed to get JWT token: {response.status}")
    
    def get_jwt_headers(self, token: str) -> Dict[str, str]:
        """
        Get headers with JWT token for API requests.
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary containing authentication headers with JWT
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        return headers
    
    def get_base_url(self) -> str:
        """
        Get the base URL for pfSense API.
        
        Returns:
            Base URL string
        """
        return f"{self.protocol}://{self.host}:{self.port}"
    
    async def test_connection(self) -> bool:
        """
        Test the connection to pfSense.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.session:
                await self.create_session()
            
            headers = self.get_auth_headers()
            
            # Try pfSense 2.8.0 API v2 endpoints
            endpoints = [
                "/api/v2/diagnostics/system",
                "/api/v2/diagnostics/health",
                "/api/v2/diagnostics/arp_table",
                "/api/v2/auth/keys"
            ]
            
            for endpoint in endpoints:
                try:
                    url = urljoin(self.get_base_url(), endpoint)
                    async with self.session.get(url, headers=headers, allow_redirects=False) as response:
                        if response.status == 200:
                            # Check if we got HTML (login page) instead of JSON
                            content_type = response.headers.get('content-type', '')
                            if 'text/html' in content_type or 'application/json' not in content_type:
                                # We got a login page, try with different auth
                                continue
                            return True
                        elif response.status == 404:
                            continue
                        elif response.status in [301, 302, 303, 307, 308]:
                            # Redirect - likely to login page
                            continue
                        else:
                            continue
                except Exception:
                    continue
            
            return False
                    
        except Exception:
            return False
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
