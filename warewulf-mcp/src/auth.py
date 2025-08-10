"""
Authentication module for the Warewulf MCP Server.
"""

import os
import base64
import json
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WarewulfAuth:
    """
    Authentication handler for Warewulf API.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize authentication handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load credentials from environment variables or config."""
        # Priority: config > environment variables
        self.host = (
            self.config.get('host') or 
            os.getenv('WAREWULF_HOST', 'localhost')
        )
        
        self.port = (
            self.config.get('port') or 
            int(os.getenv('WAREWULF_PORT', '9873'))
        )
        
        self.protocol = (
            self.config.get('protocol') or 
            os.getenv('WAREWULF_PROTOCOL', 'http')
        )
        
        self.username = (
            self.config.get('username') or 
            os.getenv('WAREWULF_USERNAME')
        )
        
        self.password = (
            self.config.get('password') or 
            os.getenv('WAREWULF_PASSWORD')
        )
        
        self.api_token = (
            self.config.get('api_token') or 
            os.getenv('WAREWULF_API_TOKEN')
        )
        
        self.ssl_verify = (
            self.config.get('ssl_verify', True) if 'ssl_verify' in self.config
            else os.getenv('WAREWULF_SSL_VERIFY', 'true').lower() == 'true'
        )
        
        self.timeout = (
            self.config.get('timeout') or 
            int(os.getenv('WAREWULF_TIMEOUT', '30'))
        )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary containing authentication headers
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Warewulf-MCP-Server/0.1.0'
        }
        
        if self.api_token:
            # Token-based authentication
            headers['Authorization'] = f'Bearer {self.api_token}'
        elif self.username and self.password:
            # Basic authentication
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
        
        return headers
    
    def get_base_url(self) -> str:
        """
        Get base URL for API requests.
        
        Returns:
            Base URL string
        """
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def get_api_url(self, endpoint: str = "") -> str:
        """
        Get full API URL for a specific endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full API URL string
        """
        base_url = self.get_base_url()
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        return f"{base_url}/api/{endpoint}"
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Validate that required credentials are present.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.host:
            return False, "Host is required"
        
        if not self.port or not (1 <= self.port <= 65535):
            return False, "Port must be between 1 and 65535"
        
        if not self.protocol or self.protocol not in ['http', 'https']:
            return False, "Protocol must be 'http' or 'https'"
        
        # Check if we have at least one authentication method
        if not self.api_token and (not self.username or not self.password):
            return False, "Either API token or username/password is required"
        
        return True, ""
    
    def get_connection_info(self) -> Dict[str, str]:
        """
        Get connection information (without sensitive data).
        
        Returns:
            Dictionary containing connection information
        """
        return {
            'host': self.host,
            'port': str(self.port),
            'protocol': self.protocol,
            'ssl_verify': str(self.ssl_verify),
            'timeout': str(self.timeout),
            'auth_method': 'token' if self.api_token else 'basic'
        }
    
    def test_connection(self) -> bool:
        """
        Test if we can form a valid connection URL.
        
        Returns:
            True if connection can be formed, False otherwise
        """
        try:
            url = self.get_base_url()
            return bool(url and '://' in url)
        except Exception:
            return False
