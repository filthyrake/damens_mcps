"""
Warewulf API client for the MCP Server.
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from .auth import WarewulfAuth
from .utils.logging import log_request, log_response, log_error


class WarewulfClient:
    """
    Client for interacting with the Warewulf REST API.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Warewulf client.
        
        Args:
            config: Configuration dictionary
        """
        self.auth = WarewulfAuth(config)
        self.session = requests.Session()
        self.session.verify = self.auth.ssl_verify
        self.session.timeout = self.auth.timeout
        
        # Initialize logger
        from .utils.logging import setup_logging
        self.logger = setup_logging()
        
        # Validate credentials
        is_valid, error_msg = self.auth.validate_credentials()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {error_msg}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Tuple[int, Dict]:
        """
        Make HTTP request to Warewulf API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            
        Returns:
            Tuple of (status_code, response_data)
        """
        url = self.auth.get_api_url(endpoint)
        headers = self.auth.get_auth_headers()
        
        start_time = time.time()
        
        try:
            log_request(self.logger, method, endpoint, data=data, params=params)
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            
            response_time = time.time() - start_time
            
            # Log response
            log_response(
                self.logger, 
                response.status_code, 
                response_time,
                endpoint=endpoint
            )
            
            # Parse response
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {'text': response.text}
            
            return response.status_code, response_data
            
        except Exception as e:
            response_time = time.time() - start_time
            log_error(self.logger, e, {
                'method': method,
                'endpoint': endpoint,
                'response_time': response_time
            })
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Warewulf server.
        
        Returns:
            Connection test results
        """
        try:
            # Try to get API docs endpoint
            status_code, response_data = self._make_request('GET', '')
            
            return {
                'success': status_code < 400,
                'status_code': status_code,
                'response': response_data,
                'connection_info': self.auth.get_connection_info()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'connection_info': self.auth.get_connection_info()
            }
    
    def get_version(self) -> Dict[str, Any]:
        """
        Get Warewulf version information.
        
        Returns:
            Version information
        """
        status_code, response_data = self._make_request('GET', '')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_api_docs(self) -> Dict[str, Any]:
        """
        Get API documentation.
        
        Returns:
            API documentation
        """
        status_code, response_data = self._make_request('GET', 'docs')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    # Node Management
    def list_nodes(self) -> Dict[str, Any]:
        """
        List all nodes.
        
        Returns:
            List of nodes
        """
        status_code, response_data = self._make_request('GET', 'nodes')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_node(self, node_id: str) -> Dict[str, Any]:
        """
        Get node information.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Node information
        """
        status_code, response_data = self._make_request('GET', f'nodes/{node_id}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def create_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new node.
        
        Args:
            node_data: Node configuration data
            
        Returns:
            Creation result
        """
        status_code, response_data = self._make_request('PUT', f'nodes/{node_data.get("node_name")}', data=node_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def update_node(self, node_id: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing node.
        
        Args:
            node_id: Node identifier
            node_data: Updated node data
            
        Returns:
            Update result
        """
        status_code, response_data = self._make_request('PATCH', f'nodes/{node_id}', data=node_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def delete_node(self, node_id: str) -> Dict[str, Any]:
        """
        Delete a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Deletion result
        """
        status_code, response_data = self._make_request('DELETE', f'nodes/{node_id}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_node_fields(self, node_id: str) -> Dict[str, Any]:
        """
        Get available node fields.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Node fields information
        """
        status_code, response_data = self._make_request('GET', f'nodes/{node_id}/fields')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_node_raw(self, node_id: str) -> Dict[str, Any]:
        """
        Get raw node configuration.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Raw node configuration
        """
        status_code, response_data = self._make_request('GET', f'nodes/{node_id}/raw')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def build_node_overlays(self, node_id: str) -> Dict[str, Any]:
        """
        Build overlays for a specific node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Build result
        """
        status_code, response_data = self._make_request('POST', f'nodes/{node_id}/overlays/build')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def build_all_overlays(self) -> Dict[str, Any]:
        """
        Build all overlays.
        
        Returns:
            Build result
        """
        status_code, response_data = self._make_request('POST', 'nodes/overlays/build')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    # Profile Management
    def list_profiles(self) -> Dict[str, Any]:
        """
        List all profiles.
        
        Returns:
            List of profiles
        """
        status_code, response_data = self._make_request('GET', 'profiles')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Get profile information.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Profile information
        """
        status_code, response_data = self._make_request('GET', f'profiles/{profile_id}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new profile.
        
        Args:
            profile_data: Profile configuration data
            
        Returns:
            Creation result
        """
        status_code, response_data = self._make_request('PUT', f'profiles/{profile_data.get("profile_name")}', data=profile_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def update_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing profile.
        
        Args:
            profile_id: Profile identifier
            profile_data: Updated profile data
            
        Returns:
            Update result
        """
        status_code, response_data = self._make_request('PATCH', f'profiles/{profile_id}', data=profile_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Delete a profile.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Deletion result
        """
        status_code, response_data = self._make_request('DELETE', f'profiles/{profile_id}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    # Image Management
    def list_images(self) -> Dict[str, Any]:
        """
        List all images.
        
        Returns:
            List of images
        """
        status_code, response_data = self._make_request('GET', 'images')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_image(self, image_name: str) -> Dict[str, Any]:
        """
        Get image information.
        
        Args:
            image_name: Image name
            
        Returns:
            Image information
        """
        status_code, response_data = self._make_request('GET', f'images/{image_name}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def build_image(self, image_name: str) -> Dict[str, Any]:
        """
        Build an image.
        
        Args:
            image_name: Image name
            
        Returns:
            Build result
        """
        status_code, response_data = self._make_request('POST', f'images/{image_name}/build')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def import_image(self, image_name: str, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import an image.
        
        Args:
            image_name: Image name
            import_data: Import configuration
            
        Returns:
            Import result
        """
        status_code, response_data = self._make_request('POST', f'images/{image_name}/import', data=import_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def delete_image(self, image_name: str) -> Dict[str, Any]:
        """
        Delete an image.
        
        Args:
            image_name: Image name
            
        Returns:
            Deletion result
        """
        status_code, response_data = self._make_request('DELETE', f'images/{image_name}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    # Overlay Management
    def list_overlays(self) -> Dict[str, Any]:
        """
        List all overlays.
        
        Returns:
            List of overlays
        """
        status_code, response_data = self._make_request('GET', 'overlays')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_overlay(self, overlay_name: str) -> Dict[str, Any]:
        """
        Get overlay information.
        
        Args:
            overlay_name: Overlay name
            
        Returns:
            Overlay information
        """
        status_code, response_data = self._make_request('GET', f'overlays/{overlay_name}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def create_overlay(self, overlay_name: str, overlay_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new overlay.
        
        Args:
            overlay_name: Overlay name
            overlay_data: Overlay configuration
            
        Returns:
            Creation result
        """
        status_code, response_data = self._make_request('PUT', f'overlays/{overlay_name}', data=overlay_data)
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def delete_overlay(self, overlay_name: str) -> Dict[str, Any]:
        """
        Delete an overlay.
        
        Args:
            overlay_name: Overlay name
            
        Returns:
            Deletion result
        """
        status_code, response_data = self._make_request('DELETE', f'overlays/{overlay_name}')
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    def get_overlay_file(self, overlay_name: str, file_path: str) -> Dict[str, Any]:
        """
        Get overlay file contents.
        
        Args:
            overlay_name: Overlay name
            file_path: File path within overlay
            
        Returns:
            File contents
        """
        status_code, response_data = self._make_request('GET', f'overlays/{overlay_name}/file', params={'path': file_path})
        return {
            'status_code': status_code,
            'data': response_data
        }
    
    # Power Management (if supported by Warewulf)
    def power_on(self, node_id: str) -> Dict[str, Any]:
        """
        Power on a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Power operation result
        """
        # Note: This endpoint may not exist in all Warewulf versions
        try:
            status_code, response_data = self._make_request('POST', f'power/{node_id}/on')
            return {
                'status_code': status_code,
                'data': response_data
            }
        except Exception as e:
            return {
                'status_code': 501,  # Not Implemented
                'error': f'Power management not supported: {str(e)}'
            }
    
    def power_off(self, node_id: str) -> Dict[str, Any]:
        """
        Power off a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Power operation result
        """
        try:
            status_code, response_data = self._make_request('POST', f'power/{node_id}/off')
            return {
                'status_code': status_code,
                'data': response_data
            }
        except Exception as e:
            return {
                'status_code': 501,
                'error': f'Power management not supported: {str(e)}'
            }
    
    def power_reset(self, node_id: str) -> Dict[str, Any]:
        """
        Reset a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Power operation result
        """
        try:
            status_code, response_data = self._make_request('POST', f'power/{node_id}/reset')
            return {
                'status_code': status_code,
                'data': response_data
            }
        except Exception as e:
            return {
                'status_code': 501,
                'error': f'Power management not supported: {str(e)}'
            }
    
    def power_cycle(self, node_id: str) -> Dict[str, Any]:
        """
        Power cycle a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Power operation result
        """
        try:
            status_code, response_data = self._make_request('POST', f'power/{node_id}/cycle')
            return {
                'status_code': status_code,
                'data': response_data
            }
        except Exception as e:
            return {
                'status_code': 501,
                'error': f'Power management not supported: {str(e)}'
            }
    
    def power_status(self, node_id: str) -> Dict[str, Any]:
        """
        Get power status of a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Power status
        """
        try:
            status_code, response_data = self._make_request('GET', f'power/{node_id}/status')
            return {
                'status_code': status_code,
                'data': response_data
            }
        except Exception as e:
            return {
                'status_code': 501,
                'error': f'Power management not supported: {str(e)}'
            }
