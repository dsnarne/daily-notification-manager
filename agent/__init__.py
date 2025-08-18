# agent/__init__.py
"""
Notification Agent Package

This package contains the core notification processing agent that uses
Anthropic's Claude with MCP (Model Context Protocol) servers to intelligently
analyze and prioritize notifications from various platforms.

Main Components:
- NotificationAgent: Core agent class for processing notifications
- NotificationDecision: Data class for individual notification decisions
- BatchGroup: Data class for grouped notifications
- ProcessingResult: Data class for complete processing results
"""

from .client import (
    NotificationAgent,
    NotificationDecision,
    BatchGroup,
    ProcessingResult
)

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Package metadata
__all__ = [
    "NotificationAgent",
    "NotificationDecision", 
    "BatchGroup",
    "ProcessingResult"
]

# For convenience imports
Agent = NotificationAgent