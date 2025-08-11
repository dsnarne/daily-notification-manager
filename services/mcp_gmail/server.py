import asyncio
import json
from mcp.server.stdio import stdio_server
from .schemas import Notification

async def list_gmail_notifications() -> list[Notification]:
    # Temporary stub for testing — replace with Gmail API calls
    return [
        Notification(
            id=1,
            title="Test Email",
            content="This is a test email",
            sender="test@example.com",
            recipient="you@example.com",
            platform="email",
            notification_type="message",
            priority="medium",
            status="unread",
            integration_id=123,
            created_at="2025-08-11T00:00:00Z"
        )
    ]

async def main():
    async with stdio_server() as (read, write):
        async for message in read:
            # You could parse message and respond according to MCP spec
            # For now, just log incoming and send back notifications
            print(f"Received from client: {message}", flush=True)
            notifications = await list_gmail_notifications()
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": [n.model_dump() for n in notifications]
            }
            write(json.dumps(response))

if __name__ == "__main__":
    asyncio.run(main())
