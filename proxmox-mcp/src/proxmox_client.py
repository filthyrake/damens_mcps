"""Proxmox API client for interacting with Proxmox VE."""

import asyncio
from typing import Any, Dict, List, Optional, Union

import httpx
from proxmoxer import ProxmoxAPI

from .utils.logging import get_logger
from .utils.validation import (
    validate_vm_config,
    validate_container_config,
    validate_vmid,
    validate_node_name,
    validate_storage_name,
    validate_network_config
)

logger = get_logger(__name__)


class ProxmoxClient:
    """Client for interacting with Proxmox VE API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Proxmox client.
        
        Args:
            config: Configuration dictionary containing Proxmox connection details
        """
        self.host = config.get("host")
        self.port = config.get("port", 8006)
        self.protocol = config.get("protocol", "https")
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_token = config.get("api_token")
        self.realm = config.get("realm", "pve")
        self.verify_ssl = config.get("verify_ssl", True)
        
        # Initialize Proxmox API connection
        self._init_proxmox_connection()
    
    def _init_proxmox_connection(self) -> None:
        """Initialize the Proxmox API connection."""
        try:
            if self.api_token:
                # Use API token authentication
                self.proxmox = ProxmoxAPI(
                    host=self.host,
                    port=self.port,
                    token_name=self.username,
                    token_value=self.api_token,
                    verify_ssl=self.verify_ssl
                )
            else:
                # Use username/password authentication
                self.proxmox = ProxmoxAPI(
                    host=self.host,
                    port=self.port,
                    user=f"{self.username}@{self.realm}",
                    password=self.password,
                    verify_ssl=self.verify_ssl
                )
            
            logger.info(f"Proxmox connection initialized to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Proxmox connection: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Proxmox.
        
        Returns:
            Connection test result
        """
        try:
            # Get version info to test connection
            version = self.proxmox.version.get()
            return {
                "status": "success",
                "version": version,
                "message": "Connection successful"
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Connection failed"
            }
    
    # Virtual Machine Methods
    
    async def list_vms(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all virtual machines.
        
        Args:
            node: Optional node name to filter by
            
        Returns:
            List of VM information
        """
        try:
            if node:
                validate_node_name(node)
                vms = self.proxmox.nodes(node).qemu.get()
            else:
                # Get VMs from all nodes
                vms = []
                nodes = self.proxmox.nodes.get()
                for node_info in nodes:
                    node_name = node_info["node"]
                    node_vms = self.proxmox.nodes(node_name).qemu.get()
                    for vm in node_vms:
                        vm["node"] = node_name
                    vms.extend(node_vms)
            
            return vms
        except Exception as e:
            logger.error(f"Failed to list VMs: {e}")
            raise
    
    async def get_vm_info(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Get detailed information about a virtual machine.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            VM information
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            vm_info = self.proxmox.nodes(node).qemu(vmid_int).status.current.get()
            vm_config = self.proxmox.nodes(node).qemu(vmid_int).config.get()
            
            return {
                "status": vm_info,
                "config": vm_config,
                "node": node,
                "vmid": vmid_int
            }
        except Exception as e:
            logger.error(f"Failed to get VM info for {vmid} on {node}: {e}")
            raise
    
    async def create_vm(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new virtual machine.
        
        Args:
            config: VM configuration
            
        Returns:
            Creation result
        """
        try:
            validated_config = validate_vm_config(config)
            
            # Generate next available VMID
            node = validated_config["node"]
            validate_node_name(node)
            
            next_id = self.proxmox.cluster.nextid.get()
            
            # Prepare VM creation parameters
            vm_params = {
                "vmid": next_id,
                "name": validated_config["name"],
                "cores": validated_config["cores"],
                "memory": validated_config["memory"],
                "sockets": 1,
                "net0": f"virtio,bridge={validated_config['bridge']}",
                "scsi0": f"{validated_config['storage']}:{validated_config['disk_size']}"
            }
            
            # Create the VM
            result = self.proxmox.nodes(node).qemu.post(**vm_params)
            
            return {
                "status": "success",
                "vmid": next_id,
                "node": node,
                "message": f"VM {validated_config['name']} created successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to create VM: {e}")
            raise
    
    async def start_vm(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Start a virtual machine.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Start operation result
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            result = self.proxmox.nodes(node).qemu(vmid_int).status.start.post()
            
            return {
                "status": "success",
                "vmid": vmid_int,
                "node": node,
                "message": f"VM {vmid_int} started successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to start VM {vmid} on {node}: {e}")
            raise
    
    async def stop_vm(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Stop a virtual machine.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Stop operation result
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            result = self.proxmox.nodes(node).qemu(vmid_int).status.stop.post()
            
            return {
                "status": "success",
                "vmid": vmid_int,
                "node": node,
                "message": f"VM {vmid_int} stopped successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to stop VM {vmid} on {node}: {e}")
            raise
    
    async def shutdown_vm(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Shutdown a virtual machine gracefully.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Shutdown operation result
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            result = self.proxmox.nodes(node).qemu(vmid_int).status.shutdown.post()
            
            return {
                "status": "success",
                "vmid": vmid_int,
                "node": node,
                "message": f"VM {vmid_int} shutdown successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to shutdown VM {vmid} on {node}: {e}")
            raise
    
    async def delete_vm(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Delete a virtual machine.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Delete operation result
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            result = self.proxmox.nodes(node).qemu(vmid_int).delete()
            
            return {
                "status": "success",
                "vmid": vmid_int,
                "node": node,
                "message": f"VM {vmid_int} deleted successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to delete VM {vmid} on {node}: {e}")
            raise
    
    # Container Methods
    
    async def list_containers(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all containers.
        
        Args:
            node: Optional node name to filter by
            
        Returns:
            List of container information
        """
        try:
            if node:
                validate_node_name(node)
                containers = self.proxmox.nodes(node).lxc.get()
            else:
                # Get containers from all nodes
                containers = []
                nodes = self.proxmox.nodes.get()
                for node_info in nodes:
                    node_name = node_info["node"]
                    node_containers = self.proxmox.nodes(node_name).lxc.get()
                    for container in node_containers:
                        container["node"] = node_name
                    containers.extend(node_containers)
            
            return containers
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise
    
    async def get_container_info(self, node: str, vmid: Union[int, str]) -> Dict[str, Any]:
        """Get detailed information about a container.
        
        Args:
            node: Node name
            vmid: Container ID
            
        Returns:
            Container information
        """
        try:
            validate_node_name(node)
            vmid_int = validate_vmid(vmid)
            
            container_info = self.proxmox.nodes(node).lxc(vmid_int).status.current.get()
            container_config = self.proxmox.nodes(node).lxc(vmid_int).config.get()
            
            return {
                "status": container_info,
                "config": container_config,
                "node": node,
                "vmid": vmid_int
            }
        except Exception as e:
            logger.error(f"Failed to get container info for {vmid} on {node}: {e}")
            raise
    
    async def create_container(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new container.
        
        Args:
            config: Container configuration
            
        Returns:
            Creation result
        """
        try:
            validated_config = validate_container_config(config)
            
            # Generate next available VMID
            node = validated_config["node"]
            validate_node_name(node)
            
            next_id = self.proxmox.cluster.nextid.get()
            
            # Prepare container creation parameters
            container_params = {
                "vmid": next_id,
                "hostname": validated_config["name"],
                "ostemplate": validated_config["ostemplate"],
                "cores": validated_config["cores"],
                "memory": validated_config["memory"],
                "storage": validated_config["storage"],
                "rootfs": f"{validated_config['storage']}:{validated_config['disk_size']}"
            }
            
            if validated_config.get("password"):
                container_params["password"] = validated_config["password"]
            
            if validated_config.get("ssh_keys"):
                container_params["ssh-public-keys"] = validated_config["ssh_keys"]
            
            # Create the container
            result = self.proxmox.nodes(node).lxc.post(**container_params)
            
            return {
                "status": "success",
                "vmid": next_id,
                "node": node,
                "message": f"Container {validated_config['name']} created successfully",
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    # Storage Methods
    
    async def list_storage(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all storage pools.
        
        Args:
            node: Optional node name to filter by
            
        Returns:
            List of storage information
        """
        try:
            if node:
                validate_node_name(node)
                storage = self.proxmox.nodes(node).storage.get()
            else:
                # Get storage from all nodes
                storage = []
                nodes = self.proxmox.nodes.get()
                for node_info in nodes:
                    node_name = node_info["node"]
                    node_storage = self.proxmox.nodes(node_name).storage.get()
                    for st in node_storage:
                        st["node"] = node_name
                    storage.extend(node_storage)
            
            return storage
        except Exception as e:
            logger.error(f"Failed to list storage: {e}")
            raise
    
    # Node Methods
    
    async def list_nodes(self) -> List[Dict[str, Any]]:
        """List all nodes in the cluster.
        
        Returns:
            List of node information
        """
        try:
            nodes = self.proxmox.nodes.get()
            return nodes
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            raise
    
    async def get_node_info(self, node: str) -> Dict[str, Any]:
        """Get detailed information about a node.
        
        Args:
            node: Node name
            
        Returns:
            Node information
        """
        try:
            validate_node_name(node)
            
            node_info = self.proxmox.nodes(node).status.get()
            return node_info
        except Exception as e:
            logger.error(f"Failed to get node info for {node}: {e}")
            raise
    
    # System Methods
    
    async def get_version(self) -> Dict[str, Any]:
        """Get Proxmox version information.
        
        Returns:
            Version information
        """
        try:
            version = self.proxmox.version.get()
            return version
        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            raise
    
    async def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status information.
        
        Returns:
            Cluster status
        """
        try:
            status = self.proxmox.cluster.status.get()
            return status
        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            raise
