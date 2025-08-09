"""Validation utilities for iDRAC MCP Server."""

import re
from typing import Dict, Any, Optional

from pydantic import BaseModel, validator


class IDracConfig(BaseModel):
    """Configuration model for iDRAC connection."""
    
    host: str
    port: int = 443
    protocol: str = "https"
    username: str
    password: str
    ssl_verify: bool = False
    ssl_cert_path: Optional[str] = None
    
    @validator('host')
    def validate_host(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-\.]+$', v):
            raise ValueError('Host must contain only alphanumeric characters, hyphens, and dots')
        return v
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('protocol')
    def validate_protocol(cls, v):
        if v not in ['http', 'https']:
            raise ValueError('Protocol must be either http or https')
        return v


class PowerOperation(BaseModel):
    """Model for power operations."""
    
    operation: str
    force: bool = False
    timeout: int = 60
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = ['on', 'off', 'cycle', 'graceful_shutdown', 'force_off']
        if v not in valid_operations:
            raise ValueError(f'Operation must be one of: {", ".join(valid_operations)}')
        return v
    
    @validator('timeout')
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
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        if len(v) < 3 or len(v) > 16:
            raise ValueError('Username must be between 3 and 16 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('privilege')
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
