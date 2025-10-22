"""
Validation utilities for pfSense MCP Server.
"""

import ipaddress
import re
from typing import Any, Dict, List, Optional, Union


def validate_ip_address(ip: str) -> bool:
    """
    Validate if a string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port: Union[int, str]) -> bool:
    """
    Validate if a port number is valid.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid port (1-65535), False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_mac_address(mac: str) -> bool:
    """
    Validate if a string is a valid MAC address.
    
    Args:
        mac: MAC address string to validate
        
    Returns:
        True if valid MAC address, False otherwise
    """
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_pattern.match(mac))


def validate_vlan_id(vlan_id: Union[int, str]) -> bool:
    """
    Validate if a VLAN ID is valid.
    
    Args:
        vlan_id: VLAN ID to validate
        
    Returns:
        True if valid VLAN ID (1-4094), False otherwise
    """
    try:
        vlan_num = int(vlan_id)
        return 1 <= vlan_num <= 4094
    except (ValueError, TypeError):
        return False


def validate_firewall_rule_params(params: Dict[str, Any]) -> List[str]:
    """
    Validate firewall rule parameters.
    
    Args:
        params: Dictionary of firewall rule parameters
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['action', 'interface', 'direction']
    for field in required_fields:
        if field not in params or not params[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate action
    if 'action' in params and params['action'] not in ['pass', 'block', 'reject']:
        errors.append("Invalid action. Must be 'pass', 'block', or 'reject'")
    
    # Validate direction
    if 'direction' in params and params['direction'] not in ['in', 'out']:
        errors.append("Invalid direction. Must be 'in' or 'out'")
    
    # Validate source/destination if provided
    if 'source' in params and params['source']:
        if not validate_ip_address(params['source']) and params['source'] != 'any':
            errors.append("Invalid source address")
    
    if 'destination' in params and params['destination']:
        if not validate_ip_address(params['destination']) and params['destination'] != 'any':
            errors.append("Invalid destination address")
    
    # Validate port if provided
    if 'port' in params and params['port']:
        if not validate_port(params['port']):
            errors.append("Invalid port number")
    
    return errors


def validate_vlan_params(params: Dict[str, Any]) -> List[str]:
    """
    Validate VLAN parameters.
    
    Args:
        params: Dictionary of VLAN parameters
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    if 'vlan_id' not in params:
        errors.append("Missing required field: vlan_id")
    elif not validate_vlan_id(params['vlan_id']):
        errors.append("Invalid VLAN ID. Must be between 1 and 4094")
    
    if 'interface' not in params or not params['interface']:
        errors.append("Missing required field: interface")
    
    return errors


def sanitize_string(value: str) -> str:
    """
    Sanitize a string value for safe use in API calls.
    
    DEPRECATED: Use specific validation functions instead (validate_package_name, validate_service_name, etc.)
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(value))
    return sanitized.strip()


def validate_package_name(name: str) -> bool:
    """
    Validate package name using whitelist approach.
    
    Package names should only contain alphanumeric characters, hyphens, underscores, and dots.
    This prevents command injection attacks.
    
    Args:
        name: Package name to validate
        
    Returns:
        True if valid package name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    # This is safe for pfSense package manager
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, name)) and len(name) <= 255


def validate_service_name(name: str) -> bool:
    """
    Validate service name using whitelist approach.
    
    Service names should only contain alphanumeric characters, hyphens, and underscores.
    This prevents command injection attacks.
    
    Args:
        name: Service name to validate
        
    Returns:
        True if valid service name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    # Common service names: openvpn, ipsec, wireguard, etc.
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name)) and len(name) <= 128


def validate_backup_name(name: str) -> bool:
    """
    Validate backup name using whitelist approach.
    
    Backup names should only contain alphanumeric characters, hyphens, underscores, and dots.
    
    Args:
        name: Backup name to validate
        
    Returns:
        True if valid backup name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, name)) and len(name) <= 255


def validate_id(id_value: str) -> bool:
    """
    Validate generic ID string (for rules, VLANs, backups, etc.).
    
    IDs should only contain alphanumeric characters, hyphens, and underscores.
    
    Args:
        id_value: ID string to validate
        
    Returns:
        True if valid ID, False otherwise
    """
    if not id_value or not isinstance(id_value, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, id_value)) and len(id_value) <= 128


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate pfSense configuration parameters.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    if 'host' not in config or not config['host']:
        errors.append("Missing required field: host")
    elif not validate_ip_address(config['host']) and not re.match(r'^[a-zA-Z0-9.-]+$', config['host']):
        errors.append("Invalid host format")
    
    if 'port' in config and not validate_port(config['port']):
        errors.append("Invalid port number")
    
    # Validate authentication
    has_api_key = 'api_key' in config and config['api_key']
    has_credentials = ('username' in config and config['username'] and 
                      'password' in config and config['password'])
    
    if not has_api_key and not has_credentials:
        errors.append("Either api_key or username/password must be provided")
    
    return errors
