"""
pfSense Web Interface Client for MCP Server.
Works with pfSense versions that don't have REST API available.
"""

import re
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from aiohttp import ClientSession

try:
    from .auth import PfSenseAuth
    from .utils.mcp_logging import get_logger
except ImportError:
    # Fallback for direct execution
    from auth import PfSenseAuth
    from utils.mcp_logging import get_logger

logger = get_logger(__name__)


class PfSenseWebError(Exception):
    """Exception raised for pfSense web interface errors."""
    pass


class WebPfSenseClient:
    """
    Web interface client for pfSense (for versions without REST API).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the pfSense web client.
        
        Args:
            config: Configuration dictionary
        """
        self.auth = PfSenseAuth(config)
        self.session: Optional[ClientSession] = None
        self.base_url = self.auth.get_base_url()
        self.csrf_token: Optional[str] = None
        
    async def _get_csrf_token(self) -> str:
        """Get CSRF token from the login page."""
        if not self.session:
            self.session = await self.auth.create_session()
        
        # Get the login page to extract CSRF token
        url = urljoin(self.base_url, "/")
        async with self.session.get(url, allow_redirects=False) as response:
            if response.status != 200:
                raise PfSenseWebError(f"Failed to get login page: {response.status}")
            
            html = await response.text()
            
            # Look for CSRF token in various forms
            csrf_patterns = [
                r'name="__csrf_magic"\s+value="([^"]+)"',
                r'name="csrf_token"\s+value="([^"]+)"',
                r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']',
                r'__csrf_magic["\']?\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, html)
                if match:
                    return match.group(1)
            
            # If no CSRF token found, return empty string
            return ""
    
    async def _login(self) -> bool:
        """Login to pfSense web interface."""
        if not self.session:
            self.session = await self.auth.create_session()
        
        # Get CSRF token
        self.csrf_token = await self._get_csrf_token()
        
        # Prepare login data
        login_data = {
            "usernamefld": self.auth.username,
            "passwordfld": self.auth.password,
            "login": "Sign In"
        }
        
        # Add CSRF token if found
        if self.csrf_token:
            login_data["__csrf_magic"] = self.csrf_token
        
        # Login
        login_url = urljoin(self.base_url, "/")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": self.base_url
        }
        
        async with self.session.post(login_url, data=login_data, headers=headers, allow_redirects=False) as response:
            # Check if login was successful (usually redirects to dashboard)
            if response.status in [200, 302, 303]:
                # Check if we're redirected to dashboard or still on login page
                location = response.headers.get('location', '')
                if 'index.php' in location or 'dashboard' in location:
                    return True
                elif response.status == 200:
                    # Check if we're still on login page
                    html = await response.text()
                    if 'login' not in html.lower() and 'usernamefld' not in html:
                        return True
            
            return False
    
    async def _get_page_content(self, path: str) -> str:
        """Get content from a pfSense page."""
        if not self.session:
            # Try to login first
            if not await self._login():
                raise PfSenseWebError("Failed to login to pfSense")
        
        url = urljoin(self.base_url, path)
        async with self.session.get(url, allow_redirects=False) as response:
            if response.status == 200:
                return await response.text()
            elif response.status in [301, 302, 303]:
                # Redirected - might need to login again
                if await self._login():
                    # Retry the request
                    async with self.session.get(url, allow_redirects=False) as retry_response:
                        if retry_response.status == 200:
                            return await retry_response.text()
            
            raise PfSenseWebError(f"Failed to get page {path}: {response.status}")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information from the dashboard."""
        try:
            html = await self._get_page_content("/index.php")
            
            # Extract system information from dashboard
            info = {
                "version": "Unknown",
                "platform": "pfSense",
                "uptime": "Unknown",
                "hostname": "Unknown"
            }
            
            # Look for version information
            version_patterns = [
                r'pfSense\s+([0-9.]+)',
                r'Version:\s*([0-9.]+)',
                r'pfSense\s+CE\s+([0-9.]+)',
                r'pfSense\s+Plus\s+([0-9.]+)'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    info["version"] = match.group(1)
                    break
            
            # Look for hostname
            hostname_patterns = [
                r'Hostname:\s*([^\n<]+)',
                r'<title>([^<]+)</title>'
            ]
            
            for pattern in hostname_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    info["hostname"] = match.group(1).strip()
                    break
            
            # Look for uptime
            uptime_patterns = [
                r'Uptime:\s*([^\n<]+)',
                r'System\s+uptime:\s*([^\n<]+)'
            ]
            
            for pattern in uptime_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    info["uptime"] = match.group(1).strip()
                    break
            
            return info
            
        except Exception as e:
            return {
                "version": "Unknown",
                "platform": "pfSense",
                "error": f"Failed to extract system info: {str(e)}"
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            html = await self._get_page_content("/index.php")
            
            health = {
                "status": "Online",
                "cpu_usage": "Unknown",
                "memory_usage": "Unknown",
                "disk_usage": "Unknown"
            }
            
            # Look for CPU usage
            cpu_patterns = [
                r'CPU:\s*([0-9.]+)%',
                r'CPU\s+Usage:\s*([0-9.]+)%'
            ]
            
            for pattern in cpu_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    health["cpu_usage"] = f"{match.group(1)}%"
                    break
            
            # Look for memory usage
            memory_patterns = [
                r'Memory:\s*([0-9.]+)%',
                r'Memory\s+Usage:\s*([0-9.]+)%'
            ]
            
            for pattern in memory_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    health["memory_usage"] = f"{match.group(1)}%"
                    break
            
            return health
            
        except Exception as e:
            return {
                "status": "Unknown",
                "error": f"Failed to get health info: {str(e)}"
            }
    
    async def get_interfaces(self) -> Dict[str, Any]:
        """Get network interfaces information."""
        try:
            # Fetch the interfaces page
            await self._get_page_content("/interfaces.php")
            
            # This is a simplified extraction - would need more sophisticated parsing
            # to extract actual interface data from the HTML
            return {
                "interfaces": "Available (requires detailed parsing)",
                "note": "Interface details available via web interface"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get interfaces: {str(e)}"
            }
    
    async def test_connection(self) -> bool:
        """Test the connection to pfSense web interface."""
        try:
            if not self.session:
                self.session = await self.auth.create_session()
            
            # Test basic connectivity
            url = urljoin(self.base_url, "/")
            async with self.session.get(url, allow_redirects=False) as response:
                if response.status == 200:
                    return True
                elif response.status in [301, 302, 303]:
                    # Redirect is OK - means pfSense is responding
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
        await self.auth.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
