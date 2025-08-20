# mcp-servers/communication-server/__init__.py
"""
Communication Server MCP Package

This MCP server provides tools for accessing and analyzing communication 
across various platforms including Gmail, Slack, Teams, and other messaging services.

Current Features:
- Gmail notification listing and analysis
- Sender importance scoring
- Communication history analysis
- Domain reputation checking

Tools Available:
- list_gmail_notifications: Get recent Gmail messages
- analyze_sender_importance: Score sender importance
- get_recent_conversations: Get conversation history
- check_sender_domain: Analyze email domain reputation
"""

from .models import (
    Notification,
    ListNotificationsArgs, 
    SenderImportance,
    ConversationMessage,
    DomainInfo
)

from .integrations import gmail

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = [
    "Notification",
    "ListNotificationsArgs",
    "SenderImportance", 
    "ConversationMessage",
    "DomainInfo",
    "gmail"
]