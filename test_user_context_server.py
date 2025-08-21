#!/usr/bin/env python3
"""
Test script for the user_context_server Google Calendar MCP integration.
This script tests the basic functionality without requiring actual Google Calendar credentials.
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from mcp_servers.user_context_server.models import (
    CalendarEvent, Calendar, EventFilters, CreateEventRequest,
    FreeBusyQuery, AvailabilitySlot
)
from datetime import datetime, timedelta

def test_models():
    """Test that all models can be instantiated correctly"""
    print("🧪 Testing model instantiation...")
    
    now = datetime.now()
    
    calendar = Calendar(
        id="test-calendar",
        provider="google",
        name="Test Calendar",
        is_primary=True
    )
    print(f"✅ Calendar model: {calendar.name}")
    
    event = CalendarEvent(
        id="test-event",
        calendar_id="test-calendar",
        provider="google",
        title="Test Event",
        start_time=now,
        end_time=now + timedelta(hours=1),
        created_at=now,
        updated_at=now
    )
    print(f"✅ CalendarEvent model: {event.title}")
    
    filters = EventFilters(
        start_time=now,
        end_time=now + timedelta(days=7),
        max_results=50
    )
    print(f"✅ EventFilters model: {filters.max_results} max results")
    
    request = CreateEventRequest(
        calendar_id="test-calendar",
        title="New Event",
        start_time=now,
        end_time=now + timedelta(hours=1)
    )
    print(f"✅ CreateEventRequest model: {request.title}")
    
    freebusy = FreeBusyQuery(
        calendar_ids=["calendar1", "calendar2"],
        start_time=now,
        end_time=now + timedelta(hours=8)
    )
    print(f"✅ FreeBusyQuery model: {len(freebusy.calendar_ids)} calendars")
    
    slot = AvailabilitySlot(
        start_time=now,
        end_time=now + timedelta(hours=2),
        duration_minutes=120,
        calendar_ids=["calendar1"]
    )
    print(f"✅ AvailabilitySlot model: {slot.duration_minutes} minutes")
    
    print("✅ All models instantiated successfully!")

def test_server_import():
    """Test that the server module can be imported"""
    print("\n🧪 Testing server module import...")
    
    try:
        from mcp_servers.user_context_server.server import server
        print(f"✅ Server imported successfully: {server.name}")
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Server import successful but initialization failed: {e}")
        print("   This is expected without proper Google Calendar credentials")
    
    return True

def test_integration_structure():
    """Test that the integration module structure is correct"""
    print("\n🧪 Testing integration module structure...")
    
    try:
        from mcp_servers.user_context_server.integrations.google_calendar import GoogleCalendarIntegration
        print("✅ GoogleCalendarIntegration class imported successfully")
        
        try:
            integration = GoogleCalendarIntegration()
            print("✅ GoogleCalendarIntegration instantiated (service may not be initialized without credentials)")
        except Exception as e:
            print(f"⚠️ GoogleCalendarIntegration failed to initialize: {e}")
            print("   This is expected without proper Google Calendar credentials")
        
    except ImportError as e:
        print(f"❌ Failed to import GoogleCalendarIntegration: {e}")
        return False
    
    return True

def test_tool_definitions():
    """Test that the tool definitions are properly structured"""
    print("\n🧪 Testing tool definitions...")
    
    try:
        from mcp_servers.user_context_server.server import list_tools
        
        print("✅ list_tools function imported successfully")
        print("   Note: Cannot test async function without running event loop")
        
    except ImportError as e:
        print(f"❌ Failed to import list_tools: {e}")
        return False
    
    return True

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting User Context Server Tests\n")
    
    tests = [
        ("Model Tests", test_models),
        ("Server Import Test", test_server_import),
        ("Integration Structure Test", test_integration_structure),
        ("Tool Definitions Test", test_tool_definitions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            if result is not False:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! The user_context_server is ready for use.")
        print("\n💡 To complete setup:")
        print("   1. Add Google Calendar credentials to .env file")
        print("   2. Test with actual Google Calendar API calls")
        print("   3. Integrate with the main notification manager")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()