"""
Centralized logging configuration for Kortex Agent

Provides consistent logging across all modules with:
- Timestamped output
- Structured log format
- Configurable log levels
"""

from __future__ import annotations

import logging
import os
import sys


# Custom formatter with colors for console output
class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        log_fmt = (
            "%(asctime)s "
            f"{color}[%(levelname)s]{self.RESET} "
            "%(name)s:%(lineno)d - %(message)s"
        )
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def _is_color_enabled() -> bool:
    return os.getenv("KORTEX_LOG_COLOR", "true").lower() == "true"


def setup_logging(level: str | None = None) -> None:
    """
    Configure logging for the entire application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses KORTEX_LOG_LEVEL environment variable.
    """
    effective_level = level or os.getenv("KORTEX_LOG_LEVEL", "INFO")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, effective_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if _is_color_enabled():
        console_handler.setFormatter(ColoredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(console_handler)
    
    # Set level for third-party libraries to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Usage:
        from kortex.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info("Message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    Args:
        name: Usually __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
