"""
Logging configuration for iDRAC MCP Server.

This module provides MCP-compatible logging that:
- Logs to stderr only (to avoid interfering with JSON-RPC protocol on stdout)
- Supports configurable log levels via environment variables
- Provides consistent formatting across all MCP servers
"""

import logging
import os
import sys
from typing import Optional


def setup_mcp_logging(
    name: str = "idrac-mcp",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Set up MCP-compatible logging configuration.

    For JSON-RPC MCP servers, logging MUST go to stderr only, as stdout
    is reserved for the protocol. This function configures logging to be
    MCP-compatible while still allowing debug output when needed.

    Args:
        name: Logger name (default: idrac-mcp)
        level: Logging level. If None, reads from MCP_LOG_LEVEL env var
               (default: CRITICAL to stay quiet unless debugging)
        log_file: Optional log file path for persistent logging
        log_format: Log message format

    Returns:
        Configured logger instance
    """
    # Get log level from environment or parameter
    if level is None:
        level = os.getenv('MCP_LOG_LEVEL', 'CRITICAL')

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.CRITICAL)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Prevent propagation to root logger (which might log to stdout)
    logger.propagate = False

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler - ALWAYS use stderr for MCP compatibility
    # stdout is reserved for JSON-RPC protocol messages
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.warning(f"Could not create log file {log_file}: {e}")

    return logger


def get_logger(name: str = "idrac-mcp") -> logging.Logger:
    """
    Get a logger instance for the specified name.

    If the logger hasn't been set up yet, returns a basic logger
    that logs to stderr.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set up basic stderr logging
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.CRITICAL)  # Default to quiet
        logger.propagate = False

    return logger


def suppress_noisy_loggers() -> None:
    """
    Suppress overly verbose loggers from third-party libraries.

    This prevents libraries like urllib3 and requests from flooding
    the logs with connection details.
    """
    noisy_loggers = [
        'urllib3',
        'requests',
        'httpx',
        'httpcore',
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


# Backward compatibility aliases
setup_logging = setup_mcp_logging
