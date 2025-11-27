"""
Pure functional logging module for observability client

This module provides functional, composable logging utilities.
"""

import logging
from typing import Dict, Any, Callable
from functools import partial


# Type aliases
LogData = Dict[str, Any]
LogFormatter = Callable[[str, LogData], str]


def create_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a configured logger instance
    
    Pure function: Same inputs always produce same output
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    return logger


def format_structured_log(message: str, data: LogData) -> str:
    """
    Format a log message with structured data
    
    Pure function for log formatting
    """
    if not data:
        return message
    
    parts = [message]
    for key, value in sorted(data.items()):
        parts.append(f"{key}={value}")
    
    return " ".join(parts)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with context data
    
    This is a pure action - it performs a side effect (logging)
    but in a controlled, predictable way
    """
    logger.log(level, message, extra=context)


# Pre-configured log functions (partial application)
def create_log_functions(logger: logging.Logger):
    """
    Create partially applied log functions
    
    Returns a dict of log functions for each level
    """
    return {
        'debug': partial(log_with_context, logger, logging.DEBUG),
        'info': partial(log_with_context, logger, logging.INFO),
        'warning': partial(log_with_context, logger, logging.WARNING),
        'error': partial(log_with_context, logger, logging.ERROR),
        'critical': partial(log_with_context, logger, logging.CRITICAL),
    }


class StructuredLogger:
    """
    Structured logger with functional core
    
    This class provides a convenient interface while keeping
    the core logic functional and testable
    """
    
    def __init__(self, service_name: str, level: int = logging.INFO):
        self._logger = create_logger(service_name, level)
        self._log_fns = create_log_functions(self._logger)
    
    def info(self, message: str, **context: Any) -> None:
        """Log info message"""
        self._log_fns['info'](message, **context)
    
    def error(self, message: str, **context: Any) -> None:
        """Log error message"""
        self._log_fns['error'](message, **context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message"""
        self._log_fns['warning'](message, **context)
    
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message"""
        self._log_fns['debug'](message, **context)
