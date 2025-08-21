import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions

from .models import (
    CalendarEvent, Calendar, EventFilters, CreateEventRequest, 
    UpdateEventRequest, FreeBusyQuery, EventConflict, AvailabilitySlot
)
from .integrations.google_calendar import GoogleCalendarIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 Starting MCP User Context Server...")
server = Server("user-context-server")
print("✅ MCP Server instance created")

print("🔧 Initializing Google Calendar integration...")
try:
    google_calendar = GoogleCalendarIntegration()
    print("✅ Google Calendar integration initialized")
except Exception as e:
    print(f"⚠️ Google Calendar integration failed to initialize: {e}")
    print("💡 Add GOOGLE_CALENDAR_* env vars to .env file to enable Google Calendar integration")
    google_calendar = None

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for user context and calendar management"""
    print("📋 Client requested tool list")
    
    tools = []
    
    if google_calendar:
        tools.extend([
            Tool(
                name="list_calendars",
                description="List all Google calendars accessible to the user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="list_calendar_events",
                description="List calendar events with optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to search (defaults to primary)"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for start time filter"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for end time filter"
                        },
                        "search_query": {
                            "type": "string",
                            "description": "Search query to filter events"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of events to return",
                            "default": 100,
                            "minimum": 1,
                            "maximum": 2500
                        },
                        "show_deleted": {
                            "type": "boolean",
                            "description": "Include deleted events",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="create_calendar_event",
                description="Create a new calendar event",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID where to create the event"
                        },
                        "title": {
                            "type": "string",
                            "description": "Event title/summary"
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for event start"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for event end"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone for the event (e.g., 'America/New_York')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Event location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of attendee email addresses"
                        },
                        "is_all_day": {
                            "type": "boolean",
                            "description": "Whether this is an all-day event",
                            "default": False
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["default", "public", "private", "confidential"],
                            "description": "Event visibility",
                            "default": "default"
                        },
                        "recurrence_rules": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Recurrence rules (RRULE format)"
                        }
                    },
                    "required": ["calendar_id", "title", "start_time", "end_time"]
                }
            ),
            Tool(
                name="update_calendar_event",
                description="Update an existing calendar event",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID to update"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID containing the event"
                        },
                        "title": {
                            "type": "string",
                            "description": "New event title"
                        },
                        "description": {
                            "type": "string",
                            "description": "New event description"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "New ISO-8601 timestamp for event start"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "New ISO-8601 timestamp for event end"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "New timezone for the event"
                        },
                        "location": {
                            "type": "string",
                            "description": "New event location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New list of attendee email addresses"
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["default", "public", "private", "confidential"],
                            "description": "New event visibility"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["confirmed", "tentative", "cancelled"],
                            "description": "New event status"
                        }
                    },
                    "required": ["event_id", "calendar_id"]
                }
            ),
            Tool(
                name="delete_calendar_event",
                description="Delete a calendar event",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID containing the event"
                        },
                        "event_id": {
                            "type": "string",
                            "description": "Event ID to delete"
                        }
                    },
                    "required": ["calendar_id", "event_id"]
                }
            ),
            Tool(
                name="get_calendar_free_busy",
                description="Get free/busy information for specified calendars",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to check"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for start time"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for end time"
                        }
                    },
                    "required": ["calendar_ids", "start_time", "end_time"]
                }
            ),
            Tool(
                name="find_scheduling_conflicts",
                description="Find scheduling conflicts across calendars within a time range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to check for conflicts"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for start time"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for end time"
                        }
                    },
                    "required": ["calendar_ids", "start_time", "end_time"]
                }
            ),
            Tool(
                name="find_available_time_slots",
                description="Find available time slots for scheduling within a time range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to check availability"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for start time"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO-8601 timestamp for end time"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Minimum duration required in minutes",
                            "default": 60,
                            "minimum": 15
                        }
                    },
                    "required": ["calendar_ids", "start_time", "end_time"]
                }
            ),
            Tool(
                name="get_today_schedule",
                description="Get today's schedule across all calendars",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to include (defaults to all)"
                        },
                        "include_all_day": {
                            "type": "boolean",
                            "description": "Include all-day events",
                            "default": True
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_upcoming_events",
                description="Get upcoming events for the next specified days",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days_ahead": {
                            "type": "integer",
                            "description": "Number of days to look ahead",
                            "default": 7,
                            "minimum": 1,
                            "maximum": 30
                        },
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to include"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of events to return",
                            "default": 50
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="analyze_calendar_patterns",
                description="Analyze calendar patterns and provide insights",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of calendar IDs to analyze"
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days to look back for analysis",
                            "default": 30,
                            "minimum": 1,
                            "maximum": 90
                        }
                    },
                    "required": []
                }
            )
        ])
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""
    print(f"🔧 Client called tool: {name} with args: {arguments}")
    
    try:
        if not google_calendar:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Google Calendar integration not available"})
            )]
        
        if name == "list_calendars":
            calendars = await google_calendar.list_calendars()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(calendars),
                    "calendars": [cal.model_dump() for cal in calendars]
                }, default=str)
            )]
        
        elif name == "list_calendar_events":
            filters = EventFilters(
                calendar_ids=arguments.get("calendar_ids"),
                start_time=datetime.fromisoformat(arguments["start_time"]) if arguments.get("start_time") else None,
                end_time=datetime.fromisoformat(arguments["end_time"]) if arguments.get("end_time") else None,
                search_query=arguments.get("search_query"),
                max_results=arguments.get("max_results", 100),
                show_deleted=arguments.get("show_deleted", False)
            )
            
            events = await google_calendar.list_events(filters)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(events),
                    "events": [event.model_dump() for event in events]
                }, default=str)
            )]
        
        elif name == "create_calendar_event":
            request = CreateEventRequest(
                calendar_id=arguments["calendar_id"],
                title=arguments["title"],
                description=arguments.get("description"),
                start_time=datetime.fromisoformat(arguments["start_time"]),
                end_time=datetime.fromisoformat(arguments["end_time"]),
                timezone=arguments.get("timezone"),
                location=arguments.get("location"),
                attendees=arguments.get("attendees", []),
                is_all_day=arguments.get("is_all_day", False),
                visibility=arguments.get("visibility", "default"),
                recurrence_rules=arguments.get("recurrence_rules")
            )
            
            event = await google_calendar.create_event(request)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "event": event.model_dump()
                }, default=str)
            )]
        
        elif name == "update_calendar_event":
            request = UpdateEventRequest(
                event_id=arguments["event_id"],
                calendar_id=arguments["calendar_id"],
                title=arguments.get("title"),
                description=arguments.get("description"),
                start_time=datetime.fromisoformat(arguments["start_time"]) if arguments.get("start_time") else None,
                end_time=datetime.fromisoformat(arguments["end_time"]) if arguments.get("end_time") else None,
                timezone=arguments.get("timezone"),
                location=arguments.get("location"),
                attendees=arguments.get("attendees"),
                visibility=arguments.get("visibility"),
                status=arguments.get("status")
            )
            
            event = await google_calendar.update_event(request)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "event": event.model_dump()
                }, default=str)
            )]
        
        elif name == "delete_calendar_event":
            success = await google_calendar.delete_event(
                arguments["calendar_id"],
                arguments["event_id"]
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": success,
                    "message": "Event deleted successfully" if success else "Event not found"
                })
            )]
        
        elif name == "get_calendar_free_busy":
            query = FreeBusyQuery(
                calendar_ids=arguments["calendar_ids"],
                start_time=datetime.fromisoformat(arguments["start_time"]),
                end_time=datetime.fromisoformat(arguments["end_time"])
            )
            
            freebusy_data = await google_calendar.get_free_busy(query)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": query.model_dump(),
                    "results": [fb.model_dump() for fb in freebusy_data]
                }, default=str)
            )]
        
        elif name == "find_scheduling_conflicts":
            conflicts = await google_calendar.find_conflicts(
                arguments["calendar_ids"],
                datetime.fromisoformat(arguments["start_time"]),
                datetime.fromisoformat(arguments["end_time"])
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "conflict_count": len(conflicts),
                    "conflicts": [conflict.model_dump() for conflict in conflicts]
                }, default=str)
            )]
        
        elif name == "find_available_time_slots":
            available_slots = await google_calendar.find_available_slots(
                arguments["calendar_ids"],
                datetime.fromisoformat(arguments["start_time"]),
                datetime.fromisoformat(arguments["end_time"]),
                arguments.get("duration_minutes", 60)
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "slot_count": len(available_slots),
                    "available_slots": [slot.model_dump() for slot in available_slots]
                }, default=str)
            )]
        
        elif name == "get_today_schedule":
            today = datetime.now().date()
            start_time = datetime.combine(today, datetime.min.time())
            end_time = datetime.combine(today, datetime.max.time())
            
            filters = EventFilters(
                calendar_ids=arguments.get("calendar_ids"),
                start_time=start_time,
                end_time=end_time,
                single_events=True,
                order_by="startTime"
            )
            
            events = await google_calendar.list_events(filters)
            
            if not arguments.get("include_all_day", True):
                events = [e for e in events if not e.is_all_day]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "date": today.isoformat(),
                    "event_count": len(events),
                    "events": [event.model_dump() for event in events]
                }, default=str)
            )]
        
        elif name == "get_upcoming_events":
            days_ahead = arguments.get("days_ahead", 7)
            start_time = datetime.now()
            end_time = start_time + timedelta(days=days_ahead)
            
            filters = EventFilters(
                calendar_ids=arguments.get("calendar_ids"),
                start_time=start_time,
                end_time=end_time,
                max_results=arguments.get("max_results", 50),
                single_events=True,
                order_by="startTime"
            )
            
            events = await google_calendar.list_events(filters)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "days_ahead": days_ahead
                    },
                    "event_count": len(events),
                    "events": [event.model_dump() for event in events]
                }, default=str)
            )]
        
        elif name == "analyze_calendar_patterns":
            days_back = arguments.get("days_back", 30)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            filters = EventFilters(
                calendar_ids=arguments.get("calendar_ids"),
                start_time=start_time,
                end_time=end_time,
                max_results=2500,
                single_events=True
            )
            
            events = await google_calendar.list_events(filters)
            
            analysis = await _analyze_events(events, days_back)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "analysis_period": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "days_analyzed": days_back
                    },
                    "total_events": len(events),
                    "patterns": analysis
                }, default=str)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            })
        )]

async def _analyze_events(events: List[CalendarEvent], days_back: int) -> Dict[str, Any]:
    """Analyze calendar events for patterns and insights"""
    if not events:
        return {"message": "No events found in the specified period"}
    
    daily_counts = {}
    hourly_distribution = [0] * 24
    event_durations = []
    attendee_counts = []
    location_counts = {}
    organizer_counts = {}
    
    for event in events:
        event_date = event.start_time.date().isoformat()
        daily_counts[event_date] = daily_counts.get(event_date, 0) + 1
        
        hour = event.start_time.hour
        hourly_distribution[hour] += 1
        
        duration_minutes = int((event.end_time - event.start_time).total_seconds() / 60)
        event_durations.append(duration_minutes)
        
        attendee_counts.append(len(event.attendees))
        
        if event.location:
            location_counts[event.location] = location_counts.get(event.location, 0) + 1
        
        if event.organizer_email:
            organizer_counts[event.organizer_email] = organizer_counts.get(event.organizer_email, 0) + 1
    
    avg_events_per_day = len(events) / days_back
    avg_duration = sum(event_durations) / len(event_durations) if event_durations else 0
    avg_attendees = sum(attendee_counts) / len(attendee_counts) if attendee_counts else 0
    
    busiest_hour = hourly_distribution.index(max(hourly_distribution))
    top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_organizers = sorted(organizer_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "summary": {
            "average_events_per_day": round(avg_events_per_day, 1),
            "average_duration_minutes": round(avg_duration, 1),
            "average_attendees_per_event": round(avg_attendees, 1),
            "busiest_hour": busiest_hour,
            "total_meeting_hours": round(sum(event_durations) / 60, 1)
        },
        "time_patterns": {
            "hourly_distribution": hourly_distribution,
            "daily_counts": daily_counts
        },
        "top_locations": [{"location": loc, "count": count} for loc, count in top_locations],
        "top_organizers": [{"organizer": org, "count": count} for org, count in top_organizers],
        "duration_stats": {
            "min_minutes": min(event_durations) if event_durations else 0,
            "max_minutes": max(event_durations) if event_durations else 0,
            "avg_minutes": round(avg_duration, 1)
        }
    }

async def run():
    """Run the server with lifespan management."""
    print("🌐 Starting stdio server...")
    
    async with stdio_server() as (read_stream, write_stream):
        print("📡 MCP User Context Server running and listening for client connections...")
        print("💡 Server is ready to process calendar requests!")
        print("⏳ Waiting for MCP client to connect...")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="user-context-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(run())