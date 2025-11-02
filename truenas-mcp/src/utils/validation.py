"""Validation utilities for TrueNAS MCP server."""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


def validate_id(id_value: str) -> bool:
    """Validate ID string to prevent path traversal attacks.
    
    IDs should only contain alphanumeric characters, hyphens, underscores, and dots.
    This prevents path traversal attacks like '../' in URL construction.
    
    Args:
        id_value: ID string to validate (pool_id, dataset_id, etc.)
        
    Returns:
        True if valid ID, False otherwise
    """
    if not id_value or not isinstance(id_value, str):
        return False
    
    # Reject path traversal attempts
    if '..' in id_value or '/' in id_value or '\\' in id_value:
        logger.warning(f"Rejected ID with path traversal characters: {id_value}")
        return False
    
    # Only allow alphanumeric, hyphens, underscores, and dots
    # Dots are intentionally allowed (e.g., for pool names like 'pool.name'), but slashes and path separators are explicitly forbidden to prevent path construction abuse. No special shell characters allowed.
    pattern = r'^[a-zA-Z0-9._-]+$'
    is_valid = bool(re.match(pattern, id_value)) and len(id_value) <= 255
    
    if not is_valid:
        logger.warning(f"Rejected invalid ID format: {id_value}")
    
    return is_valid


def validate_dataset_name(name: str) -> bool:
    """Validate dataset name format.
    
    Dataset names can contain alphanumeric characters, hyphens, underscores, and forward slashes
    for hierarchy, but should not contain path traversal sequences.
    
    Args:
        name: Dataset name to validate
        
    Returns:
        True if valid dataset name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Reject path traversal attempts
    if '..' in name:
        logger.warning(f"Rejected dataset name with path traversal: {name}")
        return False
    
    # Prevent absolute path references
    if name.startswith('/') or name.startswith('\\'):
        logger.warning(f"Rejected dataset name with absolute path: {name}")
        return False
    
    # Dataset names can have hierarchy with slashes but no special characters
    # Example: pool/dataset or pool/parent/child
    pattern = r'^[a-zA-Z0-9._/-]+$'
    is_valid = bool(re.match(pattern, name)) and len(name) <= 512
    
    if not is_valid:
        logger.warning(f"Rejected invalid dataset name: {name}")
    
    return is_valid


class TrueNASConfigValidator(BaseModel):
    """Validator for TrueNAS configuration."""
    host: str = Field(..., description="TrueNAS host address")
    port: int = Field(443, ge=1, le=65535, description="TrueNAS port")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    class Config:
        extra = "forbid"


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TrueNAS configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        validator = TrueNASConfigValidator(**config)
        return validator.dict()
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ValueError(f"Invalid configuration: {e}")


def validate_api_response(response: Any, expected_type: Optional[type] = None) -> bool:
    """Validate API response.
    
    Args:
        response: API response to validate
        expected_type: Expected type of response
        
    Returns:
        True if response is valid, False otherwise
    """
    if response is None:
        logger.warning("API response is None")
        return False
    
    if expected_type and not isinstance(response, expected_type):
        logger.warning(f"API response type mismatch: expected {expected_type}, got {type(response)}")
        return False
    
    return True


def validate_pool_config(pool_data: Dict[str, Any]) -> bool:
    """Validate storage pool configuration.
    
    Args:
        pool_data: Pool configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["name", "disks", "raid_type"]
    
    for field in required_fields:
        if field not in pool_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate RAID type
    valid_raid_types = ["mirror", "stripe", "raidz1", "raidz2", "raidz3"]
    if pool_data["raid_type"] not in valid_raid_types:
        logger.error(f"Invalid RAID type: {pool_data['raid_type']}")
        return False
    
    # Validate disks
    if not isinstance(pool_data["disks"], list) or len(pool_data["disks"]) == 0:
        logger.error("Disks must be a non-empty list")
        return False
    
    return True


def validate_dataset_config(dataset_data: Dict[str, Any]) -> bool:
    """Validate dataset configuration.
    
    Args:
        dataset_data: Dataset configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["name", "pool", "type"]
    
    for field in required_fields:
        if field not in dataset_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate dataset type
    valid_types = ["FILESYSTEM", "VOLUME"]
    if dataset_data["type"] not in valid_types:
        logger.error(f"Invalid dataset type: {dataset_data['type']}")
        return False
    
    return True


def validate_user_config(user_data: Dict[str, Any]) -> bool:
    """Validate user configuration.
    
    Args:
        user_data: User configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ["username", "full_name", "password"]
    
    for field in required_fields:
        if field not in user_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate username format
    username = user_data["username"]
    if not username or len(username) < 1:
        logger.error("Username cannot be empty")
        return False
    
    # Validate password strength (basic)
    password = user_data["password"]
    if not password or len(password) < 8:
        logger.error("Password must be at least 8 characters long")
        return False
    
    return True


def validate_network_config(network_data: Dict[str, Any]) -> bool:
    """Validate network configuration.
    
    Args:
        network_data: Network configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Validate IP address format (basic)
    if "ip_address" in network_data:
        ip = network_data["ip_address"]
        if not _is_valid_ip_address(ip):
            logger.error(f"Invalid IP address: {ip}")
            return False
    
    # Validate netmask format (basic)
    if "netmask" in network_data:
        netmask = network_data["netmask"]
        if not _is_valid_ip_address(netmask):
            logger.error(f"Invalid netmask: {netmask}")
            return False
    
    # Validate MTU
    if "mtu" in network_data:
        mtu = network_data["mtu"]
        if not isinstance(mtu, int) or mtu < 68 or mtu > 9000:
            logger.error(f"Invalid MTU: {mtu}")
            return False
    
    return True


def _is_valid_ip_address(ip: str) -> bool:
    """Check if string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except Exception:
        return False


def sanitize_input(input_data: Union[str, Dict[str, object], List[object], object]) -> Union[str, Dict[str, object], List[object], object]:
    """Sanitize input data to prevent injection attacks.
    
    Enhanced sanitization that removes dangerous characters, control characters,
    and escapes HTML entities.
    
    Args:
        input_data: Input data to sanitize
        
    Returns:
        Sanitized input data
    """
    if isinstance(input_data, str):
        # Remove null bytes
        cleaned = input_data.replace('\x00', '')
        
        # Remove other control characters except newlines and tabs
        cleaned = ''.join(
            char for char in cleaned 
            if char in ('\n', '\t') or ord(char) >= 32
        )
        
        # Remove potentially dangerous characters for command injection
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '\r']
        for char in dangerous_chars:
            cleaned = cleaned.replace(char, '')
        
        # Remove path traversal sequences
        cleaned = cleaned.replace('..', '')
        
        return cleaned.strip()
    
    elif isinstance(input_data, dict):
        return {key: sanitize_input(value) for key, value in input_data.items()}
    
    elif isinstance(input_data, list):
        return [sanitize_input(item) for item in input_data]
    
    else:
        return input_data


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS attacks.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    import html as html_module
    
    if not text or not isinstance(text, str):
        return ""
    
    return html_module.escape(text)


def coerce_and_validate_int(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None, param_name: str = "value") -> int:
    """Coerce value to integer and validate bounds.
    
    Args:
        value: Value to coerce and validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        param_name: Parameter name for error messages
        
    Returns:
        Validated integer value
        
    Raises:
        ValueError: If value cannot be coerced or is out of bounds
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{param_name} must be a valid integer, got: {value}")
    
    if min_val is not None and int_value < min_val:
        raise ValueError(f"{param_name} must be at least {min_val}, got: {int_value}")
    
    if max_val is not None and int_value > max_val:
        raise ValueError(f"{param_name} must be at most {max_val}, got: {int_value}")
    
    return int_value


def coerce_and_validate_bool(value: Any, param_name: str = "value") -> bool:
    """Coerce value to boolean.
    
    Args:
        value: Value to coerce (accepts bool, int, str)
        param_name: Parameter name for error messages
        
    Returns:
        Boolean value
        
    Raises:
        ValueError: If value cannot be coerced to boolean
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, int):
        return value != 0
    
    if isinstance(value, str):
        lower_val = value.lower().strip()
        if lower_val in ('true', '1', 'yes', 'on'):
            return True
        elif lower_val in ('false', '0', 'no', 'off'):
            return False
    
    raise ValueError(f"{param_name} must be a valid boolean, got: {value}")


def validate_string_length(value: str, min_length: int = 0, max_length: int = 255, param_name: str = "value") -> str:
    """Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        param_name: Parameter name for error messages
        
    Returns:
        Validated string
        
    Raises:
        ValueError: If string length is invalid
    """
    if not isinstance(value, str):
        raise ValueError(f"{param_name} must be a string, got: {type(value)}")
    
    if len(value) < min_length:
        raise ValueError(f"{param_name} must be at least {min_length} characters, got: {len(value)}")
    
    if len(value) > max_length:
        raise ValueError(f"{param_name} must be at most {max_length} characters, got: {len(value)}")
    
    return value


def validate_permissions(permissions: Dict[str, Any]) -> bool:
    """Validate permissions object.
    
    Args:
        permissions: Permissions object to validate
        
    Returns:
        True if permissions are valid, False otherwise
    """
    if not isinstance(permissions, dict):
        logger.error("Permissions must be a dictionary")
        return False
    
    # Add specific permission validation logic here
    # This is a placeholder for future implementation
    
    return True
