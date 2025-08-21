"""
MCP-backed endpoints to surface Gmail, Slack, and Google Calendar data in the frontend
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse

from ...core.mcp_client import MCPCommunicationClient, MCPUserContextClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from agent.client import NotificationAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# Gmail endpoints
@router.get("/gmail/notifications")
async def gmail_notifications(query: str = "", max_results: int = 20):
    """Get Gmail notifications"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "list_gmail_notifications", {"query": query, "max_results": max_results}
        )
        if isinstance(payload, dict) and "notifications" in payload:
            return payload["notifications"]
        return payload or []
    except Exception as e:
        logger.error(f"gmail_notifications failed: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail notifications error: {str(e)}")

@router.get("/gmail/sender-importance/{sender_email}")
async def gmail_sender_importance(sender_email: str, days_back: int = 30):
    """Analyze sender importance"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "analyze_sender_importance", {"sender_email": sender_email, "days_back": days_back}
        )
        return payload
    except Exception as e:
        logger.error(f"gmail_sender_importance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/conversations/{contact_email}")
async def gmail_conversations(contact_email: str, days_back: int = 7, max_messages: int = 10):
    """Get recent conversations with a contact"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "get_recent_conversations", {
                "contact_email": contact_email,
                "days_back": days_back,
                "max_messages": max_messages
            }
        )
        return payload
    except Exception as e:
        logger.error(f"gmail_conversations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Slack endpoints
@router.get("/slack/notifications")
async def slack_notifications(channel_filter: str = "", max_results: int = 20, since_timestamp: str = ""):
    """Get Slack notifications"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "list_slack_notifications", {
                "channel_filter": channel_filter,
                "max_results": max_results,
                "since_timestamp": since_timestamp
            }
        )
        if isinstance(payload, dict) and "notifications" in payload:
            return payload["notifications"]
        return payload or []
    except Exception as e:
        logger.error(f"slack_notifications failed: {e}")
        raise HTTPException(status_code=500, detail=f"Slack notifications error: {str(e)}")

@router.get("/slack/user-importance/{user_id}")
async def slack_user_importance(user_id: str, days_back: int = 30):
    """Analyze Slack user importance"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "analyze_slack_user_importance", {"user_id": user_id, "days_back": days_back}
        )
        return payload
    except Exception as e:
        logger.error(f"slack_user_importance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slack/conversations/{user_id}")
async def slack_conversations(user_id: str, days_back: int = 7, max_messages: int = 10):
    """Get recent Slack conversations with a user"""
    try:
        payload = await MCPCommunicationClient.call_tool(
            "get_slack_conversations", {
                "user_id": user_id,
                "days_back": days_back,
                "max_messages": max_messages
            }
        )
        return payload
    except Exception as e:
        logger.error(f"slack_conversations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Google Calendar endpoints
@router.get("/calendar/calendars")
async def list_calendars():
    """List all Google calendars"""
    try:
        payload = await MCPUserContextClient.call_tool("list_calendars", {})
        if isinstance(payload, dict) and "calendars" in payload:
            return payload["calendars"]
        return payload or []
    except Exception as e:
        logger.error(f"list_calendars failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar list error: {str(e)}")

@router.get("/calendar/events")
async def list_calendar_events(
    calendar_ids: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    search_query: Optional[str] = None,
    max_results: int = 100
):
    """List calendar events with filters"""
    try:
        args = {"max_results": max_results}
        if calendar_ids:
            args["calendar_ids"] = calendar_ids.split(",")
        if start_time:
            args["start_time"] = start_time
        if end_time:
            args["end_time"] = end_time
        if search_query:
            args["search_query"] = search_query
            
        payload = await MCPUserContextClient.call_tool("list_calendar_events", args)
        if isinstance(payload, dict) and "events" in payload:
            return payload["events"]
        return payload or []
    except Exception as e:
        logger.error(f"list_calendar_events failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar events error: {str(e)}")

@router.post("/calendar/events")
async def create_calendar_event(event_data: Dict[str, Any]):
    """Create a new calendar event"""
    try:
        payload = await MCPUserContextClient.call_tool("create_calendar_event", event_data)
        return payload
    except Exception as e:
        logger.error(f"create_calendar_event failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create event error: {str(e)}")

@router.put("/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, event_data: Dict[str, Any]):
    """Update an existing calendar event"""
    try:
        event_data["event_id"] = event_id
        payload = await MCPUserContextClient.call_tool("update_calendar_event", event_data)
        return payload
    except Exception as e:
        logger.error(f"update_calendar_event failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update event error: {str(e)}")

@router.delete("/calendar/events/{calendar_id}/{event_id}")
async def delete_calendar_event(calendar_id: str, event_id: str):
    """Delete a calendar event"""
    try:
        payload = await MCPUserContextClient.call_tool(
            "delete_calendar_event", {"calendar_id": calendar_id, "event_id": event_id}
        )
        return payload
    except Exception as e:
        logger.error(f"delete_calendar_event failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete event error: {str(e)}")

@router.get("/calendar/today")
async def get_today_schedule(calendar_ids: Optional[str] = None, include_all_day: bool = True):
    """Get today's schedule"""
    try:
        args = {"include_all_day": include_all_day}
        if calendar_ids:
            args["calendar_ids"] = calendar_ids.split(",")
            
        payload = await MCPUserContextClient.call_tool("get_today_schedule", args)
        if isinstance(payload, dict) and "events" in payload:
            return payload["events"]
        return payload or []
    except Exception as e:
        logger.error(f"get_today_schedule failed: {e}")
        raise HTTPException(status_code=500, detail=f"Today's schedule error: {str(e)}")

@router.get("/calendar/upcoming")
async def get_upcoming_events(days_ahead: int = 7, calendar_ids: Optional[str] = None, max_results: int = 50):
    """Get upcoming events"""
    try:
        args = {"days_ahead": days_ahead, "max_results": max_results}
        if calendar_ids:
            args["calendar_ids"] = calendar_ids.split(",")
            
        payload = await MCPUserContextClient.call_tool("get_upcoming_events", args)
        if isinstance(payload, dict) and "events" in payload:
            return payload["events"]
        return payload or []
    except Exception as e:
        logger.error(f"get_upcoming_events failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upcoming events error: {str(e)}")

@router.get("/calendar/free-busy")
async def get_calendar_free_busy(
    calendar_ids: str,
    start_time: str,
    end_time: str
):
    """Get free/busy information for calendars"""
    try:
        payload = await MCPUserContextClient.call_tool(
            "get_calendar_free_busy", {
                "calendar_ids": calendar_ids.split(","),
                "start_time": start_time,
                "end_time": end_time
            }
        )
        return payload
    except Exception as e:
        logger.error(f"get_calendar_free_busy failed: {e}")
        raise HTTPException(status_code=500, detail=f"Free/busy error: {str(e)}")

@router.get("/calendar/available-slots")
async def find_available_time_slots(
    calendar_ids: str,
    start_time: str,
    end_time: str,
    duration_minutes: int = 60
):
    """Find available time slots"""
    try:
        payload = await MCPUserContextClient.call_tool(
            "find_available_time_slots", {
                "calendar_ids": calendar_ids.split(","),
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": duration_minutes
            }
        )
        if isinstance(payload, dict) and "available_slots" in payload:
            return payload["available_slots"]
        return payload or []
    except Exception as e:
        logger.error(f"find_available_time_slots failed: {e}")
        raise HTTPException(status_code=500, detail=f"Available slots error: {str(e)}")

@router.get("/test-stream")
async def test_mcp_stream(poll_seconds: int = 10):
    """Test stream with mock data to verify classification is working"""
    async def event_generator():
        seen_ids = set()
        agent = NotificationAgent()
        await agent.initialize_mcp_servers()
        
        # Mock notifications to test with
        mock_notifications = [
            {
                "id": "test_gmail_urgent",
                "sender": "boss@company.com",
                "subject": "URGENT: Production server down",
                "content": "The main server is down and clients can't access our service. Need immediate action.",
                "timestamp": datetime.now().isoformat(),
                "type": "email"
            },
            {
                "id": "test_slack_question", 
                "sender": "sarah.developer",
                "subject": "Quick question",
                "content": "Hey, what's the API endpoint for user data?",
                "timestamp": datetime.now().isoformat(),
                "type": "message"
            },
            {
                "id": "test_newsletter",
                "sender": "newsletter@techcrunch.com", 
                "subject": "Daily Tech News",
                "content": "Today's top tech stories...",
                "timestamp": datetime.now().isoformat(),
                "type": "newsletter"
            }
        ]
        
        counter = 0
        while True:
            try:
                # Send one mock notification per cycle to see real-time classification
                if counter < len(mock_notifications):
                    raw_notifications = []
                    mock_notif = mock_notifications[counter]
                    
                    if mock_notif["id"] not in seen_ids:
                        seen_ids.add(mock_notif["id"])
                        
                        notification = {
                            **mock_notif,
                            "platform": "gmail",
                            "source": "gmail",
                            "original_data": mock_notif
                        }
                        raw_notifications.append(notification)
                        
                        # Classify the notification
                        logger.info(f"Test: Classifying notification {counter + 1}: {mock_notif['subject']}")
                        result = await agent.process_notifications(raw_notifications)
                        
                        # Emit classified notification
                        for decision in result.decisions:
                            original = next((n for n in raw_notifications if n['id'] == decision.notification_id), None)
                            if original:
                                enhanced_notification = {
                                    **original,
                                    "classification": {
                                        "decision": decision.decision,
                                        "urgency_score": decision.urgency_score,
                                        "importance_score": decision.importance_score,
                                        "reasoning": decision.reasoning,
                                        "suggested_action": decision.suggested_action,
                                        "batch_group": decision.batch_group,
                                        "context_used": decision.context_used
                                    }
                                }
                                
                                payload = {
                                    "source": "test",
                                    "notification": enhanced_notification,
                                    "analysis_summary": result.analysis_summary,
                                    "test_mode": True
                                }
                                yield f"data: {json.dumps(payload, default=str)}\n\n"
                        
                        counter += 1
                
                else:
                    # After all test notifications, send a completion message
                    payload = {
                        "source": "test",
                        "type": "test_complete",
                        "message": f"Test complete! Classified {len(mock_notifications)} notifications. Stream will continue polling real data."
                    }
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                    counter = 0  # Reset for continuous testing
                    seen_ids.clear()
                
            except Exception as e:
                logger.error(f"Test stream error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e), 'test_mode': True})}\n\n"
            
            await asyncio.sleep(max(2, poll_seconds))
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/stream")
async def mcp_stream(poll_seconds: int = 20):
    """Server-Sent Events stream that periodically polls MCP tools, classifies notifications, and emits classified results"""
    async def event_generator():
        seen_ids = set()
        agent = NotificationAgent()
        await agent.initialize_mcp_servers()
        
        poll_cycle = 0
        
        import signal
        shutdown_flag = False
        
        def signal_handler(signum, frame):
            nonlocal shutdown_flag
            shutdown_flag = True
            print("\n🛑 Shutdown signal received, stopping stream...")
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while not shutdown_flag:
            try:
                poll_cycle += 1
                print(f"\n{'='*80}")
                print(f"🔄 STREAM POLLING CYCLE #{poll_cycle} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*80}")
                
                raw_notifications = []
                
                # Gmail notifications
                print(f"📧 GMAIL: Calling list_gmail_notifications...")
                try:
                    gmail_items = await MCPCommunicationClient.call_tool(
                        "list_gmail_notifications", {"query": "is:unread", "max_results": 20}
                    )
                    print(f"📧 GMAIL RESPONSE: {type(gmail_items)} = {gmail_items}")
                    
                    if isinstance(gmail_items, dict) and "notifications" in gmail_items:
                        gmail_items = gmail_items["notifications"]
                        print(f"📧 GMAIL: Extracted {len(gmail_items)} notifications from dict")
                    elif isinstance(gmail_items, list):
                        print(f"📧 GMAIL: Got {len(gmail_items)} notifications directly")
                    else:
                        print(f"📧 GMAIL: Unexpected response type: {type(gmail_items)}")
                        
                    if isinstance(gmail_items, list):
                        new_gmail = 0
                        for item in gmail_items:
                            nid = item.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                new_gmail += 1
                                # Format for classification agent
                                notification = {
                                    "id": nid,
                                    "platform": "gmail",
                                    "sender": item.get("sender", item.get("from", "unknown")),
                                    "subject": item.get("subject", item.get("title", "No subject")),
                                    "content": item.get("content", item.get("body", "")),
                                    "timestamp": item.get("timestamp", item.get("date", datetime.now().isoformat())),
                                    "type": item.get("type", "email"),
                                    "source": "gmail",
                                    "original_data": item
                                }
                                raw_notifications.append(notification)
                                print(f"📧 GMAIL NEW: {nid} - {notification['subject']}")
                        print(f"📧 GMAIL: Found {new_gmail} new notifications")
                except Exception as e:
                    print(f"❌ GMAIL ERROR: {e}")
                    logger.warning(f"Gmail stream error: {e}")

                # Slack notifications
                print(f"💬 SLACK: Calling list_slack_notifications...")
                try:
                    slack_items = await MCPCommunicationClient.call_tool(
                        "list_slack_notifications", {"max_results": 20}
                    )
                    print(f"💬 SLACK RESPONSE: {type(slack_items)} = {slack_items}")
                    
                    if isinstance(slack_items, dict) and "notifications" in slack_items:
                        slack_items = slack_items["notifications"]
                        print(f"💬 SLACK: Extracted {len(slack_items)} notifications from dict")
                    elif isinstance(slack_items, list):
                        print(f"💬 SLACK: Got {len(slack_items)} notifications directly")
                    else:
                        print(f"💬 SLACK: Unexpected response type: {type(slack_items)}")
                        
                    if isinstance(slack_items, list):
                        new_slack = 0
                        for item in slack_items:
                            nid = item.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                new_slack += 1
                                # Format for classification agent
                                notification = {
                                    "id": nid,
                                    "platform": "slack",
                                    "sender": item.get("sender", item.get("user", "unknown")),
                                    "subject": item.get("subject", item.get("text", "Slack message"))[:100],
                                    "content": item.get("content", item.get("text", "")),
                                    "timestamp": item.get("timestamp", item.get("ts", datetime.now().isoformat())),
                                    "type": item.get("type", "message"),
                                    "source": "slack",
                                    "original_data": item
                                }
                                raw_notifications.append(notification)
                                print(f"💬 SLACK NEW: {nid} - {notification['subject']}")
                        print(f"💬 SLACK: Found {new_slack} new notifications")
                except Exception as e:
                    print(f"❌ SLACK ERROR: {e}")
                    logger.warning(f"Slack stream error: {e}")

                # Today's calendar events
                print(f"📅 CALENDAR: Calling get_today_schedule...")
                try:
                    today_events = await MCPUserContextClient.call_tool(
                        "get_today_schedule", {"include_all_day": False}
                    )
                    print(f"📅 CALENDAR RESPONSE: {type(today_events)} = {today_events}")
                    
                    if isinstance(today_events, dict) and "events" in today_events:
                        today_events = today_events["events"]
                        print(f"📅 CALENDAR: Extracted {len(today_events)} events from dict")
                    elif isinstance(today_events, list):
                        print(f"📅 CALENDAR: Got {len(today_events)} events directly")
                    else:
                        print(f"📅 CALENDAR: Unexpected response type: {type(today_events)}")
                        
                    if isinstance(today_events, list):
                        new_calendar = 0
                        for event in today_events:
                            event_id = event.get("id")
                            calendar_id = f"calendar_{event_id}"
                            if event_id and calendar_id not in seen_ids:
                                seen_ids.add(calendar_id)
                                new_calendar += 1
                                # Format for classification agent
                                notification = {
                                    "id": calendar_id,
                                    "platform": "calendar",
                                    "sender": "calendar@system.com",
                                    "subject": event.get("title", event.get("summary", "Calendar Event")),
                                    "content": f"Event: {event.get('title', 'Calendar Event')} at {event.get('start_time', 'Unknown time')}",
                                    "timestamp": event.get("start_time", datetime.now().isoformat()),
                                    "type": "calendar_event",
                                    "source": "calendar",
                                    "original_data": event
                                }
                                raw_notifications.append(notification)
                                print(f"📅 CALENDAR NEW: {calendar_id} - {notification['subject']}")
                        print(f"📅 CALENDAR: Found {new_calendar} new notifications")
                except Exception as e:
                    print(f"❌ CALENDAR ERROR: {e}")
                    logger.warning(f"Calendar stream error: {e}")

                print(f"📊 SUMMARY: Found {len(raw_notifications)} total new notifications to classify")

                # Process notifications through classification agent if we have any new ones
                if raw_notifications:
                    try:
                        print(f"\n🤖 CLASSIFICATION: Processing {len(raw_notifications)} notifications...")
                        print("🤖 INPUT TO MODEL:")
                        for i, notif in enumerate(raw_notifications, 1):
                            print(f"  {i}. {notif['platform']}: {notif['subject']} (from: {notif['sender']})")
                        
                        result = await agent.process_notifications(raw_notifications)
                        
                        print(f"\n🤖 MODEL RESPONSE:")
                        print(f"  Analysis: {result.analysis_summary}")
                        print(f"  Decisions: {len(result.decisions)}")
                        print(f"  Batch Groups: {len(result.batch_groups)}")
                        
                        # Emit classified notifications
                        emitted_count = 0
                        for decision in result.decisions:
                            print(f"\n  📋 DECISION for {decision.notification_id}:")
                            print(f"     🔥 Priority: {decision.decision} (U:{decision.urgency_score}/10, I:{decision.importance_score}/10)")
                            print(f"     💭 Reasoning: {decision.reasoning}")
                            print(f"     🎯 Action: {decision.suggested_action}")
                            if decision.batch_group:
                                print(f"     📦 Batch Group: {decision.batch_group}")
                            
                            # Find original notification data
                            original = next((n for n in raw_notifications if n['id'] == decision.notification_id), None)
                            if original:
                                enhanced_notification = {
                                    **original,
                                    "classification": {
                                        "decision": decision.decision,
                                        "urgency_score": decision.urgency_score,  
                                        "importance_score": decision.importance_score,
                                        "reasoning": decision.reasoning,
                                        "suggested_action": decision.suggested_action,
                                        "batch_group": decision.batch_group,
                                        "context_used": decision.context_used
                                    }
                                }
                                
                                payload = {
                                    "source": original["source"],
                                    "notification": enhanced_notification,
                                    "analysis_summary": result.analysis_summary
                                }
                                yield f"data: {json.dumps(payload, default=str)}\n\n"
                                emitted_count += 1
                        
                        print(f"\n📤 EMITTED: {emitted_count} classified notifications to dashboard")
                        
                        # Also emit batch group information if available
                        if result.batch_groups:
                            batch_payload = {
                                "source": "system",
                                "type": "batch_groups",
                                "batch_groups": {
                                    name: {
                                        "notifications": group.notifications,
                                        "summary": group.summary,
                                        "suggested_timing": group.suggested_timing
                                    }
                                    for name, group in result.batch_groups.items()
                                }
                            }
                            yield f"data: {json.dumps(batch_payload, default=str)}\n\n"
                            print(f"📤 EMITTED: Batch group information")
                            
                    except Exception as e:
                        print(f"❌ CLASSIFICATION ERROR: {e}")
                        logger.error(f"Classification error: {e}")
                        # Fallback: emit unclassified notifications
                        for notification in raw_notifications:
                            payload = {
                                "source": notification["source"],
                                "notification": {
                                    **notification,
                                    "classification": {
                                        "decision": "BATCH",
                                        "urgency_score": 5,
                                        "importance_score": 5,
                                        "reasoning": f"Classification failed: {str(e)}",
                                        "suggested_action": "Review manually",
                                        "batch_group": "unclassified"
                                    }
                                },
                                "error": f"Classification failed: {str(e)}"
                            }
                            yield f"data: {json.dumps(payload, default=str)}\n\n"
                else:
                    print("⏸️  NO NEW NOTIFICATIONS - Skipping classification")

                print(f"\n💤 SLEEPING for {poll_seconds} seconds until next cycle...")
                print(f"👁️  Currently tracking {len(seen_ids)} seen notification IDs")

            except Exception as e:
                print(f"❌ POLLING CYCLE ERROR: {e}")
                logger.error(f"mcp_stream polling error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            if not shutdown_flag:
                await asyncio.sleep(max(5, poll_seconds))
        
        print("🏁 Stream stopped gracefully")
        yield f"event: shutdown\ndata: {json.dumps({'message': 'Stream stopped'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

