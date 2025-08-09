# pfSense MCP Server - Implemented Tools

This document lists all the tools currently implemented in the pfSense MCP server.

## Core Features
- The server uses the working pfSense 2.8.0 API v2 endpoints
- SSL certificate verification can be disabled for self-signed certificates
- Supports both API key and username/password authentication
- Comprehensive error handling and fallback responses

## System Management Tools

### `test_connection`
- **Description**: Test connection to pfSense
- **Parameters**: None
- **Endpoint**: Multiple fallback endpoints for compatibility

### `get_system_info`
- **Description**: Get system information and version
- **Parameters**: None
- **Endpoint**: `/api/v2/system/version` + `/api/v2/status/system`

### `get_version`
- **Description**: Get pfSense version
- **Parameters**: None
- **Endpoint**: `/api/v2/system/version`

### `get_system_health`
- **Description**: Get system health and status
- **Parameters**: None
- **Endpoint**: `/api/v2/status/system` + `/api/v2/status/services`

### `get_system_logs`
- **Description**: Get system logs
- **Parameters**: `limit` (integer, default: 100)
- **Endpoint**: `/api/v1/system/log`

## Network Interface Tools

### `get_interfaces`
- **Description**: Get network interfaces information
- **Parameters**: None
- **Endpoint**: `/api/v2/interfaces` + `/api/v2/status/interfaces`

### `get_interface_status`
- **Description**: Get detailed interface status information
- **Parameters**: None
- **Endpoint**: `/api/v2/status/interfaces`

### `get_arp_table`
- **Description**: Get ARP table entries
- **Parameters**: None
- **Endpoint**: `/api/v2/diagnostics/arp_table`

### `clear_arp_table`
- **Description**: Clear all ARP table entries
- **Parameters**: None
- **Endpoint**: `/api/v2/diagnostics/arp_table` (DELETE)

### `delete_arp_entry`
- **Description**: Delete specific ARP table entry
- **Parameters**: `ip_address` (string, required)
- **Endpoint**: `/api/v2/diagnostics/arp_table/{ip}` (DELETE)

## Firewall Management Tools

### `get_firewall_rules`
- **Description**: Get firewall rules and aliases
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/aliases`

### `get_firewall_aliases`
- **Description**: Get firewall aliases configuration
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/aliases`

### `get_firewall_logs`
- **Description**: Get firewall logs
- **Parameters**: `limit` (integer, default: 100)
- **Endpoint**: `/api/v1/firewall/log`

### `get_firewall_schedules`
- **Description**: Get firewall schedules
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/schedules`

### `get_firewall_states`
- **Description**: Get firewall states
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/states`

## NAT (Network Address Translation) Tools

### `get_nat_outbound_mappings`
- **Description**: Get NAT outbound mappings
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/nat/outbound/mappings`

### `get_nat_port_forwarding`
- **Description**: Get NAT port forwarding rules
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/nat/port_forward`

### `get_nat_one_to_one_mappings`
- **Description**: Get NAT one-to-one mappings
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/nat/one_to_one/mappings`

## Traffic Shaping Tools

### `get_traffic_shaper`
- **Description**: Get traffic shaper configuration
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/traffic_shaper`

### `get_traffic_shapers`
- **Description**: Get all traffic shapers
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/traffic_shapers`

### `get_traffic_shaper_limiters`
- **Description**: Get traffic shaper limiters
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/traffic_shaper/limiters`

### `get_traffic_shaper_queues`
- **Description**: Get traffic shaper queues
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/traffic_shaper/queue`

## Virtual IP Management Tools

### `get_virtual_ips`
- **Description**: Get virtual IP addresses
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/virtual_ips`

### `get_virtual_ip`
- **Description**: Get specific virtual IP configuration
- **Parameters**: `interface` (string, optional)
- **Endpoint**: `/api/v2/firewall/virtual_ip` or `/api/v2/firewall/virtual_ip/{interface}`

### `apply_virtual_ip_changes`
- **Description**: Apply virtual IP configuration changes
- **Parameters**: None
- **Endpoint**: `/api/v2/firewall/virtual_ip/apply` (POST)

## Service Management Tools

### `get_services`
- **Description**: Get running services information
- **Parameters**: None
- **Endpoint**: `/api/v2/status/services`

### `get_service_status`
- **Description**: Get detailed service status information
- **Parameters**: None
- **Endpoint**: `/api/v2/status/services`

## DHCP Tools

### `get_dhcp_leases`
- **Description**: Get DHCP lease information
- **Parameters**: None
- **Endpoint**: `/api/v2/dhcp/leases` (with fallback to `/api/v2/dhcp/status`)

## VPN Tools

### `get_vpn_status`
- **Description**: Get VPN connection status
- **Parameters**: None
- **Endpoint**: Available via web interface (API endpoint may vary)

## Notes

- All tools include comprehensive error handling with fallback responses
- Tools that don't have confirmed working API endpoints return informative messages
- The server gracefully handles API failures and provides meaningful error messages
- SSL certificate verification can be disabled for self-signed certificates
- Both API key and username/password authentication are supported
