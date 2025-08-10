"""
Validation utilities for the Warewulf MCP Server.
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address format.
    
    Args:
        mac: MAC address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Common MAC address patterns
    patterns = [
        r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  # XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        r'^([0-9A-Fa-f]{2}){6}$',  # XXXXXXXXXXXX
    ]
    
    return any(re.match(pattern, mac) for pattern in patterns)


def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname format.
    
    Args:
        hostname: Hostname string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not hostname or len(hostname) > 253:
        return False
    
    # Check each label
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False
        
        # Label must start and end with alphanumeric
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
            return False
    
    return True


def validate_port(port: Union[int, str]) -> bool:
    """
    Validate port number.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_node_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate node configuration.
    
    Args:
        config: Node configuration dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['node_name']
    for field in required_fields:
        if field not in config or not config[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate node name
    if 'node_name' in config and not validate_hostname(config['node_name']):
        errors.append("Invalid node name format")
    
    # Validate IP address if provided
    if 'ipaddr' in config and config['ipaddr']:
        if not validate_ip_address(config['ipaddr']):
            errors.append("Invalid IP address format")
    
    # Validate MAC address if provided
    if 'hwaddr' in config and config['hwaddr']:
        if not validate_mac_address(config['hwaddr']):
            errors.append("Invalid MAC address format")
    
    # Validate profile if provided
    if 'profile' in config and config['profile']:
        if not isinstance(config['profile'], str) or not config['profile'].strip():
            errors.append("Profile must be a non-empty string")
    
    return errors


def validate_profile_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate profile configuration.
    
    Args:
        config: Profile configuration dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['profile_name']
    for field in required_fields:
        if field not in config or not config[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate profile name
    if 'profile_name' in config and not validate_hostname(config['profile_name']):
        errors.append("Invalid profile name format")
    
    return errors


def validate_image_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate image configuration.
    
    Args:
        config: Image configuration dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['image_name']
    for field in required_fields:
        if field not in config or not config[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate image name
    if 'image_name' in config and not re.match(r'^[a-zA-Z0-9._-]+$', config['image_name']):
        errors.append("Invalid image name format")
    
    return errors


def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize configuration by removing sensitive information.
    
    Args:
        config: Configuration dictionary to sanitize
        
    Returns:
        Sanitized configuration dictionary
    """
    sensitive_fields = ['password', 'token', 'secret', 'key']
    sanitized = config.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'
    
    return sanitized
