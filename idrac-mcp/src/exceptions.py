"""Custom exceptions for iDRAC MCP server.

This module defines the exception hierarchy for the iDRAC MCP server.
All custom exceptions inherit from IDracError to allow catching all
iDRAC-specific errors with a single except clause.
"""


class IDracError(Exception):
    """Base exception for all iDRAC MCP errors.

    All custom exceptions in the iDRAC MCP should inherit from this class
    to allow catching all iDRAC-specific errors with a single except clause.

    Example:
        try:
            client.get_system_info()
        except IDracError as e:
            logger.error(f"iDRAC operation failed: {e}")
    """
    pass


class IDracConnectionError(IDracError):
    """Raised when unable to establish connection to iDRAC server.

    Common causes:
        - iDRAC server is unreachable (network issues, wrong hostname/IP)
        - Firewall blocking connection
        - iDRAC service not running
        - Port mismatch (default: 443)

    Troubleshooting:
        - Verify iDRAC hostname/IP is correct
        - Test connectivity: ping <idrac-host>
        - Verify port is accessible: telnet <idrac-host> 443
        - Check firewall rules
        - Verify iDRAC web interface is accessible

    Example:
        try:
            client.connect()
        except IDracConnectionError as e:
            logger.error(f"Cannot reach iDRAC: {e}")
    """
    pass


class IDracAuthenticationError(IDracError):
    """Raised when authentication with iDRAC fails.

    Common causes:
        - Invalid username or password
        - Account locked out due to failed login attempts
        - User account disabled
        - Insufficient privileges for the operation
        - Expired credentials

    Troubleshooting:
        - Verify username and password are correct
        - Check if account is locked in iDRAC web interface
        - Verify account has appropriate privileges (Administrator, Operator, etc.)
        - Try logging into iDRAC web interface directly
        - Check if Active Directory/LDAP integration is causing issues

    Example:
        try:
            client.authenticate()
        except IDracAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
    """
    pass


class IDracAPIError(IDracError):
    """Raised when iDRAC API returns an error.

    This exception is raised when the API request completes but returns
    an error response. The error message typically contains details from
    the Redfish API response.

    Common causes:
        - Invalid API endpoint or method
        - Resource not found (wrong VMID, server ID, etc.)
        - Operation not supported on this iDRAC version
        - Server in wrong state for requested operation
        - API rate limiting

    Troubleshooting:
        - Check the error message for specific details
        - Verify the resource exists and is accessible
        - Check iDRAC version compatibility
        - Verify server power state allows the operation
        - Check iDRAC logs for additional details

    Example:
        try:
            client.set_power_state("on")
        except IDracAPIError as e:
            logger.error(f"API request failed: {e}")
    """
    pass


class IDracTimeoutError(IDracError):
    """Raised when a request to iDRAC times out.

    Common causes:
        - Network latency or connectivity issues
        - iDRAC server under heavy load
        - Long-running operation (firmware update, diagnostics)
        - Firewall dropping packets silently
        - iDRAC service unresponsive

    Troubleshooting:
        - Increase timeout value in configuration
        - Check network connectivity and latency
        - Verify iDRAC is responsive via web interface
        - Check iDRAC resource usage (CPU, memory)
        - For long operations, use async polling instead

    Example:
        try:
            client.get_system_info(timeout=30)
        except IDracTimeoutError as e:
            logger.error(f"Request timed out: {e}")
    """
    pass


class IDracValidationError(IDracError):
    """Raised when input validation fails.

    This exception is raised before making an API request when the
    input parameters fail validation. The error message contains
    details about which parameter(s) are invalid.

    Common causes:
        - Invalid server ID format
        - Invalid power operation type
        - Missing required parameters
        - Parameter values out of valid range
        - Invalid IP address or hostname format

    Troubleshooting:
        - Check the error message for specific parameter issues
        - Review valid values for the parameter
        - Ensure all required parameters are provided
        - Check parameter types (string vs int, etc.)

    Example:
        try:
            client.power_control(operation="invalid_op")
        except IDracValidationError as e:
            logger.error(f"Invalid parameters: {e}")
    """
    pass


class IDracConfigurationError(IDracError):
    """Raised when configuration is invalid.

    This exception is raised when the iDRAC client configuration
    is invalid or incomplete, typically during client initialization.

    Common causes:
        - Missing required configuration fields (host, username, password)
        - Invalid configuration file format
        - Configuration file not found
        - Environment variables not set
        - Invalid SSL certificate path

    Troubleshooting:
        - Verify config.json exists and is valid JSON
        - Check all required fields are present
        - Verify environment variables are set correctly
        - Check file permissions on configuration file
        - Validate SSL certificate path if specified

    Example:
        try:
            client = IDracClient(config)
        except IDracConfigurationError as e:
            logger.error(f"Invalid configuration: {e}")
    """
    pass
