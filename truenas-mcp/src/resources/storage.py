"""Storage resource handler for TrueNAS MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import CallToolRequest, CallToolResult, Tool

from .base import BaseResource
from ..exceptions import TrueNASAPIError, TrueNASError

logger = logging.getLogger(__name__)


class StorageResource(BaseResource):
    """Handler for storage-related operations."""

    def get_tools(self) -> List[Tool]:
        """Get list of storage tools.
        
        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="truenas_storage_get_pools",
                description="Get all storage pools",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_storage_get_pool",
                description="Get specific storage pool by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {
                            "type": "string",
                            "description": "Storage pool ID"
                        }
                    },
                    "required": ["pool_id"]
                }
            ),
            Tool(
                name="truenas_storage_create_pool",
                description="Create a new storage pool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pool name"
                        },
                        "disks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of disk names to use"
                        },
                        "raid_type": {
                            "type": "string",
                            "description": "RAID type (mirror, stripe, raidz1, raidz2, raidz3)"
                        }
                    },
                    "required": ["name", "disks", "raid_type"]
                }
            ),
            Tool(
                name="truenas_storage_delete_pool",
                description="Delete a storage pool. DESTRUCTIVE OPERATION - requires explicit confirmation via 'confirm' parameter set to true.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {
                            "type": "string",
                            "description": "Storage pool ID"
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be set to true to confirm this destructive operation"
                        }
                    },
                    "required": ["pool_id"]
                }
            ),
            Tool(
                name="truenas_storage_get_datasets",
                description="Get datasets, optionally filtered by pool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {
                            "type": "string",
                            "description": "Filter by pool ID"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="truenas_storage_create_dataset",
                description="Create a new dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Dataset name"
                        },
                        "pool": {
                            "type": "string",
                            "description": "Parent pool name"
                        },
                        "type": {
                            "type": "string",
                            "description": "Dataset type (FILESYSTEM, VOLUME)",
                            "enum": ["FILESYSTEM", "VOLUME"]
                        },
                        "compression": {
                            "type": "string",
                            "description": "Compression algorithm"
                        },
                        "encryption": {
                            "type": "boolean",
                            "description": "Enable encryption"
                        }
                    },
                    "required": ["name", "pool", "type"]
                }
            ),
            Tool(
                name="truenas_storage_delete_dataset",
                description="Delete a dataset. DESTRUCTIVE OPERATION - requires explicit confirmation via 'confirm' parameter set to true.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "Dataset ID"
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be set to true to confirm this destructive operation"
                        }
                    },
                    "required": ["dataset_id"]
                }
            ),
            Tool(
                name="truenas_storage_get_snapshots",
                description="Get snapshots, optionally filtered by dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "Filter by dataset ID"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="truenas_storage_create_snapshot",
                description="Create a new snapshot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "Dataset ID to snapshot"
                        },
                        "name": {
                            "type": "string",
                            "description": "Snapshot name"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Recursively snapshot child datasets"
                        }
                    },
                    "required": ["dataset_id", "name"]
                }
            ),
            Tool(
                name="truenas_storage_delete_snapshot",
                description="Delete a snapshot. DESTRUCTIVE OPERATION - requires explicit confirmation via 'confirm' parameter set to true.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "Snapshot ID"
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be set to true to confirm this destructive operation"
                        }
                    },
                    "required": ["snapshot_id"]
                }
            ),
            Tool(
                name="truenas_storage_get_replication_tasks",
                description="Get replication tasks",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="truenas_storage_create_replication_task",
                description="Create a new replication task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Task name"
                        },
                        "source_dataset": {
                            "type": "string",
                            "description": "Source dataset"
                        },
                        "target_dataset": {
                            "type": "string",
                            "description": "Target dataset"
                        },
                        "schedule": {
                            "type": "string",
                            "description": "Replication schedule (cron format)"
                        }
                    },
                    "required": ["name", "source_dataset", "target_dataset"]
                }
            ),
        ]
    
    async def handle_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle storage tool calls.
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call result
        """
        tool_name = request.name
        params = request.arguments or {}
        
        try:
            if tool_name == "truenas_storage_get_pools":
                return await self._get_pools()
            elif tool_name == "truenas_storage_get_pool":
                return await self._get_pool(params)
            elif tool_name == "truenas_storage_create_pool":
                return await self._create_pool(params)
            elif tool_name == "truenas_storage_delete_pool":
                return await self._delete_pool(params)
            elif tool_name == "truenas_storage_get_datasets":
                return await self._get_datasets(params)
            elif tool_name == "truenas_storage_create_dataset":
                return await self._create_dataset(params)
            elif tool_name == "truenas_storage_delete_dataset":
                return await self._delete_dataset(params)
            elif tool_name == "truenas_storage_get_snapshots":
                return await self._get_snapshots(params)
            elif tool_name == "truenas_storage_create_snapshot":
                return await self._create_snapshot(params)
            elif tool_name == "truenas_storage_delete_snapshot":
                return await self._delete_snapshot(params)
            elif tool_name == "truenas_storage_get_replication_tasks":
                return await self._get_replication_tasks()
            elif tool_name == "truenas_storage_create_replication_task":
                return await self._create_replication_task(params)
            else:
                return self._create_error_result(f"Unknown storage tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in storage tool {tool_name}: {e}")
            return self._create_error_result(str(e))
    
    async def _get_pools(self) -> CallToolResult:
        """Get all storage pools."""
        try:
            pools = await self.client.get_pools()
            return self._create_success_result(pools)
        except Exception as e:
            return self._create_error_result(f"Failed to get pools: {e}")
    
    async def _get_pool(self, params: Dict[str, Any]) -> CallToolResult:
        """Get specific storage pool."""
        try:
            self._validate_required_params(params, ["pool_id"])
            pool_id = params["pool_id"]
            pool = await self.client.get_pool(pool_id)
            return self._create_success_result(pool)
        except Exception as e:
            return self._create_error_result(f"Failed to get pool: {e}")
    
    async def _create_pool(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new storage pool."""
        try:
            self._validate_required_params(params, ["name", "disks", "raid_type"])
            
            pool_data = {
                "name": params["name"],
                "disks": params["disks"],
                "raid_type": params["raid_type"]
            }
            
            result = await self.client.create_pool(pool_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create pool: {e}")
    
    async def _delete_pool(self, params: Dict[str, Any]) -> CallToolResult:
        """Delete a storage pool."""
        try:
            self._validate_required_params(params, ["pool_id"])
            pool_id = params["pool_id"]
            confirm = self._safe_get_param(params, "confirm", False)
            
            # Require explicit confirmation for destructive operation
            if not confirm:
                return self._create_error_result(
                    "Pool deletion requires explicit confirmation. "
                    "Set 'confirm' parameter to true to proceed. "
                    "WARNING: This is a destructive operation that cannot be undone."
                )
            
            # Validate pool exists before attempting deletion
            try:
                await self.client.get_pool(pool_id)
            except (TrueNASAPIError, TrueNASError) as e:
                return self._create_error_result(f"Pool '{pool_id}' not found or inaccessible: {e}")
            
            # Execute the actual deletion via API
            result = await self.client.delete_pool(pool_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to delete pool: {e}")
    
    async def _get_datasets(self, params: Dict[str, Any]) -> CallToolResult:
        """Get datasets."""
        try:
            pool_id = self._safe_get_param(params, "pool_id")
            datasets = await self.client.get_datasets(pool_id)
            return self._create_success_result(datasets)
        except Exception as e:
            return self._create_error_result(f"Failed to get datasets: {e}")
    
    async def _create_dataset(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new dataset."""
        try:
            self._validate_required_params(params, ["name", "pool", "type"])
            
            dataset_data = {
                "name": params["name"],
                "pool": params["pool"],
                "type": params["type"]
            }
            
            # Add optional parameters
            if "compression" in params:
                dataset_data["compression"] = params["compression"]
            if "encryption" in params:
                dataset_data["encryption"] = params["encryption"]
            
            result = await self.client.create_dataset(dataset_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create dataset: {e}")
    
    async def _delete_dataset(self, params: Dict[str, Any]) -> CallToolResult:
        """Delete a dataset."""
        try:
            self._validate_required_params(params, ["dataset_id"])
            dataset_id = params["dataset_id"]
            confirm = self._safe_get_param(params, "confirm", False)
            
            # Require explicit confirmation for destructive operation
            if not confirm:
                return self._create_error_result(
                    "Dataset deletion requires explicit confirmation. "
                    "Set 'confirm' parameter to true to proceed. "
                    "WARNING: This is a destructive operation that cannot be undone."
                )
            
            # Execute the actual deletion via API
            result = await self.client.delete_dataset(dataset_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to delete dataset: {e}")
    
    async def _get_snapshots(self, params: Dict[str, Any]) -> CallToolResult:
        """Get snapshots."""
        try:
            dataset_id = self._safe_get_param(params, "dataset_id")
            snapshots = await self.client.get_snapshots(dataset_id)
            return self._create_success_result(snapshots)
        except Exception as e:
            return self._create_error_result(f"Failed to get snapshots: {e}")
    
    async def _create_snapshot(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new snapshot."""
        try:
            self._validate_required_params(params, ["dataset_id", "name"])
            
            snapshot_data = {
                "dataset_id": params["dataset_id"],
                "name": params["name"]
            }
            
            if "recursive" in params:
                snapshot_data["recursive"] = params["recursive"]
            
            result = await self.client.create_snapshot(snapshot_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create snapshot: {e}")
    
    async def _delete_snapshot(self, params: Dict[str, Any]) -> CallToolResult:
        """Delete a snapshot."""
        try:
            self._validate_required_params(params, ["snapshot_id"])
            snapshot_id = params["snapshot_id"]
            confirm = self._safe_get_param(params, "confirm", False)
            
            # Require explicit confirmation for destructive operation
            if not confirm:
                return self._create_error_result(
                    "Snapshot deletion requires explicit confirmation. "
                    "Set 'confirm' parameter to true to proceed. "
                    "WARNING: This is a destructive operation that cannot be undone."
                )
            
            # Execute the actual deletion via API
            result = await self.client.delete_snapshot(snapshot_id)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to delete snapshot: {e}")
    
    async def _get_replication_tasks(self) -> CallToolResult:
        """Get replication tasks."""
        try:
            tasks = await self.client.get_replication_tasks()
            return self._create_success_result(tasks)
        except Exception as e:
            return self._create_error_result(f"Failed to get replication tasks: {e}")
    
    async def _create_replication_task(self, params: Dict[str, Any]) -> CallToolResult:
        """Create a new replication task."""
        try:
            self._validate_required_params(params, ["name", "source_dataset", "target_dataset"])
            
            task_data = {
                "name": params["name"],
                "source_dataset": params["source_dataset"],
                "target_dataset": params["target_dataset"]
            }
            
            if "schedule" in params:
                task_data["schedule"] = params["schedule"]
            
            result = await self.client.create_replication_task(task_data)
            return self._create_success_result(result)
        except Exception as e:
            return self._create_error_result(f"Failed to create replication task: {e}")
