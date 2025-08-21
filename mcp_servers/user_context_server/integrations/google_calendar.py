import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

try:
    from ..models import (
        CalendarEvent, Calendar, FreeBusyQuery, FreeBusyResponse,
        EventFilters, CreateEventRequest, UpdateEventRequest, EventConflict,
        AvailabilitySlot
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from mcp_servers.user_context_server.models import (
        CalendarEvent, Calendar, FreeBusyQuery, FreeBusyResponse,
        EventFilters, CreateEventRequest, UpdateEventRequest, EventConflict,
        AvailabilitySlot
    )

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]

class GoogleCalendarIntegration:
    """Google Calendar integration for user context and scheduling"""
    
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _mint_access_token(self) -> str:
        """Generate access token from refresh token"""
        refresh = os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN")
        cid = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
        csec = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
        
        if not all([refresh, cid, csec]):
            raise RuntimeError("Missing env: GOOGLE_CALENDAR_REFRESH_TOKEN / GOOGLE_CALENDAR_CLIENT_ID / GOOGLE_CALENDAR_CLIENT_SECRET")
        
        creds = Credentials(
            None,
            refresh_token=refresh,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cid,
            client_secret=csec,
            scopes=SCOPES
        )
        creds.refresh(Request())
        return creds.token
    
    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            token = self._mint_access_token()
            creds = Credentials(token=token)
            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Failed to initialize Google Calendar service: {e}")
            self.service = None
    
    def _parse_datetime(self, dt_dict: Dict[str, Any]) -> datetime:
        """Parse Google Calendar datetime format"""
        if 'dateTime' in dt_dict:
            return datetime.fromisoformat(dt_dict['dateTime'].replace('Z', '+00:00'))
        elif 'date' in dt_dict:
            return datetime.fromisoformat(dt_dict['date'] + 'T00:00:00+00:00')
        else:
            raise ValueError("Invalid datetime format")
    
    def _format_datetime(self, dt: datetime, is_all_day: bool = False) -> Dict[str, str]:
        """Format datetime for Google Calendar API"""
        if is_all_day:
            return {'date': dt.date().isoformat()}
        else:
            return {'dateTime': dt.isoformat(), 'timeZone': 'UTC'}
    
    def _convert_to_calendar_event(self, event_data: Dict[str, Any], calendar_id: str) -> CalendarEvent:
        """Convert Google Calendar event to our CalendarEvent model"""
        start_time = self._parse_datetime(event_data['start'])
        end_time = self._parse_datetime(event_data['end'])
        
        attendees = []
        if 'attendees' in event_data:
            for attendee in event_data['attendees']:
                attendees.append({
                    'email': attendee.get('email', ''),
                    'display_name': attendee.get('displayName'),
                    'response_status': attendee.get('responseStatus', 'needsAction'),
                    'optional': attendee.get('optional', False),
                    'organizer': attendee.get('organizer', False)
                })
        
        return CalendarEvent(
            id=event_data['id'],
            calendar_id=calendar_id,
            provider="google",
            title=event_data.get('summary', 'No Title'),
            description=event_data.get('description'),
            start_time=start_time,
            end_time=end_time,
            timezone=event_data['start'].get('timeZone'),
            location=event_data.get('location'),
            status=event_data.get('status', 'confirmed'),
            visibility=event_data.get('visibility', 'default'),
            is_all_day='date' in event_data['start'],
            created_at=datetime.fromisoformat(event_data['created'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(event_data['updated'].replace('Z', '+00:00')),
            creator_email=event_data.get('creator', {}).get('email'),
            organizer_email=event_data.get('organizer', {}).get('email'),
            attendees=attendees,
            recurrence_rules=event_data.get('recurrence'),
            original_start_time=self._parse_datetime(event_data['originalStartTime']) if 'originalStartTime' in event_data else None,
            recurring_event_id=event_data.get('recurringEventId'),
            meeting_url=event_data.get('hangoutLink') or event_data.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri'),
            metadata={
                'google_event_type': event_data.get('eventType'),
                'google_sequence': event_data.get('sequence'),
                'google_transparency': event_data.get('transparency'),
                'google_ical_uid': event_data.get('iCalUID')
            }
        )
    
    async def list_calendars(self) -> List[Calendar]:
        """List all calendars accessible to the user"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        try:
            calendars_result = self.service.calendarList().list().execute()
            calendars = []
            
            for cal_data in calendars_result.get('items', []):
                calendar = Calendar(
                    id=cal_data['id'],
                    provider="google",
                    name=cal_data['summary'],
                    description=cal_data.get('description'),
                    timezone=cal_data.get('timeZone'),
                    color=cal_data.get('backgroundColor'),
                    is_primary=cal_data.get('primary', False),
                    access_role=cal_data.get('accessRole'),
                    selected=cal_data.get('selected', True)
                )
                calendars.append(calendar)
            
            return calendars
        except HttpError as e:
            raise RuntimeError(f"Failed to list calendars: {e}")
    
    async def list_events(self, filters: EventFilters) -> List[CalendarEvent]:
        """List events with optional filters"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        events = []
        calendar_ids = filters.calendar_ids or ['primary']
        
        for calendar_id in calendar_ids:
            try:
                params = {
                    'calendarId': calendar_id,
                    'maxResults': filters.max_results,
                    'singleEvents': filters.single_events,
                    'orderBy': filters.order_by,
                    'showDeleted': filters.show_deleted
                }
                
                if filters.start_time:
                    params['timeMin'] = filters.start_time.isoformat()
                if filters.end_time:
                    params['timeMax'] = filters.end_time.isoformat()
                if filters.search_query:
                    params['q'] = filters.search_query
                
                events_result = self.service.events().list(**params).execute()
                
                for event_data in events_result.get('items', []):
                    if 'start' in event_data:
                        event = self._convert_to_calendar_event(event_data, calendar_id)
                        events.append(event)
                        
            except HttpError as e:
                print(f"Failed to list events for calendar {calendar_id}: {e}")
                continue
        
        return events
    
    async def create_event(self, request: CreateEventRequest) -> CalendarEvent:
        """Create a new calendar event"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        event_body = {
            'summary': request.title,
            'start': self._format_datetime(request.start_time, request.is_all_day),
            'end': self._format_datetime(request.end_time, request.is_all_day),
            'visibility': request.visibility
        }
        
        if request.description:
            event_body['description'] = request.description
        if request.location:
            event_body['location'] = request.location
        if request.timezone:
            if not request.is_all_day:
                event_body['start']['timeZone'] = request.timezone
                event_body['end']['timeZone'] = request.timezone
        
        if request.attendees:
            event_body['attendees'] = [{'email': email} for email in request.attendees]
        
        if request.recurrence_rules:
            event_body['recurrence'] = request.recurrence_rules
        
        if request.reminders:
            event_body['reminders'] = {'useDefault': False, 'overrides': request.reminders}
        
        try:
            created_event = self.service.events().insert(
                calendarId=request.calendar_id,
                body=event_body
            ).execute()
            
            return self._convert_to_calendar_event(created_event, request.calendar_id)
        except HttpError as e:
            raise RuntimeError(f"Failed to create event: {e}")
    
    async def update_event(self, request: UpdateEventRequest) -> CalendarEvent:
        """Update an existing calendar event"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        try:
            existing_event = self.service.events().get(
                calendarId=request.calendar_id,
                eventId=request.event_id
            ).execute()
            
            if request.title is not None:
                existing_event['summary'] = request.title
            if request.description is not None:
                existing_event['description'] = request.description
            if request.location is not None:
                existing_event['location'] = request.location
            if request.visibility is not None:
                existing_event['visibility'] = request.visibility
            if request.status is not None:
                existing_event['status'] = request.status
            
            if request.start_time is not None and request.end_time is not None:
                is_all_day = 'date' in existing_event['start']
                existing_event['start'] = self._format_datetime(request.start_time, is_all_day)
                existing_event['end'] = self._format_datetime(request.end_time, is_all_day)
                
                if request.timezone and not is_all_day:
                    existing_event['start']['timeZone'] = request.timezone
                    existing_event['end']['timeZone'] = request.timezone
            
            if request.attendees is not None:
                existing_event['attendees'] = [{'email': email} for email in request.attendees]
            
            updated_event = self.service.events().update(
                calendarId=request.calendar_id,
                eventId=request.event_id,
                body=existing_event
            ).execute()
            
            return self._convert_to_calendar_event(updated_event, request.calendar_id)
        except HttpError as e:
            raise RuntimeError(f"Failed to update event: {e}")
    
    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete a calendar event"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return False
            raise RuntimeError(f"Failed to delete event: {e}")
    
    async def get_free_busy(self, query: FreeBusyQuery) -> List[FreeBusyResponse]:
        """Get free/busy information for specified calendars"""
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized")
        
        body = {
            'timeMin': query.start_time.isoformat(),
            'timeMax': query.end_time.isoformat(),
            'items': [{'id': cal_id} for cal_id in query.calendar_ids]
        }
        
        try:
            freebusy_result = self.service.freebusy().query(body=body).execute()
            responses = []
            
            for calendar_id in query.calendar_ids:
                cal_data = freebusy_result['calendars'].get(calendar_id, {})
                busy_periods = []
                
                for busy in cal_data.get('busy', []):
                    busy_periods.append({
                        'start': datetime.fromisoformat(busy['start'].replace('Z', '+00:00')),
                        'end': datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    })
                
                errors = cal_data.get('errors', [])
                error_messages = [error.get('reason', 'Unknown error') for error in errors]
                
                responses.append(FreeBusyResponse(
                    calendar_id=calendar_id,
                    busy_periods=busy_periods,
                    errors=error_messages
                ))
            
            return responses
        except HttpError as e:
            raise RuntimeError(f"Failed to get free/busy information: {e}")
    
    async def find_conflicts(self, calendar_ids: List[str], start_time: datetime, end_time: datetime) -> List[EventConflict]:
        """Find scheduling conflicts within specified time range"""
        filters = EventFilters(
            calendar_ids=calendar_ids,
            start_time=start_time,
            end_time=end_time,
            single_events=True
        )
        
        events = await self.list_events(filters)
        conflicts = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if self._events_conflict(event1, event2):
                    conflict_type = self._get_conflict_type(event1, event2)
                    duration = self._get_overlap_duration(event1, event2)
                    
                    conflicts.append(EventConflict(
                        event_id=event1.id,
                        title=event1.title,
                        start_time=event1.start_time,
                        end_time=event1.end_time,
                        calendar_id=event1.calendar_id,
                        conflict_type=conflict_type,
                        duration_minutes=duration
                    ))
        
        return conflicts
    
    def _events_conflict(self, event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events conflict"""
        return (event1.start_time < event2.end_time and event2.start_time < event1.end_time)
    
    def _get_conflict_type(self, event1: CalendarEvent, event2: CalendarEvent) -> str:
        """Determine the type of conflict between two events"""
        if event1.start_time == event2.start_time and event1.end_time == event2.end_time:
            return "same_time"
        elif event1.end_time == event2.start_time or event2.end_time == event1.start_time:
            return "adjacent"
        else:
            return "overlap"
    
    def _get_overlap_duration(self, event1: CalendarEvent, event2: CalendarEvent) -> int:
        """Calculate overlap duration in minutes"""
        overlap_start = max(event1.start_time, event2.start_time)
        overlap_end = min(event1.end_time, event2.end_time)
        
        if overlap_start >= overlap_end:
            return 0
        
        return int((overlap_end - overlap_start).total_seconds() / 60)
    
    async def find_available_slots(self, calendar_ids: List[str], start_time: datetime, 
                                 end_time: datetime, duration_minutes: int = 60) -> List[AvailabilitySlot]:
        """Find available time slots within specified time range"""
        freebusy_query = FreeBusyQuery(
            calendar_ids=calendar_ids,
            start_time=start_time,
            end_time=end_time
        )
        
        freebusy_data = await self.get_free_busy(freebusy_query)
        
        all_busy_periods = []
        for response in freebusy_data:
            all_busy_periods.extend(response.busy_periods)
        
        all_busy_periods.sort(key=lambda x: x['start'])
        
        available_slots = []
        current_time = start_time
        
        for busy_period in all_busy_periods:
            busy_start = busy_period['start']
            
            if current_time + timedelta(minutes=duration_minutes) <= busy_start:
                available_slots.append(AvailabilitySlot(
                    start_time=current_time,
                    end_time=busy_start,
                    duration_minutes=int((busy_start - current_time).total_seconds() / 60),
                    calendar_ids=calendar_ids
                ))
            
            current_time = max(current_time, busy_period['end'])
        
        if current_time + timedelta(minutes=duration_minutes) <= end_time:
            available_slots.append(AvailabilitySlot(
                start_time=current_time,
                end_time=end_time,
                duration_minutes=int((end_time - current_time).total_seconds() / 60),
                calendar_ids=calendar_ids
            ))
        
        return [slot for slot in available_slots if slot.duration_minutes >= duration_minutes]