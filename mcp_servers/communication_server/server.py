#!/usr/bin/env python3
# communication_server/server.py
import sys, json, traceback, os, threading, time
from typing import Any, Dict, Optional, List
from datetime import datetime

from mcp_servers.communication_server.models import Notification
from app.integrations.email_integration import GmailIntegration
from app.integrations.slack_integration import SlackIntegration
from app.models.schemas import GmailConfig, SlackConfig

# Enable debug logging when MCP_DEBUG=1 in env
DEBUG = os.getenv("MCP_DEBUG", "0") == "1"

def log(*a):
    if DEBUG:
        print(*a, file=sys.stderr, flush=True)

def send(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def send_result(rid: Any, result: Any) -> None:
    if rid is None:
        return  # never respond to notifications
    send({"jsonrpc": "2.0", "id": rid, "result": result})

def send_error(rid: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    if rid is None:
        return  # never respond to notifications
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    send({"jsonrpc": "2.0", "id": rid, "error": err})

def publish_notification(payload: Dict[str, Any]) -> None:
    # Fire-and-forget JSON-RPC notification (no id)
    send({
        "jsonrpc": "2.0",
        "method": "notifications/publish",
        "params": {
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
        }
    })

# -------
# Integrations (reuse existing app integrations)
# -------

def build_gmail_integration() -> Optional[GmailIntegration]:
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        log("Gmail env missing; set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN")
        return None
    cfg = GmailConfig(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    return GmailIntegration(cfg)

def build_slack_integration() -> Optional[SlackIntegration]:
    bot = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")
    signing = os.getenv("SLACK_SIGNING_SECRET")
    if not bot:
        log("Slack env missing; set SLACK_BOT_TOKEN (and optionally SLACK_APP_TOKEN, SLACK_SIGNING_SECRET)")
        return None
    cfg = SlackConfig(bot_token=bot, app_token=app_token, signing_secret=signing)
    return SlackIntegration(cfg)

def parse_email_date(date_str: str) -> str:
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return (dt if dt.tzinfo else dt.replace(tzinfo=None)).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()

# -------
# Tool definitions
# -------

GMAIL_TOOL = {
    "name": "list_notifications",
    "description": "List recent Gmail notifications using app GmailIntegration. Optional filters: query, max_results.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 200}
        },
        "required": []
    }
}

SLACK_LIST_CHANNELS_TOOL = {
    "name": "slack_list_channels",
    "description": "List Slack channels available to the bot.",
    "inputSchema": {"type": "object", "properties": {}, "required": []}
}

SLACK_LIST_MESSAGES_TOOL = {
    "name": "slack_list_channel_messages",
    "description": "List recent messages for a Slack channel.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "channel_id": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200}
        },
        "required": ["channel_id"]
    }
}

def map_email_to_notification(e: Dict[str, Any]) -> Dict[str, Any]:
    return Notification(
        id=f"gmail:{e.get('id')}",
        external_id=e.get('id'),
        thread_id=e.get('thread_id'),
        platform="email",
        notification_type="message",
        title=e.get('subject') or e.get('title'),
        content=e.get('body') or e.get('content') or "",
        sender=e.get('sender'),
        recipient=None,
        priority="medium",
        metadata={"labels": ",".join(e.get('labels') or [])},
        created_at=datetime.fromisoformat(parse_email_date(e.get('date', datetime.utcnow().isoformat())).replace('Z','+00:00')),
        link=f"https://mail.google.com/mail/u/0/#inbox/{e.get('id')}"
    ).model_dump(mode="json")

def handle_list_notifications(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    gi = build_gmail_integration()
    if gi is None:
        raise RuntimeError("Gmail integration is not configured")
    emails = gi.fetch_emails(max_results=int(args.get("max_results", 20)), query=args.get("query") or "")
    return [map_email_to_notification(e) for e in emails]

def handle_slack_list_channels(_: Dict[str, Any]) -> List[Dict[str, Any]]:
    si = build_slack_integration()
    if si is None:
        raise RuntimeError("Slack integration is not configured")
    channels = si.get_channels() or []
    # Return raw channels for flexibility
    return channels

def handle_slack_list_messages(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    si = build_slack_integration()
    if si is None:
        raise RuntimeError("Slack integration is not configured")
    channel_id = args.get("channel_id")
    limit = int(args.get("limit", 50))
    msgs = si.get_channel_messages(channel_id, limit=limit) or []

    out: List[Dict[str, Any]] = []
    for m in msgs:
        ts = m.get("ts") or m.get("event_ts") or "0"
        try:
            ts_float = float(ts)
        except Exception:
            ts_float = time.time()
        created_at_str = datetime.utcfromtimestamp(ts_float).isoformat()
        out.append(Notification(
            id=f"slack:{channel_id}:{ts}",
            external_id=str(ts),
            thread_id=m.get("thread_ts"),
            platform="slack",
            notification_type="message",
            title=(m.get("text") or "").split("\n")[0][:120] or "Slack Message",
            content=m.get("text") or "",
            sender=m.get("user") or m.get("username"),
            recipient=channel_id,
            priority="medium",
            metadata={"channel": channel_id},
            created_at=datetime.fromisoformat(created_at_str),
            link=None
        ).model_dump(mode="json"))
    return out

# Optional background polling to publish new items as notifications
def start_background_publishers():
    if os.getenv("MCP_ENABLE_REALTIME", "0") != "1":
        return

    def gmail_poll():
        gi = build_gmail_integration()
        if gi is None:
            return
        seen: set = set()
        interval = int(os.getenv("MCP_GMAIL_POLL_SECONDS", "60"))
        while True:
            try:
                emails = gi.fetch_emails(max_results=20, query=os.getenv("MCP_GMAIL_QUERY", "is:unread"))
                for e in emails:
                    key = e.get('id')
                    if key in seen:
                        continue
                    seen.add(key)
                    publish_notification({"source": "gmail", "notification": map_email_to_notification(e)})
            except Exception as exc:
                log("gmail poll error:", exc)
            time.sleep(interval)

    def slack_poll():
        si = build_slack_integration()
        if si is None:
            return
        channels_env = os.getenv("MCP_SLACK_CHANNELS", "").strip()
        if not channels_env:
            log("MCP_SLACK_CHANNELS not set; skipping slack polling")
            return
        channel_ids = [c.strip() for c in channels_env.split(",") if c.strip()]
        last_ts: Dict[str, float] = {}
        interval = int(os.getenv("MCP_SLACK_POLL_SECONDS", "30"))
        while True:
            try:
                for cid in channel_ids:
                    msgs = si.get_channel_messages(cid, limit=50) or []
                    # Newest first per Slack API typically; iterate reversed to publish oldest first
                    for m in reversed(msgs):
                        ts = float(m.get("ts", "0")) if m.get("ts") else 0.0
                        if ts <= last_ts.get(cid, 0.0):
                            continue
                        last_ts[cid] = ts
                        payloads = handle_slack_list_messages({"channel_id": cid, "limit": 1})
                        if payloads:
                            publish_notification({"source": "slack", "notification": payloads[-1]})
            except Exception as exc:
                log("slack poll error:", exc)
            time.sleep(interval)

    threading.Thread(target=gmail_poll, daemon=True).start()
    threading.Thread(target=slack_poll, daemon=True).start()


# Start background publishers if enabled
start_background_publishers()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = None
    try:
        req = json.loads(line)
        log("RAW REQUEST:", line)
        log("PARSED REQUEST:", req)

        # Basic JSON-RPC sanity
        if req.get("jsonrpc") != "2.0":
            # ignore garbage / non-JSON-RPC lines
            continue

        rid = req.get("id")  # may be None (notification)
        method = req.get("method")
        params = req.get("params") or {}

        # Some MCP clients may send notifications; ignore them silently
        if method is None:
            continue

        if method == "initialize":
            send_result(rid, {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-communication", "version": "0.2.0"},
            })
            continue

        if method == "tools/list":
            send_result(rid, {"tools": [GMAIL_TOOL, SLACK_LIST_CHANNELS_TOOL, SLACK_LIST_MESSAGES_TOOL]})
            continue

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            log(f"TOOLS/CALL name={name} args={arguments}")
            try:
                if name == "list_notifications":
                    items = handle_list_notifications(arguments)
                    send_result(rid, {
                        "content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]
                    })
                elif name == "slack_list_channels":
                    channels = handle_slack_list_channels(arguments)
                    send_result(rid, {"content": [{"type": "text", "text": json.dumps(channels, ensure_ascii=False)}]})
                elif name == "slack_list_channel_messages":
                    msgs = handle_slack_list_messages(arguments)
                    send_result(rid, {"content": [{"type": "text", "text": json.dumps(msgs, ensure_ascii=False)}]})
                else:
                    send_error(rid, -32601, f"Unknown tool: {name}")
            except Exception as e:
                log("TOOLS/CALL ERROR:", repr(e))
                log(traceback.format_exc())
                send_error(rid, -32603, "Internal error", {
                    "exception": str(e),
                    "trace": traceback.format_exc(),
                    "arguments": arguments,
                })
            continue

        # optional niceties some clients use
        if method in ("ping", "notifications/subscribe"):
            send_result(rid, {})  # ack
            continue

        # Unknown method
        send_error(rid, -32601, f"Unknown method: {method}")

    except Exception as e:
        # Only respond if there was an id; otherwise, swallow
        send_error((req or {}).get("id"), -32603, "Internal error", {
            "exception": str(e),
            "trace": traceback.format_exc(),
        })
