# services/mcp_gmail/server.py
import sys, json, traceback
from typing import Any, Dict, Optional, List

from mcp_servers.communication_server.schemas import Notification
from mcp_servers.communication_server.gmail_api import list_gmail_notifications
import os

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

TOOL_DEF = {
    "name": "list_notifications",
    "description": "List recent Gmail notifications (INBOX). Optional filters: since ISO-8601, Gmail query.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "since": {"type": "string"},
            "query": {"type": "string"}
        },
        "required": []
    }
}

def handle_list_notifications(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = list_gmail_notifications(args.get("since"), args.get("query"))
    return [Notification(**x).model_dump() for x in items]

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
            # If it's a response we didn't ask for (shouldn't happen), or a malformed notification — ignore
            continue

        if method == "initialize":
            send_result(rid, {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-gmail", "version": "0.1.0"},
            })
            continue

        if method == "tools/list":
            send_result(rid, {"tools": [TOOL_DEF]})
            continue

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            log(f"TOOLS/CALL name={name} args={arguments}")
            if name == "list_notifications":
                if name == "list_notifications":
                    try:
                        items = handle_list_notifications(arguments)
                        payload = [Notification(**x).model_dump(mode="json") for x in items]
                        log(f"TOOL RESULT COUNT: {len(payload)}")
                        send_result(rid, {
                            "content": [
                                {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
                            ]
                        })
                    except Exception as e:
                        log("TOOLS/CALL ERROR:", repr(e))
                        log(traceback.format_exc())
                        send_error(rid, -32603, "Internal error", {
                            "exception": str(e),
                            "trace": traceback.format_exc(),
                            "arguments": arguments,
                        })
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
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
