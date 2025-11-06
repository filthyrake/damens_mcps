"""Version information for Proxmox MCP Server."""

__version__ = "1.0.0"
__author__ = "Proxmox MCP Team"
__description__ = "Model Context Protocol server for Proxmox VE management"


def get_version() -> str:
    """Get the current version string.

    Returns:
        str: Version string in format 'X.Y.Z'
    """
    return __version__


def get_version_info() -> dict:
    """Get detailed version information.

    Returns:
        dict: Dictionary containing version, author, and description
    """
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
    }
