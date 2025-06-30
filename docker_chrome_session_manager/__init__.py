"""
Docker Chrome Session Manager

A Python module for managing Selenium Chrome sessions across multiple Docker containers.
It supports dynamic container selection, session configuration persistence, and safe concurrent access.
"""

__version__ = "1.0.4"

import logging

from .data import SessionConfig, SessionManagerConfig
from .manager import SessionManager

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "SessionConfig",
    "SessionManagerConfig",
    "SessionManager",
]
