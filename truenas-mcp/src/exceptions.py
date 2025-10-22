"""Custom exceptions for TrueNAS MCP server."""


class TrueNASError(Exception):
    """Base exception for all TrueNAS-related errors."""
    pass


class TrueNASConnectionError(TrueNASError):
    """Raised when connection to TrueNAS fails."""
    pass


class TrueNASAuthenticationError(TrueNASError):
    """Raised when authentication with TrueNAS fails."""
    pass


class TrueNASAPIError(TrueNASError):
    """Raised when TrueNAS API returns an error."""
    pass


class TrueNASTimeoutError(TrueNASError):
    """Raised when a request to TrueNAS times out."""
    pass


class TrueNASValidationError(TrueNASError):
    """Raised when input validation fails."""
    pass


class TrueNASConfigurationError(TrueNASError):
    """Raised when configuration is invalid."""
    pass


class TrueNASTokenError(TrueNASError):
    """Raised when token operations fail."""
    pass
