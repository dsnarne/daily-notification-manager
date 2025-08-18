# services/mcp_gmail/gmail_api.py
import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def _mint_access_token() -> str:
    refresh = os.getenv("GMAIL_REFRESH_TOKEN")
    cid = os.getenv("GMAIL_CLIENT_ID")
    csec = os.getenv("GMAIL_CLIENT_SECRET")
    if not all([refresh, cid, csec]):
        raise RuntimeError("Missing env: GMAIL_REFRESH_TOKEN / GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET")
    creds = Credentials(
        None, refresh_token=refresh, token_uri="https://oauth2.googleapis.com/token",
        client_id=cid, client_secret=csec, scopes=SCOPES
    )
    creds.refresh(Request())
    return creds.token

def _svc(access_token: str):
    creds = Credentials(token=access_token)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def list_gmail_notifications(since_iso: Optional[str] = None,
                             query: Optional[str] = None) -> List[Dict]:
    access = _mint_access_token()
    svc = _svc(access)

    q = query or "label:INBOX newer_than:1d"
    if since_iso:
        # Best-effort absolute date filter: Gmail supports after:YYYY/MM/DD
        try:
            dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
            q = f"{q} after:{dt.strftime('%Y/%m/%d')}"
        except Exception:
            pass

    res = svc.users().messages().list(userId="me", q=q, maxResults=20).execute()
    msgs = res.get("messages", [])
    out: List[Dict] = []

    for m in msgs:
        meta = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From","To","Subject","Date"]
        ).execute()
        headers = {h["name"].lower(): h["value"] for h in meta.get("payload", {}).get("headers", [])}
        dt = parsedate_to_datetime(headers.get("date")) if headers.get("date") else datetime.utcnow()
        out.append({
            "id": f"gmail:{m['id']}",
            "external_id": m["id"],
            "thread_id": meta.get("threadId"),
            "title": headers.get("subject"),
            "content": meta.get("snippet"),
            "sender": headers.get("from"),
            "recipient": headers.get("to"),
            "priority": "medium",
            "metadata": {"labelIds": ",".join(meta.get("labelIds", []) or [])},
            "created_at": dt.isoformat(),
            "link": f"https://mail.google.com/mail/u/0/#inbox/{m['id']}",
            "platform": "email",
            "notification_type": "message",
        })
    return out
