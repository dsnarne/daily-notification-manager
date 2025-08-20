#!/usr/bin/env python3
"""
Tests for Agent MCP Client
"""

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import agent components
from agent.client import (
    NotificationAgent, 
    NotificationDecision, 
    BatchGroup, 
    ProcessingResult
)


class TestNotificationAgent:
    """Test suite for NotificationAgent MCP client functionality"""

    @pytest.fixture
    def sample_notifications(self):
        """Sample notifications for testing"""
        return [
            {
                "id": "email_123",
                "platform": "gmail",
                "sender": "boss@company.com",
                "subject": "Urgent: Q4 Budget Review",
                "content": "We need to review the Q4 budget by EOD. Please prepare the financial report.",
                "timestamp": "2024-01-15T14:30:00Z",
                "type": "email"
            },
            {
                "id": "slack_456", 
                "platform": "slack",
                "sender": "mike.jones",
                "subject": "API endpoint error",
                "content": "The /users endpoint is returning 500 errors. Need immediate fix.",
                "timestamp": "2024-01-15T14:35:00Z",
                "type": "direct_message"
            },
            {
                "id": "newsletter_789",
                "platform": "gmail",
                "sender": "newsletter@techcrunch.com",
                "subject": "Daily Tech News",
                "content": "Today's top stories from the world of technology...",
                "timestamp": "2024-01-15T14:00:00Z",
                "type": "newsletter"
            }
        ]

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response"""
        return {
            "analysis_summary": "Analyzed 3 notifications: 1 urgent business item, 1 technical issue, 1 newsletter",
            "decisions": [
                {
                    "notification_id": "email_123",
                    "decision": "IMMEDIATE",
                    "urgency_score": 9,
                    "importance_score": 8,
                    "reasoning": "High priority from boss with deadline",
                    "context_used": ["sender_importance", "deadline_detection"],
                    "suggested_action": "Notify immediately with high priority alert",
                    "batch_group": None
                },
                {
                    "notification_id": "slack_456",
                    "decision": "IMMEDIATE", 
                    "urgency_score": 8,
                    "importance_score": 7,
                    "reasoning": "Technical issue affecting production systems",
                    "context_used": ["error_detection", "system_impact"],
                    "suggested_action": "Alert development team immediately",
                    "batch_group": None
                },
                {
                    "notification_id": "newsletter_789",
                    "decision": "DIGEST",
                    "urgency_score": 2,
                    "importance_score": 3, 
                    "reasoning": "Low priority newsletter content",
                    "context_used": ["sender_classification"],
                    "suggested_action": "Include in daily digest",
                    "batch_group": "daily_newsletters"
                }
            ],
            "batch_groups": {
                "daily_newsletters": {
                    "notifications": ["newsletter_789"],
                    "summary": "Daily newsletters and non-urgent updates",
                    "suggested_timing": "Once daily at 6 PM"
                }
            },
            "overall_recommendations": [
                "Consider adding auto-filters for newsletters",
                "Set up priority routing for boss emails"
            ]
        }

    @pytest.fixture
    def mock_mcp_tools(self):
        """Mock MCP tools available from servers"""
        return [
            {
                "name": "list_gmail_notifications",
                "description": "List recent Gmail notifications", 
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "since": {"type": "string"},
                        "query": {"type": "string"}
                    }
                },
                "_server": "communication"
            },
            {
                "name": "analyze_sender_importance", 
                "description": "Analyze sender importance",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sender_email": {"type": "string"}
                    }
                },
                "_server": "communication"
            }
        ]

    @pytest.fixture
    def agent(self):
        """Create NotificationAgent instance for testing"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            return NotificationAgent()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.anthropic is not None
        assert agent.mcp_sessions == {}
        assert agent.system_prompt is not None

    @pytest.mark.asyncio
    @patch('agent.client.stdio_client')
    async def test_initialize_mcp_servers(self, mock_stdio_client, agent):
        """Test MCP server initialization"""
        # Mock successful connections
        mock_session = AsyncMock()
        mock_stdio_client.return_value = mock_session
        
        await agent.initialize_mcp_servers()
        
        # Check that sessions were initialized
        assert len(agent.mcp_sessions) > 0
        assert "communication" in agent.mcp_sessions

    @pytest.mark.asyncio
    @patch('agent.client.stdio_client')
    async def test_initialize_mcp_servers_partial_failure(self, mock_stdio_client, agent):
        """Test MCP server initialization with partial failures"""
        # Mock mixed success/failure
        def side_effect(params):
            if "communication" in str(params):
                return AsyncMock()
            else:
                raise Exception("Server not available")
        
        mock_stdio_client.side_effect = side_effect
        
        await agent.initialize_mcp_servers()
        
        # Should continue with available servers
        assert "communication" in agent.mcp_sessions

    @pytest.mark.asyncio
    async def test_get_available_tools(self, agent, mock_mcp_tools):
        """Test getting available tools from MCP servers"""
        # Mock MCP session
        mock_session = AsyncMock()
        mock_tools_response = MagicMock()
        mock_tools_response.tools = [
            MagicMock(
                name="list_gmail_notifications",
                description="List recent Gmail notifications",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
        mock_session.list_tools.return_value = mock_tools_response
        agent.mcp_sessions["communication"] = mock_session
        
        tools = await agent.get_available_tools()
        
        assert len(tools) == 1
        assert tools[0]["name"] == "list_gmail_notifications"
        assert tools[0]["_server"] == "communication"

    @pytest.mark.asyncio
    async def test_get_claude_tools_format(self, agent):
        """Test converting MCP tools to Claude format"""
        # Mock get_available_tools
        with patch.object(agent, 'get_available_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "input_schema": {"type": "object"},
                    "_server": "test"
                }
            ]
            
            claude_tools = await agent.get_claude_tools_format()
            
            assert len(claude_tools) == 1
            assert claude_tools[0]["name"] == "test_tool"
            assert "_server" not in claude_tools[0]  # Should be removed

    @pytest.mark.asyncio
    async def test_call_mcp_tool(self, agent):
        """Test calling MCP tools"""
        # Mock session and tools
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"result": "success"}')]
        mock_session.call_tool.return_value = mock_result
        
        agent.mcp_sessions["communication"] = mock_session
        
        # Mock get_available_tools to find the tool
        with patch.object(agent, 'get_available_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {"name": "test_tool", "_server": "communication"}
            ]
            
            result = await agent.call_mcp_tool("test_tool", {"arg": "value"})
            
            assert result == '{"result": "success"}'
            mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_mcp_tool_not_found(self, agent):
        """Test calling non-existent MCP tool"""
        with patch.object(agent, 'get_available_tools') as mock_get_tools:
            mock_get_tools.return_value = []
            
            with pytest.raises(ValueError, match="Tool non_existent not found"):
                await agent.call_mcp_tool("non_existent", {})

    def test_format_notifications(self, agent, sample_notifications):
        """Test notification formatting for Claude"""
        formatted = agent.format_notifications(sample_notifications)
        
        assert "Notification #1:" in formatted
        assert "email_123" in formatted
        assert "boss@company.com" in formatted
        assert "Urgent: Q4 Budget Review" in formatted
        assert "Notification #3:" in formatted

    @pytest.mark.asyncio
    @patch('agent.client.NotificationAgent.initialize_mcp_servers')
    @patch('agent.client.NotificationAgent.get_claude_tools_format')
    @patch('agent.client.NotificationAgent.handle_tool_calls_conversation')
    @patch('agent.client.NotificationAgent.cleanup_mcp_sessions')
    async def test_process_notifications(self, mock_cleanup, mock_handle_tools, 
                                       mock_get_tools, mock_init, agent, 
                                       sample_notifications, mock_claude_response):
        """Test main notification processing"""
        # Setup mocks
        mock_init.return_value = None
        mock_get_tools.return_value = []
        mock_handle_tools.return_value = json.dumps(mock_claude_response)
        mock_cleanup.return_value = None
        
        # Mock Anthropic API
        with patch.object(agent.anthropic.messages, 'create') as mock_create:
            mock_response = MagicMock()
            mock_create.return_value = mock_response
            
            result = await agent.process_notifications(sample_notifications)
            
            # Verify result structure
            assert isinstance(result, ProcessingResult)
            assert len(result.decisions) == 3
            assert len(result.batch_groups) == 1
            assert result.processing_time > 0
            
            # Verify decisions
            urgent_decision = next(d for d in result.decisions if d.notification_id == "email_123")
            assert urgent_decision.decision == "IMMEDIATE"
            assert urgent_decision.urgency_score == 9
            
            newsletter_decision = next(d for d in result.decisions if d.notification_id == "newsletter_789")
            assert newsletter_decision.decision == "DIGEST"
            assert newsletter_decision.batch_group == "daily_newsletters"

    @pytest.mark.asyncio
    async def test_handle_tool_calls_conversation_no_tools(self, agent):
        """Test conversation handling with no tool calls"""
        # Mock response with just text
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Final response text"
        mock_content.type = "text"
        mock_response.content = [mock_content]
        
        result = await agent.handle_tool_calls_conversation(mock_response, [])
        
        assert result == "Final response text"

    @pytest.mark.asyncio
    @patch('agent.client.NotificationAgent.call_mcp_tool')
    async def test_handle_tool_calls_conversation_with_tools(self, mock_call_tool, agent):
        """Test conversation handling with tool calls"""
        # Mock initial response with tool call
        mock_response = MagicMock()
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "test_tool"
        mock_tool_use.input = {"arg": "value"}
        mock_tool_use.id = "tool_123"
        mock_response.content = [mock_tool_use]
        
        # Mock tool call result
        mock_call_tool.return_value = '{"result": "tool_success"}'
        
        # Mock follow-up response
        mock_follow_up = MagicMock()
        mock_text_content = MagicMock()
        mock_text_content.text = "Final response after tool use"
        mock_text_content.type = "text"
        mock_follow_up.content = [mock_text_content]
        
        with patch.object(agent.anthropic.messages, 'create') as mock_create:
            with patch.object(agent, 'get_claude_tools_format') as mock_get_tools:
                mock_create.return_value = mock_follow_up
                mock_get_tools.return_value = []
                
                result = await agent.handle_tool_calls_conversation(mock_response, [])
                
                assert result == "Final response after tool use"
                mock_call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    def test_parse_response_success(self, agent, mock_claude_response):
        """Test successful response parsing"""
        response_text = json.dumps(mock_claude_response)
        result = agent.parse_response(response_text)
        
        assert isinstance(result, ProcessingResult)
        assert result.analysis_summary == "Analyzed 3 notifications: 1 urgent business item, 1 technical issue, 1 newsletter"
        assert len(result.decisions) == 3
        assert len(result.batch_groups) == 1
        
        # Check decision details
        urgent_decision = result.decisions[0]
        assert urgent_decision.notification_id == "email_123"
        assert urgent_decision.decision == "IMMEDIATE"
        assert urgent_decision.urgency_score == 9
        
        # Check batch group
        newsletter_group = result.batch_groups["daily_newsletters"]
        assert newsletter_group.name == "daily_newsletters"
        assert len(newsletter_group.notifications) == 1

    def test_parse_response_invalid_json(self, agent):
        """Test response parsing with invalid JSON"""
        invalid_json = "This is not valid JSON"
        result = agent.parse_response(invalid_json)
        
        assert isinstance(result, ProcessingResult)
        assert result.analysis_summary == "Error parsing response"
        assert len(result.decisions) == 0
        assert len(result.overall_recommendations) == 1
        assert "Failed to parse response" in result.overall_recommendations[0]

    @pytest.mark.asyncio
    async def test_cleanup_mcp_sessions(self, agent):
        """Test MCP session cleanup"""
        # Mock sessions
        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()
        agent.mcp_sessions = {
            "session1": mock_session1,
            "session2": mock_session2
        }
        
        await agent.cleanup_mcp_sessions()
        
        # Verify cleanup
        mock_session1.close.assert_called_once()
        mock_session2.close.assert_called_once()
        assert agent.mcp_sessions == {}

    @pytest.mark.asyncio
    async def test_cleanup_mcp_sessions_with_errors(self, agent):
        """Test MCP session cleanup with errors"""
        # Mock session that raises error on close
        mock_session = AsyncMock()
        mock_session.close.side_effect = Exception("Close error")
        agent.mcp_sessions = {"session": mock_session}
        
        # Should not raise exception
        await agent.cleanup_mcp_sessions()
        assert agent.mcp_sessions == {}


class TestNotificationModels:
    """Test notification-related data models"""

    def test_notification_decision_creation(self):
        """Test NotificationDecision model creation"""
        decision = NotificationDecision(
            notification_id="test_123",
            decision="IMMEDIATE",
            urgency_score=8,
            importance_score=7,
            reasoning="High priority email",
            context_used=["sender_analysis"],
            suggested_action="Alert immediately"
        )
        
        assert decision.notification_id == "test_123"
        assert decision.decision == "IMMEDIATE"
        assert decision.batch_group is None

    def test_batch_group_creation(self):
        """Test BatchGroup model creation"""
        group = BatchGroup(
            name="newsletters",
            notifications=["notif_1", "notif_2"],
            summary="Daily newsletters",
            suggested_timing="6 PM daily"
        )
        
        assert group.name == "newsletters"
        assert len(group.notifications) == 2

    def test_processing_result_creation(self):
        """Test ProcessingResult model creation"""
        result = ProcessingResult(
            analysis_summary="Test analysis",
            decisions=[],
            batch_groups={},
            overall_recommendations=["Test recommendation"],
            processing_time=1.5
        )
        
        assert result.analysis_summary == "Test analysis"
        assert result.processing_time == 1.5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])