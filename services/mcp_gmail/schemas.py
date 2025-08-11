# completely decoupled from your app
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

# Keep enums as Literals to avoid drift/versioning headaches for now
Platform = Literal["email"]
NotifType = Literal["message"]
Priority = Literal["low","medium","high","urgent"]

class ListNotificationsArgs(BaseModel):
    since: datetime
    query: Optional[str] = None
    access_token: str

class FetchThreadArgs(BaseModel):
    thread_id: str
    access_token: str

class WireNotification(BaseModel):
    # portable, provider-oriented object
    id: str                     # stable dedupe key, e.g. "gmail:<messageId>"
    external_id: str            # Gmail messageId
    thread_id: Optional[str] = None
    platform: Platform = "email"
    notification_type: NotifType = "message"

    title: Optional[str] = None     # subject
    content: Optional[str] = None   # snippet/preview
    sender: Optional[str] = None
    recipient: Optional[str] = None
    priority: Optional[Priority] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

    created_at: datetime
    link: Optional[HttpUrl] = None

class WireThreadMessage(BaseModel):
    id: str
    sender: Optional[str] = None
    text: Optional[str] = None
    ts: datetime

class ThreadResponse(BaseModel):
    messages: List[WireThreadMessage]
