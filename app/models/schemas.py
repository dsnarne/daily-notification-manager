"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class PlatformType(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class NotificationType(str, Enum):
    MESSAGE = "message"
    MENTION = "mention"
    ALERT = "alert"
    TASK = "task"
    REMINDER = "reminder"

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# Integration schemas
class IntegrationBase(BaseSchema):
    platform: PlatformType
    name: str = Field(..., min_length=1, max_length=100)
    config: Dict[str, Any]

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Integration(IntegrationBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# Email-specific schemas
class EmailConfig(BaseSchema):
    server: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    provider: Optional[str] = None  # gmail, outlook, exchange

class GmailConfig(BaseSchema):
    client_id: str
    client_secret: str
    refresh_token: str

class OutlookConfig(BaseSchema):
    client_id: str
    client_secret: str
    tenant_id: str

# Slack-specific schemas
class SlackConfig(BaseSchema):
    bot_token: str
    app_token: Optional[str] = None
    signing_secret: Optional[str] = None
    webhook_url: Optional[str] = None

# Teams-specific schemas
class TeamsConfig(BaseSchema):
    client_id: str
    client_secret: str
    tenant_id: str
    authority: str = "https://login.microsoftonline.com"

# Webhook-specific schemas
class WebhookConfig(BaseSchema):
    url: str
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

# Notification schemas
class NotificationBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    platform: PlatformType
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    integration_id: int
    external_id: Optional[str] = None

class NotificationUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None

class Notification(NotificationBase):
    id: int
    integration_id: int
    external_id: Optional[str] = None
    status: NotificationStatus
    created_at: datetime
    read_at: Optional[datetime] = None

# Notification preference schemas
class PriorityLevel(BaseSchema):
    message: NotificationPriority = NotificationPriority.MEDIUM
    mention: NotificationPriority = NotificationPriority.HIGH
    alert: NotificationPriority = NotificationPriority.HIGH
    task: NotificationPriority = NotificationPriority.MEDIUM
    reminder: NotificationPriority = NotificationPriority.LOW

class QuietHours(BaseSchema):
    enabled: bool = False
    start_time: str = "22:00"  # HH:MM format
    end_time: str = "08:00"    # HH:MM format
    timezone: str = "UTC"

class NotificationFilter(BaseSchema):
    keywords: Optional[List[str]] = None
    senders: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    min_priority: Optional[NotificationPriority] = None

class NotificationPreferenceBase(BaseSchema):
    platform: PlatformType
    priority_levels: PriorityLevel
    quiet_hours: Optional[QuietHours] = None
    filters: Optional[NotificationFilter] = None

class NotificationPreferenceCreate(NotificationPreferenceBase):
    pass

class NotificationPreferenceUpdate(BaseSchema):
    priority_levels: Optional[PriorityLevel] = None
    quiet_hours: Optional[QuietHours] = None
    filters: Optional[NotificationFilter] = None

class NotificationPreference(NotificationPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Notification rule schemas
class RuleCondition(BaseSchema):
    field: str  # sender, content, priority, etc.
    operator: str  # equals, contains, greater_than, etc.
    value: Any

class RuleAction(BaseSchema):
    action_type: str  # mark_read, change_priority, forward, etc.
    parameters: Optional[Dict[str, Any]] = None

class NotificationRuleBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    priority: int = 1

class NotificationRuleCreate(NotificationRuleBase):
    pass

class NotificationRuleUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: Optional[List[RuleCondition]] = None
    actions: Optional[List[RuleAction]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class NotificationRule(NotificationRuleBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# API response schemas
class SuccessResponse(BaseSchema):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    details: Optional[str] = None

# Pagination schemas
class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int 