from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Literal
from datetime import datetime

Platform = Literal["email"]
NotifType = Literal["message"]
Priority = Literal["low","medium","high","urgent"]

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
