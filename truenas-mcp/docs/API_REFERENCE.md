# TrueNAS MCP Server API Reference

This document provides a comprehensive reference for all the tools and APIs available in the TrueNAS MCP Server.

## Table of Contents

- [System Tools](#system-tools)
- [Storage Tools](#storage-tools)
- [Network Tools](#network-tools)
- [Services Tools](#services-tools)
- [User Tools](#user-tools)
- [Error Handling](#error-handling)
- [Response Formats](#response-formats)

## System Tools

### truenas_system_get_info
Get detailed system information from TrueNAS.

**Parameters:** None

**Response:**
```json
{
  "hostname": "truenas-server",
  "platform": "TrueNAS-SCALE-25.04.2",
  "uptime": 1234567,
  "load_average": [1.2, 1.1, 0.9],
  "cpu_model": "Intel(R) Core(TM) i7-8700K",
  "memory_total": 16777216,
  "memory_used": 8388608
}
```

### truenas_system_get_version
Get TrueNAS version information.

**Parameters:** None

**Response:**
```json
{
  "version": "25.04.2",
  "buildtime": "2024-01-15T10:30:00Z",
  "fullversion": "TrueNAS-SCALE-25.04.2"
}
```

### truenas_system_get_health
Get system health status.

**Parameters:** None

**Response:**
```json
{
  "status": "HEALTHY",
  "issues": [],
  "checks": {
    "cpu": "OK",
    "memory": "OK",
    "storage": "OK",
    "network": "OK"
  }
}
```

### truenas_system_get_uptime
Get system uptime information.

**Parameters:** None

**Response:**
```json
{
  "uptime": 1234567,
  "boot_time": "2024-01-01T00:00:00Z",
  "formatted": "14 days, 6 hours, 56 minutes"
}
```

### truenas_system_get_stats
Get system statistics and metrics.

**Parameters:** None

**Response:**
```json
{
  "cpu_usage": 25.5,
  "memory_usage": 45.2,
  "disk_usage": 67.8,
  "network_rx": 1024000,
  "network_tx": 512000
}
```

### truenas_system_get_alerts
Get system alerts.

**Parameters:**
- `limit` (optional): Maximum number of alerts to return (integer)

**Response:**
```json
[
  {
    "id": 1,
    "level": "WARNING",
    "message": "Pool tank is 80% full",
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

### truenas_system_get_alert_classes
Get available alert classes.

**Parameters:** None

**Response:**
```json
[
  "System",
  "Storage",
  "Network",
  "Services",
  "Security"
]
```

## Storage Tools

### truenas_storage_get_pools
Get all storage pools.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "name": "tank",
    "status": "ONLINE",
    "size": 1099511627776,
    "used": 549755813888,
    "raid_type": "raidz1"
  }
]
```

### truenas_storage_get_pool
Get specific storage pool by ID.

**Parameters:**
- `pool_id` (required): Storage pool ID (string)

**Response:**
```json
{
  "id": 1,
  "name": "tank",
  "status": "ONLINE",
  "size": 1099511627776,
  "used": 549755813888,
  "raid_type": "raidz1",
  "disks": ["sda", "sdb", "sdc"]
}
```

### truenas_storage_create_pool
Create a new storage pool.

**Parameters:**
- `name` (required): Pool name (string)
- `disks` (required): List of disk names (array of strings)
- `raid_type` (required): RAID type (string, one of: mirror, stripe, raidz1, raidz2, raidz3)

**Response:**
```json
{
  "id": 2,
  "name": "new_pool",
  "status": "ONLINE",
  "message": "Pool created successfully"
}
```

### truenas_storage_delete_pool
Delete a storage pool.

**Parameters:**
- `pool_id` (required): Storage pool ID (string)
- `force` (optional): Force deletion (boolean, default: false)

**Response:**
```json
{
  "status": "deletion_scheduled",
  "pool_id": "1",
  "message": "Pool deletion has been scheduled"
}
```

### truenas_storage_get_datasets
Get datasets, optionally filtered by pool.

**Parameters:**
- `pool_id` (optional): Filter by pool ID (string)

**Response:**
```json
[
  {
    "id": 1,
    "name": "tank/documents",
    "type": "FILESYSTEM",
    "compression": "lz4",
    "encryption": false,
    "size": 1073741824
  }
]
```

### truenas_storage_create_dataset
Create a new dataset.

**Parameters:**
- `name` (required): Dataset name (string)
- `pool` (required): Parent pool name (string)
- `type` (required): Dataset type (string, one of: FILESYSTEM, VOLUME)
- `compression` (optional): Compression algorithm (string)
- `encryption` (optional): Enable encryption (boolean)

**Response:**
```json
{
  "id": 2,
  "name": "tank/new_dataset",
  "type": "FILESYSTEM",
  "message": "Dataset created successfully"
}
```

### truenas_storage_delete_dataset
Delete a dataset.

**Parameters:**
- `dataset_id` (required): Dataset ID (string)
- `recursive` (optional): Recursively delete child datasets (boolean, default: false)

**Response:**
```json
{
  "status": "deletion_scheduled",
  "dataset_id": "1",
  "message": "Dataset deletion has been scheduled"
}
```

### truenas_storage_get_snapshots
Get snapshots, optionally filtered by dataset.

**Parameters:**
- `dataset_id` (optional): Filter by dataset ID (string)

**Response:**
```json
[
  {
    "id": 1,
    "name": "tank/documents@snapshot-2024-01-15",
    "dataset": "tank/documents",
    "created": "2024-01-15T10:30:00Z",
    "size": 1073741824
  }
]
```

### truenas_storage_create_snapshot
Create a new snapshot.

**Parameters:**
- `dataset_id` (required): Dataset ID to snapshot (string)
- `name` (required): Snapshot name (string)
- `recursive` (optional): Recursively snapshot child datasets (boolean, default: false)

**Response:**
```json
{
  "id": 2,
  "name": "tank/documents@new-snapshot",
  "message": "Snapshot created successfully"
}
```

### truenas_storage_delete_snapshot
Delete a snapshot.

**Parameters:**
- `snapshot_id` (required): Snapshot ID (string)
- `recursive` (optional): Recursively delete child snapshots (boolean, default: false)

**Response:**
```json
{
  "status": "deletion_scheduled",
  "snapshot_id": "1",
  "message": "Snapshot deletion has been scheduled"
}
```

### truenas_storage_get_replication_tasks
Get replication tasks.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "name": "daily_backup",
    "source": "tank/documents",
    "target": "backup/documents",
    "schedule": "0 2 * * *",
    "status": "RUNNING"
  }
]
```

### truenas_storage_create_replication_task
Create a new replication task.

**Parameters:**
- `name` (required): Task name (string)
- `source_dataset` (required): Source dataset (string)
- `target_dataset` (required): Target dataset (string)
- `schedule` (optional): Replication schedule in cron format (string)

**Response:**
```json
{
  "id": 2,
  "name": "new_replication",
  "message": "Replication task created successfully"
}
```

## Network Tools

### truenas_network_get_interfaces
Get all network interfaces.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "name": "eth0",
    "type": "ETHERNET",
    "ip_address": "192.168.1.100",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "mtu": 1500,
    "status": "UP"
  }
]
```

### truenas_network_get_interface
Get specific network interface by ID.

**Parameters:**
- `interface_id` (required): Network interface ID (string)

**Response:**
```json
{
  "id": 1,
  "name": "eth0",
  "type": "ETHERNET",
  "ip_address": "192.168.1.100",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "mtu": 1500,
  "status": "UP",
  "mac_address": "00:11:22:33:44:55"
}
```

### truenas_network_update_interface
Update network interface configuration.

**Parameters:**
- `interface_id` (required): Network interface ID (string)
- `ip_address` (optional): IP address (string)
- `netmask` (optional): Subnet mask (string)
- `gateway` (optional): Gateway address (string)
- `mtu` (optional): MTU size (integer)

**Response:**
```json
{
  "id": 1,
  "name": "eth0",
  "message": "Interface updated successfully"
}
```

### truenas_network_get_routes
Get network routes.

**Parameters:** None

**Response:**
```json
[
  {
    "destination": "0.0.0.0/0",
    "gateway": "192.168.1.1",
    "interface": "eth0",
    "metric": 1
  }
]
```

### truenas_network_test_connectivity
Test network connectivity to a host.

**Parameters:**
- `host` (required): Host to test connectivity to (string)
- `port` (optional): Port to test (integer, default: 80)

**Response:**
```json
{
  "host": "8.8.8.8",
  "port": 80,
  "status": "connectivity_test_scheduled",
  "message": "Connectivity test to 8.8.8.8:80 has been scheduled"
}
```

## Services Tools

### truenas_services_get_all
Get all services.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "service": "smb",
    "state": "RUNNING",
    "enable": true,
    "pid": 1234
  }
]
```

### truenas_services_get_service
Get specific service by ID.

**Parameters:**
- `service_id` (required): Service ID (string)

**Response:**
```json
{
  "id": 1,
  "service": "smb",
  "state": "RUNNING",
  "enable": true,
  "pid": 1234,
  "config": {
    "workgroup": "WORKGROUP",
    "description": "TrueNAS SMB Server"
  }
}
```

### truenas_services_start_service
Start a service.

**Parameters:**
- `service_id` (required): Service ID (string)

**Response:**
```json
{
  "id": 1,
  "service": "smb",
  "state": "RUNNING",
  "message": "Service started successfully"
}
```

### truenas_services_stop_service
Stop a service.

**Parameters:**
- `service_id` (required): Service ID (string)

**Response:**
```json
{
  "id": 1,
  "service": "smb",
  "state": "STOPPED",
  "message": "Service stopped successfully"
}
```

### truenas_services_restart_service
Restart a service.

**Parameters:**
- `service_id` (required): Service ID (string)

**Response:**
```json
{
  "id": 1,
  "service": "smb",
  "state": "RUNNING",
  "message": "Service restarted successfully"
}
```

### truenas_services_get_smb_shares
Get SMB shares.

**Parameters:** None

**Response:**
```json
{
  "status": "not_implemented",
  "message": "SMB shares API endpoint not yet implemented"
}
```

### truenas_services_create_smb_share
Create a new SMB share.

**Parameters:**
- `name` (required): Share name (string)
- `path` (required): Path to share (string)
- `comment` (optional): Share comment (string)
- `readonly` (optional): Make share read-only (boolean, default: false)

**Response:**
```json
{
  "status": "creation_scheduled",
  "name": "documents",
  "path": "/mnt/tank/documents",
  "message": "SMB share creation has been scheduled"
}
```

### truenas_services_get_nfs_shares
Get NFS shares.

**Parameters:** None

**Response:**
```json
{
  "status": "not_implemented",
  "message": "NFS shares API endpoint not yet implemented"
}
```

### truenas_services_create_nfs_share
Create a new NFS share.

**Parameters:**
- `path` (required): Path to share (string)
- `hosts` (optional): Allowed hosts (array of strings)
- `readonly` (optional): Make share read-only (boolean, default: false)

**Response:**
```json
{
  "status": "creation_scheduled",
  "path": "/mnt/tank/documents",
  "message": "NFS share creation has been scheduled"
}
```

### truenas_services_get_iscsi_targets
Get iSCSI targets.

**Parameters:** None

**Response:**
```json
{
  "status": "not_implemented",
  "message": "iSCSI targets API endpoint not yet implemented"
}
```

### truenas_services_create_iscsi_target
Create a new iSCSI target.

**Parameters:**
- `name` (required): Target name (string)
- `alias` (optional): Target alias (string)

**Response:**
```json
{
  "status": "creation_scheduled",
  "name": "iqn.2024-01.com.truenas:target1",
  "message": "iSCSI target creation has been scheduled"
}
```

## User Tools

### truenas_users_get_all
Get all users.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "email": "admin@example.com",
    "uid": 1000,
    "gid": 1000,
    "home": "/home/admin",
    "shell": "/bin/bash"
  }
]
```

### truenas_users_get_user
Get specific user by ID.

**Parameters:**
- `user_id` (required): User ID (string)

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "full_name": "Administrator",
  "email": "admin@example.com",
  "uid": 1000,
  "gid": 1000,
  "home": "/home/admin",
  "shell": "/bin/bash",
  "groups": ["admin", "wheel"]
}
```

### truenas_users_create_user
Create a new user.

**Parameters:**
- `username` (required): Username (string)
- `full_name` (required): Full name (string)
- `password` (required): Password (string)
- `email` (optional): Email address (string)
- `shell` (optional): Shell (string, default: "/bin/bash")
- `home` (optional): Home directory (string)
- `groups` (optional): List of group names (array of strings)

**Response:**
```json
{
  "id": 2,
  "username": "newuser",
  "message": "User created successfully"
}
```

### truenas_users_update_user
Update user information.

**Parameters:**
- `user_id` (required): User ID (string)
- `full_name` (optional): Full name (string)
- `email` (optional): Email address (string)
- `shell` (optional): Shell (string)
- `home` (optional): Home directory (string)
- `groups` (optional): List of group names (array of strings)

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "message": "User updated successfully"
}
```

### truenas_users_delete_user
Delete a user.

**Parameters:**
- `user_id` (required): User ID (string)
- `force` (optional): Force deletion even if user has files (boolean, default: false)

**Response:**
```json
{
  "status": "deletion_scheduled",
  "user_id": "1",
  "message": "User deletion has been scheduled"
}
```

### truenas_users_get_groups
Get all groups.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "name": "admin",
    "gid": 1000,
    "members": ["admin"]
  }
]
```

### truenas_users_create_group
Create a new group.

**Parameters:**
- `name` (required): Group name (string)
- `gid` (optional): Group ID (integer)
- `members` (optional): List of usernames to add to group (array of strings)

**Response:**
```json
{
  "status": "creation_scheduled",
  "name": "newgroup",
  "message": "Group creation has been scheduled"
}
```

### truenas_users_get_user_permissions
Get user permissions.

**Parameters:**
- `user_id` (required): User ID (string)

**Response:**
```json
{
  "status": "not_implemented",
  "user_id": "1",
  "message": "User permissions API endpoint not yet implemented"
}
```

### truenas_users_set_user_permissions
Set user permissions.

**Parameters:**
- `user_id` (required): User ID (string)
- `permissions` (required): Permissions object (object)

**Response:**
```json
{
  "status": "permissions_update_scheduled",
  "user_id": "1",
  "message": "User permissions update has been scheduled"
}
```

## Error Handling

All tools return standardized error responses when something goes wrong:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Failed to connect to TrueNAS server"
    }
  ]
}
```

Common error scenarios:
- **Authentication failed**: Invalid API key or credentials
- **Connection failed**: Network issues or server unreachable
- **Validation error**: Invalid parameters provided
- **Permission denied**: Insufficient privileges for the operation
- **Resource not found**: Requested resource doesn't exist
- **Server error**: Internal TrueNAS server error

## Response Formats

All successful responses follow the MCP protocol format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Response data here"
    }
  ]
}
```

For complex data, the response is formatted as a readable string representation of the JSON data.

## Rate Limiting

The TrueNAS API has rate limiting to prevent abuse. The MCP server respects these limits and will return appropriate error messages if rate limits are exceeded.

## Security Notes

- All API keys and passwords are handled securely and not logged
- SSL certificate verification is enabled by default
- Input validation is performed on all parameters
- Audit logging is available for security-sensitive operations
