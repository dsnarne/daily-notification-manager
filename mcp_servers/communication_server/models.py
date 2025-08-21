from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Literal, List
from datetime import datetime

Platform = Literal["email", "slack"]
NotifType = Literal["message", "dm", "mention", "reaction"]
Priority = Literal["low","medium","high","urgent"]
ImportanceLevel = Literal["low","medium","high","critical"]
DomainType = Literal["internal","external","trusted","unknown"]
UserType = Literal["member", "admin", "owner", "primary_owner", "guest", "bot", "unknown"]

class Notification(BaseModel):
    id: str
    external_id: str
    thread_id: Optional[str] = None
    platform: Platform
    notification_type: NotifType = "message"
    title: Optional[str] = None
    content: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    priority: Optional[Priority] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    link: Optional[HttpUrl] = None

class ListNotificationsArgs(BaseModel):
    since: Optional[str] = None
    query: Optional[str] = None

class SenderImportance(BaseModel):
    sender: str
    importance_score: float = Field(ge=0.0, le=10.0, description="Importance score from 0-10")
    email_frequency: int = Field(ge=0, description="Number of emails in analyzed period")
    response_rate: float = Field(ge=0.0, le=1.0, description="Response rate percentage")
    avg_response_time_hours: Optional[float] = Field(ge=0.0, description="Average response time in hours")
    is_internal: bool = Field(description="Whether sender is from internal domain")
    recent_interactions: int = Field(ge=0, description="Number of recent interactions")
    classification: ImportanceLevel = Field(description="Overall importance classification")

class ConversationMessage(BaseModel):
    message_id: str
    subject: Optional[str] = None
    sender: str
    recipient: str
    date: datetime
    snippet: Optional[str] = None
    thread_id: Optional[str] = None

class DomainInfo(BaseModel):
    email: str
    domain: str
    domain_type: DomainType
    is_internal: bool
    is_trusted: bool

class SlackListNotificationsArgs(BaseModel):
    since_timestamp: Optional[str] = None
    channel_filter: Optional[str] = None
    max_results: int = Field(default=20, ge=1, le=100)

class SlackUserInfo(BaseModel):
    user_id: str
    user_name: str
    user_type: UserType
    is_internal: bool
    is_admin: bool
    is_bot: bool
    workspace_name: str
    workspace_domain: str
    timezone: Optional[str] = None
    profile_email: Optional[str] = None
    title: Optional[str] = None

class SlackChannelInfo(BaseModel):
    channel_id: str
    name: str
    topic: Optional[str] = None
    purpose: Optional[str] = None
    is_private: bool
    is_archived: bool
    member_count: int
    created: datetime
    creator: Optional[str] = None
