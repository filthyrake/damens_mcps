"""Input validation utilities for Proxmox MCP Server."""

import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ValidationError, validator


class VMConfig(BaseModel):
    """Validation model for VM configuration."""
    
    name: str
    node: str
    cores: int = 1
    memory: int = 512
    storage: str = "local-lvm"
    disk_size: str = "10G"
    network_model: str = "virtio"
    bridge: str = "vmbr0"
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('VM name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @validator('cores')
    def validate_cores(cls, v):
        if v < 1 or v > 128:
            raise ValueError('CPU cores must be between 1 and 128')
        return v
    
    @validator('memory')
    def validate_memory(cls, v):
        if v < 64 or v > 1048576:  # 64MB to 1TB
            raise ValueError('Memory must be between 64MB and 1TB')
        return v
    
    @validator('disk_size')
    def validate_disk_size(cls, v):
        if not re.match(r'^\d+[KMGTP]?$', v):
            raise ValueError('Disk size must be in format: number[KMGTP] (e.g., 10G, 100M)')
        return v


class ContainerConfig(BaseModel):
    """Validation model for container configuration."""
    
    name: str
    node: str
    ostemplate: str
    cores: int = 1
    memory: int = 512
    storage: str = "local-lvm"
    disk_size: str = "10G"
    password: Optional[str] = None
    ssh_keys: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Container name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @validator('ostemplate')
    def validate_ostemplate(cls, v):
        if not v or not v.strip():
            raise ValueError('OS template is required')
        return v


def validate_vm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate VM configuration parameters.
    
    Args:
        config: VM configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        vm_config = VMConfig(**config)
        return vm_config.dict()
    except ValidationError as e:
        raise ValueError(f"Invalid VM configuration: {e}")


def validate_container_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate container configuration parameters.
    
    Args:
        config: Container configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        container_config = ContainerConfig(**config)
        return container_config.dict()
    except ValidationError as e:
        raise ValueError(f"Invalid container configuration: {e}")


def validate_vmid(vmid: Union[int, str]) -> int:
    """Validate VM/Container ID.
    
    Args:
        vmid: VM/Container ID
        
    Returns:
        Validated VM/Container ID as integer
        
    Raises:
        ValueError: If VMID is invalid
    """
    try:
        vmid_int = int(vmid)
        if vmid_int < 100 or vmid_int > 999999:
            raise ValueError("VMID must be between 100 and 999999")
        return vmid_int
    except (ValueError, TypeError):
        raise ValueError("VMID must be a valid integer")


def validate_node_name(node: str) -> str:
    """Validate node name.
    
    Args:
        node: Node name
        
    Returns:
        Validated node name
        
    Raises:
        ValueError: If node name is invalid
    """
    if not node or not re.match(r'^[a-zA-Z0-9\-_]+$', node):
        raise ValueError("Node name must contain only alphanumeric characters, hyphens, and underscores")
    return node


def validate_storage_name(storage: str) -> str:
    """Validate storage name.
    
    Args:
        storage: Storage name
        
    Returns:
        Validated storage name
        
    Raises:
        ValueError: If storage name is invalid
    """
    if not storage or not re.match(r'^[a-zA-Z0-9\-_]+$', storage):
        raise ValueError("Storage name must contain only alphanumeric characters, hyphens, and underscores")
    return storage


def validate_network_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate network configuration.
    
    Args:
        config: Network configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ['name', 'type']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Network configuration missing required field: {field}")
    
    if config['type'] not in ['bridge', 'bond', 'vlan']:
        raise ValueError("Network type must be one of: bridge, bond, vlan")
    
    return config
