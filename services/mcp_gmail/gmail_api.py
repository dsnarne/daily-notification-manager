from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.utils import parsedate_to_datetime
from datetime import datetime

def _svc(access_token: str):
    creds = Credentials(token=access_token)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def list_gmail_notifications(since_dt: datetime, query: str | None, access_token: str) -> list[dict]:
    svc = _svc(access_token)
    q = query or "label:INBOX newer_than:1d"
    res = svc.users().messages().list(userId="me", q=q, maxResults=50).execute()
    items = []
    for m in res.get("messages", []):
        meta = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From","To","Subject","Date"]
        ).execute()
        headers = {h["name"].lower(): h["value"] for h in meta.get("payload", {}).get("headers", [])}
        dt = parsedate_to_datetime(headers.get("date")) if headers.get("date") else since_dt
        items.append({
            "id": f"gmail:{m['id']}",
            "external_id": m["id"],
            "thread_id": meta.get("threadId"),
            "title": headers.get("subject"),
            "content": meta.get("snippet"),
            "sender": headers.get("from"),
            "recipient": headers.get("to"),
            "priority": "medium",
            "metadata": {"labelIds": meta.get("labelIds", [])},
            "created_at": dt.isoformat(),
            "link": f"https://mail.google.com/mail/u/0/#inbox/{m['id']}",
            "platform": "email",
            "notification_type": "message",
        })
    return items
