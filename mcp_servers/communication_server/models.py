from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Literal, List
from datetime import datetime

Platform = Literal["email"]
NotifType = Literal["message"]
Priority = Literal["low","medium","high","urgent"]
ImportanceLevel = Literal["low","medium","high","critical"]
DomainType = Literal["internal","external","trusted","unknown"]

class Notification(BaseModel):
    id: str
    external_id: str
    thread_id: Optional[str] = None
    platform: Platform = "email"
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
