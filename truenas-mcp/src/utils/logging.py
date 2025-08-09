"""Logging utilities for TrueNAS MCP server."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    use_rich: bool = True
) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Custom log format (optional)
        use_rich: Whether to use rich formatting for console output
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    if log_format:
        formatter = logging.Formatter(log_format)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if use_rich and not log_file:
        # Use rich formatting for console output
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
    else:
        # Standard console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """Set log level for a specific logger.
    
    Args:
        logger_name: Name of the logger to configure
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(logger_name).setLevel(numeric_level)


def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None) -> None:
    """Log function call details.
    
    Args:
        func_name: Name of the function being called
        args: Function arguments
        kwargs: Function keyword arguments
    """
    logger = logging.getLogger(__name__)
    
    call_info = f"Function call: {func_name}"
    if args:
        call_info += f" args: {args}"
    if kwargs:
        # Don't log sensitive information like passwords
        safe_kwargs = {}
        for key, value in kwargs.items():
            if 'password' in key.lower() or 'token' in key.lower() or 'key' in key.lower():
                safe_kwargs[key] = '***'
            else:
                safe_kwargs[key] = value
        call_info += f" kwargs: {safe_kwargs}"
    
    logger.debug(call_info)


def log_api_request(method: str, url: str, status_code: Optional[int] = None, error: Optional[str] = None) -> None:
    """Log API request details.
    
    Args:
        method: HTTP method
        url: Request URL
        status_code: Response status code
        error: Error message if request failed
    """
    logger = logging.getLogger(__name__)
    
    if error:
        logger.error(f"API request failed: {method} {url} - {error}")
    elif status_code:
        if status_code >= 400:
            logger.warning(f"API request warning: {method} {url} - Status: {status_code}")
        else:
            logger.debug(f"API request: {method} {url} - Status: {status_code}")
    else:
        logger.debug(f"API request: {method} {url}")


def log_security_event(event_type: str, details: str, user: Optional[str] = None) -> None:
    """Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
        user: User associated with the event
    """
    logger = logging.getLogger("security")
    
    security_msg = f"Security event [{event_type}]: {details}"
    if user:
        security_msg += f" - User: {user}"
    
    logger.warning(security_msg)


def log_performance_metric(operation: str, duration: float, success: bool = True) -> None:
    """Log performance metrics.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        success: Whether the operation was successful
    """
    logger = logging.getLogger("performance")
    
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Performance: {operation} - {duration:.3f}s - {status}")


def create_audit_logger(log_file: str) -> logging.Logger:
    """Create an audit logger for sensitive operations.
    
    Args:
        log_file: Path to audit log file
        
    Returns:
        Configured audit logger
    """
    # Ensure audit log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if not audit_logger.handlers:
        # Create file handler for audit log
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        
        # Create formatter for audit logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        audit_logger.addHandler(file_handler)
    
    return audit_logger


def log_audit_event(
    event_type: str,
    user: str,
    resource: str,
    action: str,
    details: Optional[str] = None,
    success: bool = True
) -> None:
    """Log an audit event.
    
    Args:
        event_type: Type of audit event
        user: User performing the action
        resource: Resource being accessed/modified
        action: Action being performed
        details: Additional details
        success: Whether the action was successful
    """
    audit_logger = logging.getLogger("audit")
    
    status = "SUCCESS" if success else "FAILED"
    audit_msg = f"AUDIT [{event_type}] - User: {user} - Resource: {resource} - Action: {action} - Status: {status}"
    
    if details:
        audit_msg += f" - Details: {details}"
    
    audit_logger.info(audit_msg)
