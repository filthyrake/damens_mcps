"""Custom exceptions for Proxmox MCP server."""


class ProxmoxError(Exception):
    """Base exception for all Proxmox-related errors."""
    pass


class ProxmoxConnectionError(ProxmoxError):
    """Raised when connection to Proxmox fails."""
    pass


class ProxmoxAuthenticationError(ProxmoxError):
    """Raised when authentication with Proxmox fails."""
    pass


class ProxmoxAPIError(ProxmoxError):
    """Raised when Proxmox API returns an error."""
    pass


class ProxmoxTimeoutError(ProxmoxError):
    """Raised when a request to Proxmox times out."""
    pass


class ProxmoxValidationError(ProxmoxError):
    """Raised when input validation fails."""
    pass


class ProxmoxConfigurationError(ProxmoxError):
    """Raised when configuration is invalid."""
    pass


class ProxmoxResourceNotFoundError(ProxmoxError):
    """Raised when a requested resource is not found."""
    pass
