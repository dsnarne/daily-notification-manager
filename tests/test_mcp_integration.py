#!/usr/bin/env python3
"""
Integration Tests for MCP Server-Client Communication
"""

import pytest
import asyncio
import json
import os
import tempfile
import subprocess
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch

# Import components for integration testing
from agent.client import NotificationAgent, ProcessingResult
from mcp_servers.communication_server.models import Notification


class MCPServerProcess:
    """Helper class to manage MCP server process for testing"""
    
    def __init__(self, server_script: str, server_name: str):
        self.server_script = server_script
        self.server_name = server_name
        self.process: Optional[subprocess.Popen] = None
        
    async def start(self):
        """Start the MCP server process"""
        try:
            self.process = subprocess.Popen(
                ["python", self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Give server time to initialize
            await asyncio.sleep(1)
            
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read() if self.process.stderr else ""
                raise Exception(f"Server {self.server_name} failed to start: {stderr_output}")
                
        except Exception as e:
            raise Exception(f"Failed to start {self.server_name} server: {e}")
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.sleep(0.5)
                if self.process.poll() is None:
                    self.process.kill()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None
    
    def is_running(self) -> bool:
        """Check if server process is running"""
        return self.process is not None and self.process.poll() is None


class TestMCPIntegration:
    """Integration tests for MCP server-client communication"""

    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent

    @pytest.fixture
    def communication_server_path(self, project_root):
        """Path to communication server"""
        return project_root / "mcp_servers" / "communication_server" / "server.py"

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables needed for testing"""
        env_vars = {
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'GMAIL_CLIENT_ID': 'test_gmail_client_id',
            'GMAIL_CLIENT_SECRET': 'test_gmail_client_secret',
            'GMAIL_REFRESH_TOKEN': 'test_gmail_refresh_token'
        }
        
        with patch.dict(os.environ, env_vars):
            yield env_vars

    @pytest.fixture
    async def communication_server(self, communication_server_path):
        """Start and manage communication server for testing"""
        server = MCPServerProcess(str(communication_server_path), "communication")
        
        try:
            await server.start()
            yield server
        finally:
            await server.stop()

    @pytest.fixture
    def sample_notifications(self):
        """Sample notifications for integration testing"""
        return [
            {
                "id": "gmail_integration_test_1",
                "platform": "gmail",
                "sender": "important@company.com",
                "subject": "Quarterly Review Meeting",
                "content": "Please join us for the quarterly review meeting tomorrow at 2 PM in Conference Room A.",
                "timestamp": "2024-01-15T14:30:00Z",
                "type": "email"
            },
            {
                "id": "gmail_integration_test_2", 
                "platform": "gmail",
                "sender": "alerts@monitoring.com",
                "subject": "System Alert: High CPU Usage",
                "content": "CPU usage on production server has exceeded 90% for the last 10 minutes.",
                "timestamp": "2024-01-15T14:35:00Z",
                "type": "alert"
            },
            {
                "id": "gmail_integration_test_3",
                "platform": "gmail", 
                "sender": "newsletter@techblog.com",
                "subject": "Weekly Tech Digest",
                "content": "This week's top articles about machine learning, cloud computing, and software development.",
                "timestamp": "2024-01-15T14:00:00Z",
                "type": "newsletter"
            }
        ]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_server_client_basic_communication(self, communication_server, mock_env_vars):
        """Test basic MCP server-client communication"""
        # Create agent
        agent = NotificationAgent()
        
        try:
            # Initialize MCP connections
            await agent.initialize_mcp_servers()
            
            # Check that we can list tools
            tools = await agent.get_available_tools()
            assert len(tools) > 0
            
            # Find Gmail tool
            gmail_tools = [t for t in tools if "gmail" in t["name"]]
            assert len(gmail_tools) > 0
            assert any("list_gmail_notifications" in t["name"] for t in gmail_tools)
            
        finally:
            await agent.cleanup_mcp_sessions()

    @pytest.mark.asyncio
    @pytest.mark.integration
    @patch('mcp_servers.communication_server.integrations.gmail.GmailIntegration.list_notifications')
    async def test_end_to_end_notification_processing(self, mock_gmail_list, communication_server, 
                                                     mock_env_vars, sample_notifications):
        """Test end-to-end notification processing with real MCP communication"""
        # Mock Gmail API to return test data
        gmail_notifications = [
            {
                "id": f"gmail:{notif['id']}",
                "external_id": notif["id"],
                "thread_id": f"thread_{notif['id']}",
                "platform": "email",
                "notification_type": "message",
                "title": notif["subject"],
                "content": notif["content"], 
                "sender": notif["sender"],
                "recipient": "user@company.com",
                "priority": "medium",
                "metadata": {"labelIds": "INBOX"},
                "created_at": notif["timestamp"],
                "link": f"https://mail.google.com/mail/u/0/#inbox/{notif['id']}"
            } for notif in sample_notifications
        ]
        mock_gmail_list.return_value = gmail_notifications
        
        # Mock Claude API response
        mock_claude_response = {
            "analysis_summary": "Processed 3 notifications: 1 meeting, 1 alert, 1 newsletter",
            "decisions": [
                {
                    "notification_id": "gmail_integration_test_1",
                    "decision": "IMMEDIATE",
                    "urgency_score": 7,
                    "importance_score": 8,
                    "reasoning": "Important meeting notification from company domain",
                    "context_used": ["sender_domain", "meeting_detection"],
                    "suggested_action": "Add to calendar and send reminder"
                },
                {
                    "notification_id": "gmail_integration_test_2",
                    "decision": "IMMEDIATE", 
                    "urgency_score": 9,
                    "importance_score": 9,
                    "reasoning": "Critical system alert requiring immediate attention",
                    "context_used": ["alert_detection", "severity_analysis"],
                    "suggested_action": "Escalate to on-call engineer"
                },
                {
                    "notification_id": "gmail_integration_test_3",
                    "decision": "DIGEST",
                    "urgency_score": 2,
                    "importance_score": 3,
                    "reasoning": "Regular newsletter, low priority",
                    "context_used": ["content_classification"],
                    "suggested_action": "Include in daily digest",
                    "batch_group": "newsletters"
                }
            ],
            "batch_groups": {
                "newsletters": {
                    "notifications": ["gmail_integration_test_3"],
                    "summary": "Weekly newsletters and updates",
                    "suggested_timing": "End of day digest"
                }
            },
            "overall_recommendations": [
                "Set up automatic filtering for newsletters",
                "Create priority rules for system alerts"
            ]
        }
        
        agent = NotificationAgent()
        
        try:
            # Mock Claude API call
            with patch.object(agent.anthropic.messages, 'create') as mock_claude:
                # Mock the response with tool calls
                mock_response = type('MockResponse', (), {
                    'content': [type('MockContent', (), {
                        'text': json.dumps(mock_claude_response),
                        'type': 'text'
                    })()]
                })()
                mock_claude.return_value = mock_response
                
                # Process notifications
                result = await agent.process_notifications(sample_notifications)
                
                # Verify processing result
                assert isinstance(result, ProcessingResult)
                assert len(result.decisions) == 3
                assert len(result.batch_groups) == 1
                assert result.processing_time > 0
                
                # Check specific decisions
                meeting_decision = next(d for d in result.decisions if d.notification_id == "gmail_integration_test_1")
                assert meeting_decision.decision == "IMMEDIATE"
                assert meeting_decision.importance_score == 8
                
                alert_decision = next(d for d in result.decisions if d.notification_id == "gmail_integration_test_2") 
                assert alert_decision.decision == "IMMEDIATE"
                assert alert_decision.urgency_score == 9
                
                newsletter_decision = next(d for d in result.decisions if d.notification_id == "gmail_integration_test_3")
                assert newsletter_decision.decision == "DIGEST"
                assert newsletter_decision.batch_group == "newsletters"
                
                # Verify batch groups
                newsletter_group = result.batch_groups["newsletters"]
                assert "gmail_integration_test_3" in newsletter_group.notifications
                
        finally:
            await agent.cleanup_mcp_sessions()

    @pytest.mark.asyncio
    @pytest.mark.integration
    @patch('mcp_servers.communication_server.integrations.gmail.GmailIntegration.analyze_sender_importance')
    async def test_mcp_tool_calls_with_context(self, mock_analyze_sender, communication_server, mock_env_vars):
        """Test MCP tool calls for gathering context"""
        # Mock sender importance analysis
        mock_analyze_sender.return_value = {
            "sender": "important@company.com",
            "importance_score": 8.5,
            "email_frequency": 15,
            "response_rate": 0.9,
            "is_internal": True,
            "classification": "high_priority"
        }
        
        agent = NotificationAgent()
        
        try:
            await agent.initialize_mcp_servers()
            
            # Test direct tool call
            result = await agent.call_mcp_tool("analyze_sender_importance", {
                "sender_email": "important@company.com",
                "days_back": 30
            })
            
            # Parse result
            result_data = json.loads(result)
            assert result_data["sender"] == "important@company.com"
            assert result_data["importance_score"] == 8.5
            assert result_data["classification"] == "high_priority"
            
            # Verify mock was called
            mock_analyze_sender.assert_called_once_with("important@company.com", 30)
            
        finally:
            await agent.cleanup_mcp_sessions()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_server_error_handling(self, mock_env_vars):
        """Test error handling when MCP server is not available"""
        agent = NotificationAgent()
        
        # Try to initialize without server running
        await agent.initialize_mcp_servers()
        
        # Should handle missing servers gracefully
        tools = await agent.get_available_tools()
        # May be empty if no servers available, which is expected
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_with_multiple_notification_batches(self, communication_server, mock_env_vars):
        """Test agent processing multiple notification batches"""
        large_notification_set = []
        
        # Create a larger set of notifications
        for i in range(10):
            large_notification_set.append({
                "id": f"test_notification_{i}",
                "platform": "gmail" if i % 2 == 0 else "slack",
                "sender": f"user{i}@company.com",
                "subject": f"Test notification {i}",
                "content": f"This is test notification number {i}",
                "timestamp": "2024-01-15T14:00:00Z",
                "type": "email" if i % 2 == 0 else "message"
            })
        
        agent = NotificationAgent()
        
        try:
            # Mock Claude response for large batch
            mock_large_response = {
                "analysis_summary": f"Analyzed {len(large_notification_set)} notifications",
                "decisions": [
                    {
                        "notification_id": f"test_notification_{i}",
                        "decision": "BATCH" if i > 5 else "IMMEDIATE",
                        "urgency_score": 5,
                        "importance_score": 5,
                        "reasoning": f"Notification {i} analysis",
                        "context_used": ["batch_processing"],
                        "suggested_action": "Process in batch" if i > 5 else "Process immediately",
                        "batch_group": "bulk_notifications" if i > 5 else None
                    } for i in range(len(large_notification_set))
                ],
                "batch_groups": {
                    "bulk_notifications": {
                        "notifications": [f"test_notification_{i}" for i in range(6, 10)],
                        "summary": "Bulk notifications for batch processing",
                        "suggested_timing": "Process in 1 hour"
                    }
                },
                "overall_recommendations": ["Consider bulk processing for efficiency"]
            }
            
            with patch.object(agent.anthropic.messages, 'create') as mock_claude:
                mock_response = type('MockResponse', (), {
                    'content': [type('MockContent', (), {
                        'text': json.dumps(mock_large_response),
                        'type': 'text'
                    })()]
                })()
                mock_claude.return_value = mock_response
                
                result = await agent.process_notifications(large_notification_set)
                
                assert len(result.decisions) == 10
                assert "bulk_notifications" in result.batch_groups
                
                # Check batch grouping
                batch_decisions = [d for d in result.decisions if d.decision == "BATCH"]
                immediate_decisions = [d for d in result.decisions if d.decision == "IMMEDIATE"]
                
                assert len(batch_decisions) == 4  # notifications 6-9
                assert len(immediate_decisions) == 6  # notifications 0-5
                
        finally:
            await agent.cleanup_mcp_sessions()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_mcp_operations(self, communication_server, mock_env_vars):
        """Test concurrent MCP operations"""
        agent = NotificationAgent()
        
        try:
            await agent.initialize_mcp_servers()
            
            # Test concurrent tool calls
            with patch('mcp_servers.communication_server.integrations.gmail.GmailIntegration.check_sender_domain') as mock_domain:
                mock_domain.return_value = {"domain": "test.com", "is_internal": False}
                
                # Create multiple concurrent tasks
                tasks = []
                for i in range(3):
                    task = agent.call_mcp_tool("check_sender_domain", {
                        "sender_email": f"user{i}@test.com"
                    })
                    tasks.append(task)
                
                # Execute concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all succeeded
                assert len(results) == 3
                for result in results:
                    assert not isinstance(result, Exception)
                    result_data = json.loads(result)
                    assert result_data["domain"] == "test.com"
                
        finally:
            await agent.cleanup_mcp_sessions()


class TestMCPServerResilience:
    """Test MCP server resilience and recovery"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_restart_recovery(self, communication_server_path, mock_env_vars):
        """Test recovery when MCP server restarts"""
        agent = NotificationAgent()
        
        # Start server
        server = MCPServerProcess(str(communication_server_path), "communication")
        await server.start()
        
        try:
            # Initialize connection
            await agent.initialize_mcp_servers()
            assert len(agent.mcp_sessions) > 0
            
            # Stop server
            await server.stop()
            
            # Try operation (should fail gracefully)
            try:
                await agent.get_available_tools()
            except Exception:
                pass  # Expected to fail
            
            # Restart server
            await server.start()
            
            # Reinitialize
            await agent.cleanup_mcp_sessions()
            await agent.initialize_mcp_servers()
            
            # Should work again
            tools = await agent.get_available_tools()
            assert isinstance(tools, list)
            
        finally:
            await agent.cleanup_mcp_sessions()
            await server.stop()


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])