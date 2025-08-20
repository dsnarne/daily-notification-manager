#!/usr/bin/env python3
"""
Tests for Gmail MCP Server
"""

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List

# Import MCP types and server components
from mcp.types import Tool, TextContent


class TestGmailMCPServer:
    """Test suite for Gmail MCP Server functionality"""

    @pytest.fixture
    def mock_gmail_data(self):
        """Mock Gmail notification data"""
        return [
            {
                "id": "gmail:12345",
                "external_id": "12345",
                "thread_id": "thread123",
                "platform": "email",
                "notification_type": "message",
                "title": "Important Meeting Tomorrow",
                "content": "Don't forget about the quarterly review meeting at 2 PM tomorrow.",
                "sender": "boss@company.com",
                "recipient": "user@company.com",
                "priority": "high",
                "metadata": {"labelIds": "INBOX,IMPORTANT"},
                "created_at": datetime.now(),
                "link": "https://mail.google.com/mail/u/0/#inbox/12345"
            },
            {
                "id": "gmail:67890",
                "external_id": "67890",
                "thread_id": "thread456",
                "platform": "email",
                "notification_type": "message",
                "title": "Weekly Newsletter",
                "content": "This week's updates from the tech team...",
                "sender": "newsletter@techteam.com",
                "recipient": "user@company.com",
                "priority": "low",
                "metadata": {"labelIds": "INBOX"},
                "created_at": datetime.now(),
                "link": "https://mail.google.com/mail/u/0/#inbox/67890"
            }
        ]

    @pytest.fixture
    def mock_sender_importance_data(self):
        """Mock sender importance analysis data"""
        return {
            "sender": "boss@company.com",
            "importance_score": 9.5,
            "email_frequency": 12,
            "response_rate": 0.95,
            "avg_response_time_hours": 2.5,
            "is_internal": True,
            "recent_interactions": 8,
            "classification": "high_priority"
        }

    @pytest.fixture
    def mock_domain_info(self):
        """Mock domain information"""
        return {
            "email": "boss@company.com",
            "domain": "company.com",
            "is_internal": True,
            "is_trusted": True,
            "domain_type": "corporate"
        }

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that the server lists all expected tools"""
        from mcp_servers.communication_server.server import list_tools
        
        tools = await list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 4
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "list_gmail_notifications",
            "analyze_sender_importance", 
            "get_recent_conversations",
            "check_sender_domain"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_list_gmail_notifications_tool_schema(self):
        """Test the schema of list_gmail_notifications tool"""
        from mcp_servers.communication_server.server import list_tools
        
        tools = await list_tools()
        gmail_tool = next(tool for tool in tools if tool.name == "list_gmail_notifications")
        
        assert gmail_tool.description == "List recent Gmail notifications from INBOX with optional filters"
        
        schema = gmail_tool.inputSchema
        assert schema["type"] == "object"
        assert "since" in schema["properties"]
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]
        assert schema["required"] == []

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.list_notifications')
    async def test_list_gmail_notifications_success(self, mock_list_notifications, mock_gmail_data):
        """Test successful Gmail notifications listing"""
        from mcp_servers.communication_server.server import call_tool
        from mcp_servers.communication_server.models import Notification
        
        # Setup mock
        mock_list_notifications.return_value = mock_gmail_data
        
        # Call the tool
        result = await call_tool("list_gmail_notifications", {
            "max_results": 10,
            "query": "label:INBOX"
        })
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        
        # Parse response
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 2
        assert len(response_data["notifications"]) == 2
        assert response_data["notifications"][0]["title"] == "Important Meeting Tomorrow"
        assert response_data["notifications"][1]["title"] == "Weekly Newsletter"
        
        # Verify mock was called correctly
        mock_list_notifications.assert_called_once_with(
            since_iso=None,
            query="label:INBOX", 
            max_results=10
        )

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.list_notifications')
    async def test_list_gmail_notifications_with_filters(self, mock_list_notifications, mock_gmail_data):
        """Test Gmail notifications listing with filters"""
        from mcp_servers.communication_server.server import call_tool
        
        mock_list_notifications.return_value = mock_gmail_data
        
        # Call with filters
        result = await call_tool("list_gmail_notifications", {
            "since": "2024-01-01T00:00:00Z",
            "query": "from:boss@company.com",
            "max_results": 5
        })
        
        # Verify result
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 2
        
        # Verify mock was called with correct parameters
        mock_list_notifications.assert_called_once_with(
            since_iso="2024-01-01T00:00:00Z",
            query="from:boss@company.com",
            max_results=5
        )

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.analyze_sender_importance')
    async def test_analyze_sender_importance(self, mock_analyze_importance, mock_sender_importance_data):
        """Test sender importance analysis"""
        from mcp_servers.communication_server.server import call_tool
        
        mock_analyze_importance.return_value = mock_sender_importance_data
        
        result = await call_tool("analyze_sender_importance", {
            "sender_email": "boss@company.com",
            "days_back": 30
        })
        
        # Verify result
        response_data = json.loads(result[0].text)
        assert response_data["sender"] == "boss@company.com"
        assert response_data["importance_score"] == 9.5
        assert response_data["classification"] == "high_priority"
        
        # Verify mock was called correctly
        mock_analyze_importance.assert_called_once_with("boss@company.com", 30)

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.get_recent_conversations')
    async def test_get_recent_conversations(self, mock_get_conversations):
        """Test getting recent conversations"""
        mock_conversations = [
            {
                "message_id": "msg1",
                "subject": "Re: Project Update",
                "from": "boss@company.com",
                "date": "2024-01-15T10:00:00Z",
                "snippet": "Thanks for the update..."
            }
        ]
        mock_get_conversations.return_value = mock_conversations
        
        from mcp_servers.communication_server.server import call_tool
        
        result = await call_tool("get_recent_conversations", {
            "contact_email": "boss@company.com",
            "days_back": 7,
            "max_messages": 10
        })
        
        # Verify result
        response_data = json.loads(result[0].text)
        assert response_data["contact"] == "boss@company.com"
        assert len(response_data["conversations"]) == 1
        assert response_data["conversations"][0]["subject"] == "Re: Project Update"
        
        # Verify mock was called correctly
        mock_get_conversations.assert_called_once_with("boss@company.com", 7, 10)

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.check_sender_domain')
    async def test_check_sender_domain(self, mock_check_domain, mock_domain_info):
        """Test checking sender domain"""
        from mcp_servers.communication_server.server import call_tool
        
        mock_check_domain.return_value = mock_domain_info
        
        result = await call_tool("check_sender_domain", {
            "sender_email": "boss@company.com"
        })
        
        # Verify result
        response_data = json.loads(result[0].text)
        assert response_data["email"] == "boss@company.com"
        assert response_data["domain"] == "company.com"
        assert response_data["is_internal"] == True
        assert response_data["domain_type"] == "corporate"
        
        # Verify mock was called correctly
        mock_check_domain.assert_called_once_with("boss@company.com")

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self):
        """Test calling a non-existent tool"""
        from mcp_servers.communication_server.server import call_tool
        
        result = await call_tool("non_existent_tool", {})
        
        # Should return error
        response_data = json.loads(result[0].text)
        assert "error" in response_data
        assert "Unknown tool" in response_data["error"]

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.server.gmail_integration.list_notifications')
    async def test_list_notifications_error_handling(self, mock_list_notifications):
        """Test error handling in list_gmail_notifications"""
        from mcp_servers.communication_server.server import call_tool
        
        # Setup mock to raise exception
        mock_list_notifications.side_effect = Exception("Gmail API error")
        
        result = await call_tool("list_gmail_notifications", {})
        
        # Should return error response
        response_data = json.loads(result[0].text)
        assert "error" in response_data
        assert "Gmail API error" in response_data["error"]
        assert response_data["tool"] == "list_gmail_notifications"

    @pytest.mark.asyncio
    async def test_notification_model_validation(self, mock_gmail_data):
        """Test that notification data validates against the Notification model"""
        from mcp_servers.communication_server.models import Notification
        
        for notification_data in mock_gmail_data:
            # This should not raise any validation errors
            notification = Notification(**notification_data)
            assert notification.id == notification_data["id"]
            assert notification.platform == "email"
            assert notification.notification_type == "message"

    @pytest.mark.asyncio
    async def test_list_notifications_args_validation(self):
        """Test ListNotificationsArgs validation"""
        from mcp_servers.communication_server.models import ListNotificationsArgs
        
        # Valid args
        valid_args = ListNotificationsArgs(
            since="2024-01-01T00:00:00Z",
            query="from:test@example.com"
        )
        assert valid_args.since == "2024-01-01T00:00:00Z"
        assert valid_args.query == "from:test@example.com"
        
        # Args with defaults
        default_args = ListNotificationsArgs()
        assert default_args.since is None
        assert default_args.query is None


class TestGmailIntegrationUnit:
    """Unit tests for Gmail integration without MCP server"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for Gmail"""
        with patch.dict(os.environ, {
            'GMAIL_CLIENT_ID': 'test_client_id',
            'GMAIL_CLIENT_SECRET': 'test_client_secret', 
            'GMAIL_REFRESH_TOKEN': 'test_refresh_token'
        }):
            yield

    @pytest.mark.asyncio
    @patch('mcp_servers.communication_server.integrations.gmail.GmailIntegration._list_notifications_sync')
    async def test_gmail_integration_direct_call(self, mock_list_gmail_sync, mock_env_vars):
        """Test calling Gmail integration directly"""
        mock_notifications = [
            {
                "id": "gmail:test123",
                "external_id": "test123", 
                "title": "Test Email",
                "content": "Test content",
                "sender": "test@example.com",
                "platform": "email",
                "notification_type": "message",
                "created_at": datetime.now().isoformat()
            }
        ]
        mock_list_gmail_sync.return_value = mock_notifications
        
        from mcp_servers.communication_server.integrations.gmail import GmailIntegration
        
        gmail = GmailIntegration()
        result = await gmail.list_notifications()
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Email"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])