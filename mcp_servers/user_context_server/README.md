# User Context Server - Google Calendar MCP Integration

A Model Context Protocol (MCP) server for Google Calendar integration, designed to provide comprehensive calendar management and user context awareness.

## Features

### Core Calendar Operations
- List all accessible calendars
- Create, read, update, and delete calendar events  
- Search and filter events across multiple calendars
- Support for recurring events and all-day events

### Advanced Scheduling
- Free/busy time checking across multiple calendars
- Conflict detection and resolution
- Available time slot finding
- Smart scheduling assistance

### Context & Analytics
- Today's schedule overview
- Upcoming events analysis
- Calendar pattern analysis and insights
- Meeting frequency and duration statistics

### Extensible Design
- Built with room for expansion to other calendar providers (Outlook, Apple Calendar)
- Modular integration architecture
- Comprehensive data models for calendar entities

## Setup

### 1. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file

### 2. Environment Variables

Add these to your `.env` file:

```bash
# Google Calendar Integration
GOOGLE_CALENDAR_CLIENT_ID=your_client_id_here
GOOGLE_CALENDAR_CLIENT_SECRET=your_client_secret_here
GOOGLE_CALENDAR_REFRESH_TOKEN=your_refresh_token_here
```

### 3. Getting Refresh Token

Run the OAuth flow to get a refresh token:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']

flow = InstalledAppFlow.from_client_secrets_file(
    'path/to/credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

print(f"Refresh token: {creds.refresh_token}")
```

## Available Tools

### Calendar Management
- `list_calendars` - List all accessible calendars
- `list_calendar_events` - List events with filtering options
- `create_calendar_event` - Create new events
- `update_calendar_event` - Update existing events  
- `delete_calendar_event` - Delete events

### Scheduling & Availability
- `get_calendar_free_busy` - Check free/busy status
- `find_scheduling_conflicts` - Detect scheduling conflicts
- `find_available_time_slots` - Find open time slots
- `get_today_schedule` - Get today's agenda
- `get_upcoming_events` - Get upcoming events

### Analytics & Insights
- `analyze_calendar_patterns` - Analyze meeting patterns and habits

## Usage Examples

### List Today's Events
```json
{
  "tool": "get_today_schedule",
  "arguments": {
    "include_all_day": true
  }
}
```

### Create a Meeting
```json
{
  "tool": "create_calendar_event",
  "arguments": {
    "calendar_id": "primary",
    "title": "Team Standup",
    "start_time": "2024-01-15T09:00:00",
    "end_time": "2024-01-15T09:30:00",
    "attendees": ["team@company.com"],
    "location": "Conference Room A"
  }
}
```

### Find Available Time
```json
{
  "tool": "find_available_time_slots",
  "arguments": {
    "calendar_ids": ["primary"],
    "start_time": "2024-01-15T09:00:00",
    "end_time": "2024-01-15T17:00:00",
    "duration_minutes": 60
  }
}
```

## Integration with Main Application

The user context server integrates with the daily notification manager to:

1. **Enhance Notification Context** - Understand user availability when processing notifications
2. **Smart Scheduling** - Suggest optimal meeting times based on calendar availability
3. **Priority Insights** - Factor in calendar events when determining notification urgency
4. **Context-Aware Responses** - Provide intelligent responses based on current schedule

## Future Expansion

The server is designed to support additional calendar providers:

- **Microsoft Outlook Calendar** - Office 365 and Outlook.com integration
- **Apple Calendar** - iCloud calendar integration  
- **CalDAV/CardDAV** - Support for any standards-compliant calendar service
- **Custom Calendar Systems** - Enterprise calendar solutions

## Error Handling

The server includes comprehensive error handling for:
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid calendar data
- Permission errors

## Security

- OAuth 2.0 for secure authentication
- Refresh token management
- Minimal scope requirements
- No storage of sensitive credentials
- Secure token refresh mechanisms