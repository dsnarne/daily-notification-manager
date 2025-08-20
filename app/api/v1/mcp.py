"""
MCP-backed endpoints to surface Gmail and Slack data in the frontend
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import asyncio
import json
from fastapi.responses import StreamingResponse

from ...core.mcp_client import MCPCommunicationClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/gmail/notifications")
async def gmail_notifications(query: str = "", max_results: int = 20):
    try:
        data = await MCPCommunicationClient.call_tool(
            "list_notifications", {"query": query, "max_results": max_results}
        )
        return data
    except Exception as e:
        logger.error(f"gmail_notifications failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/channels")
async def slack_channels():
    try:
        data = await MCPCommunicationClient.call_tool("slack_list_channels", {})
        return data
    except Exception as e:
        logger.error(f"slack_channels failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/channels/{channel_id}/messages")
async def slack_channel_messages(channel_id: str, limit: int = 50):
    try:
        data = await MCPCommunicationClient.call_tool(
            "slack_list_channel_messages", {"channel_id": channel_id, "limit": limit}
        )
        return data
    except Exception as e:
        logger.error(f"slack_channel_messages failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def mcp_stream(poll_seconds: int = 20):
    """Server-Sent Events stream that periodically polls MCP tools and emits new notifications.
    This provides near real-time updates to the UI without tight coupling to MCP notification transport.
    """
    async def event_generator():
        seen_ids = set()
        while True:
            try:
                # Gmail
                gmail_items = await MCPCommunicationClient.call_tool(
                    "list_notifications", {"query": "is:unread", "max_results": 20}
                )
                if isinstance(gmail_items, list):
                    for item in gmail_items:
                        nid = item.get("id")
                        if nid and nid not in seen_ids:
                            seen_ids.add(nid)
                            payload = {
                                "source": "gmail",
                                "notification": item,
                            }
                            yield f"data: {json.dumps(payload)}\n\n"

                # Slack (best-effort: first channel)
                channels = await MCPCommunicationClient.call_tool("slack_list_channels", {})
                channel_id = None
                if isinstance(channels, list) and channels:
                    channel_id = channels[0].get("id") or channels[0].get("channel", {}).get("id")
                if channel_id:
                    slack_items = await MCPCommunicationClient.call_tool(
                        "slack_list_channel_messages", {"channel_id": channel_id, "limit": 20}
                    )
                    if isinstance(slack_items, list):
                        for item in slack_items:
                            nid = item.get("id")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                payload = {
                                    "source": "slack",
                                    "notification": item,
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
            except Exception as e:
                logger.error(f"mcp_stream polling error: {e}")
                # send error event to client
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(max(5, poll_seconds))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

