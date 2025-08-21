from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List, Any, Literal
from datetime import datetime

CalendarProvider = Literal["google", "outlook", "apple"]
EventStatus = Literal["confirmed", "tentative", "cancelled"]
AttendeeStatus = Literal["needsAction", "declined", "tentative", "accepted"]
Visibility = Literal["default", "public", "private", "confidential"]
RecurrenceType = Literal["daily", "weekly", "monthly", "yearly"]

class CalendarEvent(BaseModel):
    id: str
    calendar_id: str
    provider: CalendarProvider
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: Optional[str] = None
    location: Optional[str] = None
    status: EventStatus = "confirmed"
    visibility: Visibility = "default"
    is_all_day: bool = False
    created_at: datetime
    updated_at: datetime
    creator_email: Optional[str] = None
    organizer_email: Optional[str] = None
    attendees: List[Dict[str, Any]] = Field(default_factory=list)
    recurrence_rules: Optional[List[str]] = None
    original_start_time: Optional[datetime] = None
    recurring_event_id: Optional[str] = None
    meeting_url: Optional[HttpUrl] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Calendar(BaseModel):
    id: str
    provider: CalendarProvider
    name: str
    description: Optional[str] = None
    timezone: Optional[str] = None
    color: Optional[str] = None
    is_primary: bool = False
    access_role: Optional[str] = None
    selected: bool = True

class Attendee(BaseModel):
    email: str
    display_name: Optional[str] = None
    response_status: AttendeeStatus = "needsAction"
    optional: bool = False
    resource: bool = False
    organizer: bool = False
    comment: Optional[str] = None

class FreeBusyQuery(BaseModel):
    calendar_ids: List[str]
    start_time: datetime
    end_time: datetime

class FreeBusyResponse(BaseModel):
    calendar_id: str
    busy_periods: List[Dict[str, datetime]]
    errors: List[str] = Field(default_factory=list)

class EventFilters(BaseModel):
    calendar_ids: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    search_query: Optional[str] = None
    show_deleted: bool = False
    single_events: bool = True
    max_results: int = Field(default=100, ge=1, le=2500)
    order_by: Literal["startTime", "updated"] = "startTime"

class CreateEventRequest(BaseModel):
    calendar_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: Optional[str] = None
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    visibility: Visibility = "default"
    is_all_day: bool = False
    recurrence_rules: Optional[List[str]] = None
    meeting_url: Optional[str] = None
    reminders: Optional[List[Dict[str, Any]]] = None

class UpdateEventRequest(BaseModel):
    event_id: str
    calendar_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    visibility: Optional[Visibility] = None
    status: Optional[EventStatus] = None

class EventConflict(BaseModel):
    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    calendar_id: str
    conflict_type: Literal["overlap", "adjacent", "same_time"]
    duration_minutes: int

class AvailabilitySlot(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    calendar_ids: List[str]