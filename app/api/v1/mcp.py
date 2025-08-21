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

@router.get("/stream")
async def mcp_stream(poll_seconds: int = 20):
    """Server-Sent Events stream that periodically polls MCP tools and emits new notifications"""
    async def event_generator():
        seen_ids = set()
        while True:
            try:
                # Gmail notifications
                try:
                    gmail_items = await MCPCommunicationClient.call_tool(
                        "list_gmail_notifications", {"query": "is:unread", "max_results": 20}
                    )
                    if isinstance(gmail_items, dict) and "notifications" in gmail_items:
                        gmail_items = gmail_items["notifications"]
                    if isinstance(gmail_items, list):
                        for item in gmail_items:
                            nid = item.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                payload = {
                                    "source": "gmail",
                                    "notification": item,
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
                except Exception as e:
                    logger.warning(f"Gmail stream error: {e}")

                # Slack notifications
                try:
                    slack_items = await MCPCommunicationClient.call_tool(
                        "list_slack_notifications", {"max_results": 20}
                    )
                    if isinstance(slack_items, dict) and "notifications" in slack_items:
                        slack_items = slack_items["notifications"]
                    if isinstance(slack_items, list):
                        for item in slack_items:
                            nid = item.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                payload = {
                                    "source": "slack",
                                    "notification": item,
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
                except Exception as e:
                    logger.warning(f"Slack stream error: {e}")

                # Today's calendar events
                try:
                    today_events = await MCPUserContextClient.call_tool(
                        "get_today_schedule", {"include_all_day": False}
                    )
                    if isinstance(today_events, dict) and "events" in today_events:
                        today_events = today_events["events"]
                    if isinstance(today_events, list):
                        for event in today_events:
                            event_id = event.get("id")
                            if event_id and f"calendar_{event_id}" not in seen_ids:
                                seen_ids.add(f"calendar_{event_id}")
                                payload = {
                                    "source": "calendar",
                                    "notification": {
                                        "id": event_id,
                                        "title": event.get("title", "Calendar Event"),
                                        "start_time": event.get("start_time"),
                                        "type": "calendar_event"
                                    }
                                }
                                yield f"data: {json.dumps(payload, default=str)}\n\n"
                except Exception as e:
                    logger.warning(f"Calendar stream error: {e}")

            except Exception as e:
                logger.error(f"mcp_stream polling error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(max(5, poll_seconds))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

