"""Validation utilities for iDRAC MCP Server."""

import re
from typing import Dict, Any, Optional

from pydantic import BaseModel, field_validator


class IDracConfig(BaseModel):
    """Configuration model for iDRAC connection."""
    
    host: str
    port: int = 443
    protocol: str = "https"
    username: str
    password: str
    ssl_verify: bool = False
    ssl_cert_path: Optional[str] = None
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-\.]+$', v):
            raise ValueError('Host must contain only alphanumeric characters, hyphens, and dots')
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @field_validator('protocol')
    @classmethod
    def validate_protocol(cls, v):
        if v not in ['http', 'https']:
            raise ValueError('Protocol must be either http or https')
        return v


class PowerOperation(BaseModel):
    """Model for power operations."""
    
    operation: str
    force: bool = False
    timeout: int = 60
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        valid_operations = ['on', 'off', 'cycle', 'graceful_shutdown', 'force_off']
        if v not in valid_operations:
            raise ValueError(f'Operation must be one of: {", ".join(valid_operations)}')
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if not 10 <= v <= 300:
            raise ValueError('Timeout must be between 10 and 300 seconds')
        return v


class UserConfig(BaseModel):
    """Model for iDRAC user configuration."""
    
    username: str
    password: str
    privilege: str = "Administrator"
    enabled: bool = True
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        if len(v) < 3 or len(v) > 16:
            raise ValueError('Username must be between 3 and 16 characters')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @field_validator('privilege')
    @classmethod
    def validate_privilege(cls, v):
        valid_privileges = ['Administrator', 'Operator', 'ReadOnly']
        if v not in valid_privileges:
            raise ValueError(f'Privilege must be one of: {", ".join(valid_privileges)}')
        return v


def validate_idrac_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate iDRAC configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        validated_config = IDracConfig(**config)
        return validated_config.dict()
    except Exception as e:
        raise ValueError(f"Invalid iDRAC configuration: {e}")


def validate_power_operation(operation: Dict[str, Any]) -> Dict[str, Any]:
    """Validate power operation parameters.
    
    Args:
        operation: Operation parameters
        
    Returns:
        Validated operation parameters
        
    Raises:
        ValueError: If operation parameters are invalid
    """
    try:
        validated_operation = PowerOperation(**operation)
        return validated_operation.dict()
    except Exception as e:
        raise ValueError(f"Invalid power operation: {e}")


def validate_user_config(user_config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user configuration.
    
    Args:
        user_config: User configuration dictionary
        
    Returns:
        Validated user configuration
        
    Raises:
        ValueError: If user configuration is invalid
    """
    try:
        validated_config = UserConfig(**user_config)
        return validated_config.dict()
    except Exception as e:
        raise ValueError(f"Invalid user configuration: {e}")


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def validate_mac_address(mac: str) -> bool:
    """Validate MAC address format.
    
    Args:
        mac: MAC address string
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))


def validate_server_id(server_id: str) -> bool:
    """Validate server ID format.
    
    Server IDs should only contain alphanumeric characters, hyphens, and underscores.
    This prevents injection attacks and path traversal.
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not server_id or not isinstance(server_id, str):
        return False
    
    # Only allow alphanumeric, hyphens, and underscores
    # No special characters that could be used for injection
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, server_id)) and len(server_id) <= 128


def safe_get_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    """Safely get a field from a dictionary with existence checking.
    
    Useful for handling Redfish API responses where fields may not always exist.
    
    Args:
        data: Dictionary to get field from
        field: Field name to retrieve
        default: Default value if field doesn't exist
        
    Returns:
        Field value or default
    """
    if not isinstance(data, dict):
        return default
    
    return data.get(field, default)


def safe_get_nested_field(data: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    """Safely get a nested field from a dictionary with existence checking.
    
    Args:
        data: Dictionary to get nested field from
        *fields: Field path (e.g., 'a', 'b', 'c' for data['a']['b']['c'])
        default: Default value if field doesn't exist
        
    Returns:
        Field value or default
    """
    current = data
    
    for field in fields:
        if not isinstance(current, dict):
            return default
        
        current = current.get(field)
        if current is None:
            return default
    
    return current
