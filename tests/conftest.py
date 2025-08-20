#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for DaiLY tests
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_environment():
    """Mock environment variables for testing"""
    return {
        'ANTHROPIC_API_KEY': 'test_anthropic_key',
        'GMAIL_CLIENT_ID': 'test_gmail_client_id',
        'GMAIL_CLIENT_SECRET': 'test_gmail_client_secret',
        'GMAIL_REFRESH_TOKEN': 'test_gmail_refresh_token',
        'SLACK_BOT_TOKEN': 'xoxb-test-slack-token',
        'TEAMS_CLIENT_ID': 'test_teams_client_id',
        'SECRET_KEY': 'test_secret_key'
    }

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring external services"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (default)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add unit marker to all tests by default
        if not any(mark.name in ['integration', 'slow'] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)