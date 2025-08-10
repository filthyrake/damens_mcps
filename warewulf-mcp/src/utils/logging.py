"""
Logging utilities for the Warewulf MCP Server.
"""

import logging
import json
import os
from typing import Optional, Dict, Any


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the Warewulf MCP Server.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ('json' or 'text')
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger("warewulf_mcp")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if format_type.lower() == "json":
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_request(logger: logging.Logger, method: str, endpoint: str, **kwargs) -> None:
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        **kwargs: Additional request parameters
    """
    logger.info(
        f"API Request: {method} {endpoint}",
        extra={
            "method": method,
            "endpoint": endpoint,
            "params": kwargs
        }
    )


def log_response(logger: logging.Logger, status_code: int, response_time: float, **kwargs) -> None:
    """
    Log API response details.
    
    Args:
        logger: Logger instance
        status_code: HTTP status code
        response_time: Response time in seconds
        **kwargs: Additional response parameters
    """
    level = logging.INFO if status_code < 400 else logging.WARNING
    logger.log(
        level,
        f"API Response: {status_code} ({response_time:.3f}s)",
        extra={
            "status_code": status_code,
            "response_time": response_time,
            "params": kwargs
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error details with context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Optional context information
    """
    logger.error(
        f"Error: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        },
        exc_info=True
    )
