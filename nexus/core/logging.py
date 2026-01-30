"""
Logging framework for Nexus WiFi Radar.

Provides centralized logging configuration with support for:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file output
- Colored console output for terminals
- Structured log format with timestamps
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Default log format
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ANSI color codes for console output
COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds ANSI color codes for terminal output.

    Colors are only applied when outputting to a TTY.
    """

    def __init__(self, fmt: str = DEFAULT_FORMAT, datefmt: str = DEFAULT_DATE_FORMAT,
                 use_colors: bool = True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with optional colors."""
        # Save original levelname
        original_levelname = record.levelname

        if self.use_colors:
            color = COLORS.get(record.levelname, "")
            reset = COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"

        result = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return result


class NexusLogger:
    """
    Centralized logger for Nexus WiFi Radar.

    Provides a singleton-like interface for consistent logging across
    all modules.

    Usage:
        from nexus.core.logging import get_logger

        logger = get_logger(__name__)
        logger.info("Scan started")
        logger.warning("Weak signal detected")
        logger.error("Scanner failed", exc_info=True)
    """

    _instance: Optional["NexusLogger"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if NexusLogger._initialized:
            return

        self._loggers: dict = {}
        self._root_logger = logging.getLogger("nexus")
        self._root_logger.setLevel(logging.DEBUG)

        # Default console handler
        self._console_handler: Optional[logging.Handler] = None
        self._file_handler: Optional[logging.Handler] = None

        # Set up default console handler
        self.add_console_handler()

        NexusLogger._initialized = True

    def add_console_handler(self, level: int = logging.INFO,
                           use_colors: bool = True) -> None:
        """Add or replace the console handler."""
        if self._console_handler:
            self._root_logger.removeHandler(self._console_handler)

        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(level)
        self._console_handler.setFormatter(ColoredFormatter(use_colors=use_colors))
        self._root_logger.addHandler(self._console_handler)

    def add_file_handler(self, filepath: str, level: int = logging.DEBUG,
                        max_bytes: int = 10 * 1024 * 1024,
                        backup_count: int = 3) -> None:
        """
        Add a file handler for persistent logging.

        Args:
            filepath: Path to the log file
            level: Minimum log level for file output
            max_bytes: Maximum file size before rotation (default 10MB)
            backup_count: Number of backup files to keep
        """
        if self._file_handler:
            self._root_logger.removeHandler(self._file_handler)

        # Ensure log directory exists
        log_path = Path(filepath)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from logging.handlers import RotatingFileHandler
            self._file_handler = RotatingFileHandler(
                filepath,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
        except ImportError:
            # Fallback to basic file handler
            self._file_handler = logging.FileHandler(filepath, encoding="utf-8")

        self._file_handler.setLevel(level)
        self._file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT))
        self._root_logger.addHandler(self._file_handler)

    def set_level(self, level: int) -> None:
        """Set the root logger level."""
        self._root_logger.setLevel(level)
        if self._console_handler:
            self._console_handler.setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger for the specified module.

        Args:
            name: Module name (typically __name__)

        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        # Create child logger under nexus namespace
        if name.startswith("nexus"):
            logger = logging.getLogger(name)
        else:
            logger = logging.getLogger(f"nexus.{name}")

        self._loggers[name] = logger
        return logger

    def disable_console(self) -> None:
        """Disable console output (useful for GUI mode)."""
        if self._console_handler:
            self._root_logger.removeHandler(self._console_handler)
            self._console_handler = None

    def enable_debug(self) -> None:
        """Enable debug mode with verbose output."""
        self.set_level(logging.DEBUG)


# Module-level singleton
_logger_instance: Optional[NexusLogger] = None


def get_nexus_logger() -> NexusLogger:
    """Get the Nexus logger singleton."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = NexusLogger()
    return _logger_instance


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified module.

    This is the primary interface for obtaining loggers throughout
    the Nexus codebase.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        from nexus.core.logging import get_logger

        logger = get_logger(__name__)
        logger.info("Starting scan...")
    """
    return get_nexus_logger().get_logger(name)


def configure_logging(level: int = logging.INFO,
                     log_file: Optional[str] = None,
                     use_colors: bool = True) -> None:
    """
    Configure the Nexus logging system.

    Args:
        level: Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        use_colors: Whether to use colored console output
    """
    nexus_logger = get_nexus_logger()
    nexus_logger.set_level(level)
    nexus_logger.add_console_handler(level=level, use_colors=use_colors)

    if log_file:
        nexus_logger.add_file_handler(log_file, level=logging.DEBUG)


def set_log_level(level: int) -> None:
    """Set the global log level."""
    get_nexus_logger().set_level(level)


def enable_debug_logging() -> None:
    """Enable debug logging globally."""
    get_nexus_logger().enable_debug()


def disable_console_logging() -> None:
    """Disable console logging (for GUI mode)."""
    get_nexus_logger().disable_console()
