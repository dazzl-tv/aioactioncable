"""
Async library for building Ruby on Rails Action Cable clients, built on top of websockets.
"""

__version__ = '0.8'
__all__ = ["client", "subscription"]

from .client import Connect as connect
