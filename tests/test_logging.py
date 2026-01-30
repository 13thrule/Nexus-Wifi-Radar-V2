"""
Tests for the logging module.
"""

import logging
import pytest
from io import StringIO

from nexus.core.logging import (
    get_logger,
    get_nexus_logger,
    configure_logging,
    set_log_level,
    enable_debug_logging,
    disable_console_logging,
    NexusLogger,
    ColoredFormatter,
)


class TestGetLogger:
    """Tests for logger retrieval."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that same name returns same logger."""
        logger1 = get_logger("test_same")
        logger2 = get_logger("test_same")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        logger1 = get_logger("test_a")
        logger2 = get_logger("test_b")
        assert logger1 is not logger2


class TestNexusLogger:
    """Tests for the NexusLogger singleton."""

    def test_singleton_pattern(self):
        """Test that NexusLogger follows singleton pattern."""
        instance1 = get_nexus_logger()
        instance2 = get_nexus_logger()
        assert instance1 is instance2

    def test_set_level(self):
        """Test setting log level."""
        nexus_logger = get_nexus_logger()
        nexus_logger.set_level(logging.WARNING)
        # Verify it was set
        assert nexus_logger._root_logger.level == logging.WARNING
        # Reset for other tests
        nexus_logger.set_level(logging.INFO)


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_with_level(self):
        """Test configuring with specific level."""
        configure_logging(level=logging.DEBUG)
        nexus_logger = get_nexus_logger()
        assert nexus_logger._root_logger.level == logging.DEBUG
        # Reset
        configure_logging(level=logging.INFO)


class TestColoredFormatter:
    """Tests for the colored formatter."""

    def test_formatter_creates_output(self):
        """Test that formatter produces output."""
        formatter = ColoredFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        assert "Test message" in output

    def test_formatter_includes_level(self):
        """Test that formatter includes log level."""
        formatter = ColoredFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        assert "WARNING" in output


class TestLogLevelHelpers:
    """Tests for log level helper functions."""

    def test_enable_debug_logging(self):
        """Test enabling debug logging."""
        enable_debug_logging()
        nexus_logger = get_nexus_logger()
        assert nexus_logger._root_logger.level == logging.DEBUG
        # Reset
        set_log_level(logging.INFO)

    def test_set_log_level(self):
        """Test setting log level via helper."""
        set_log_level(logging.ERROR)
        nexus_logger = get_nexus_logger()
        assert nexus_logger._root_logger.level == logging.ERROR
        # Reset
        set_log_level(logging.INFO)
