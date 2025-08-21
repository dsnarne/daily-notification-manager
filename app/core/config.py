"""
Configuration settings for DaiLY Notification Manager
"""

import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    """Application settings"""
    # Application
    app_name: str = "DaiLY Notification Manager"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./daily.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # Gmail MCP Server settings
    gmail_server_path: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    
    # Google Calendar settings
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    google_calendar_refresh_token: str = ""
    
    # Slack settings
    slack_user_token: str = ""
    
    # Anthropic API
    anthropic_api_key: str = ""
    
    # Scheduler settings
    notification_check_interval: int = 60  # seconds
    
    # Email providers configuration
    email_providers: Dict[str, Dict[str, Any]] = {
        "gmail": {
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"],
            "redirect_uri": "http://localhost:8000/auth/gmail/callback"
        },
        "outlook": {
            "scopes": ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/Mail.Send"],
            "redirect_uri": "http://localhost:8000/auth/outlook/callback"
        }
    }
    
    # Slack configuration
    slack_event_types: List[str] = [
        "message", "mention", "reaction_added", "channel_created", "team_join"
    ]
    
    # Teams configuration  
    teams_event_types: List[str] = [
        "message", "mention", "reaction", "channelCreated", "teamMemberAdded"
    ]
    
    # Webhook configuration
    webhook: Dict[str, Any] = {
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 5
    }
    
    # Notification settings
    default_priority: str = "medium"
    max_notifications_per_sync: int = 100
    sync_interval_minutes: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Export commonly used constants
EMAIL_PROVIDERS = settings.email_providers
SLACK_EVENT_TYPES = settings.slack_event_types
TEAMS_EVENT_TYPES = settings.teams_event_types
WEBHOOK_TIMEOUT = settings.webhook["timeout"]
WEBHOOK_MAX_RETRIES = settings.webhook["max_retries"]
WEBHOOK_RETRY_DELAY = settings.webhook["retry_delay"] 