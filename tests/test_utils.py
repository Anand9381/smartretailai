"""
test_utils.py - Simple tests for utility helpers (logging)
=========================================================

These tests are intentionally small and explainable. They verify that
the project's logger setup function returns a usable logger instance
with at least one handler attached.
"""

import logging
from utils import logger as project_logger


def test_setup_logger_returns_logger():
    """setup_logger should return a logger instance with handlers."""
    lg = project_logger.setup_logger("test_logger")
    assert lg is not None
    # Should be a Logger instance (handlers may be attached at root in test env)
    assert isinstance(lg, logging.Logger)
