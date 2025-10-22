"""Custom exceptions for pfSense MCP server."""


class PfSenseError(Exception):
    """Base exception for all pfSense-related errors."""
    pass


class PfSenseConnectionError(PfSenseError):
    """Raised when connection to pfSense fails."""
    pass


class PfSenseAuthenticationError(PfSenseError):
    """Raised when authentication with pfSense fails."""
    pass


class PfSenseAPIError(PfSenseError):
    """Raised when pfSense API returns an error."""
    pass


class PfSenseTimeoutError(PfSenseError):
    """Raised when a request to pfSense times out."""
    pass


class PfSenseValidationError(PfSenseError):
    """Raised when input validation fails."""
    pass


class PfSenseConfigurationError(PfSenseError):
    """Raised when configuration is invalid."""
    pass
