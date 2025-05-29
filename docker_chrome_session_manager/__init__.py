"""
Docker Chrome Session Manager

A Python module for managing Selenium Chrome sessions across multiple Docker containers.
It supports dynamic container selection, session configuration persistence, and safe concurrent access.
"""

__version__ = "1.0.1"

from .data import SessionConfig, SessionManagerConfig
from .manager import SessionManager

__all__ = [
    "SessionConfig",
    "SessionManagerConfig",
    "SessionManager",
]