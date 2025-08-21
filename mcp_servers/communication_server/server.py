# mcp-servers/communication-server/server.py
import asyncio
import json
import logging
from typing import Dict, List, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions

from .models import Notification, ListNotificationsArgs, SlackListNotificationsArgs
from .integrations.gmail import GmailIntegration
from .integrations.slack import SlackIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
print("🚀 Starting MCP Communication Server...")
server = Server("communication-server")
print("✅ MCP Server instance created")

# Initialize integrations
print("🔧 Initializing Gmail integration...")
gmail_integration = GmailIntegration()
print("✅ Gmail integration initialized")

print("🔧 Initializing Slack integration...")
try:
    slack_integration = SlackIntegration()
    print("✅ Slack integration initialized (user token)")
except Exception as e:
    print(f"⚠️ Slack integration failed to initialize: {e}")
    print("💡 Add SLACK_USER_TOKEN to .env file to enable Slack integration")
    slack_integration = None

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for communication platforms"""
    print("📋 Client requested tool list")
    return [
        Tool(
            name="list_gmail_notifications",
            description="List recent Gmail notifications from INBOX with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "since": {
                        "type": "string",
                        "description": "ISO-8601 timestamp to filter notifications since this date"
                    },
                    "query": {
                        "type": "string", 
                        "description": "Gmail search query (e.g., 'from:example@company.com')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of notifications to return",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="analyze_sender_importance",
            description="Analyze the importance of an email sender based on communication history",
            inputSchema={
                "type": "object",
                "properties": {
                    "sender_email": {
                        "type": "string",
                        "description": "Email address of the sender to analyze"
                    },
                    "days_back": {
                        "type": "integer", 
                        "description": "Number of days to look back for analysis",
                        "default": 30
                    }
                },
                "required": ["sender_email"]
            }
        ),
        Tool(
            name="get_recent_conversations",
            description="Get recent conversation history with a specific contact",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_email": {
                        "type": "string",
                        "description": "Email address of the contact"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 7
                    },
                    "max_messages": {
                        "type": "integer",
                        "description": "Maximum number of messages to return",
                        "default": 10
                    }
                },
                "required": ["contact_email"]
            }
        ),
        Tool(
            name="check_sender_domain",
            description="Check if sender is from company domain or external",
            inputSchema={
                "type": "object",
                "properties": {
                    "sender_email": {
                        "type": "string",
                        "description": "Email address to check domain for"
                    }
                },
                "required": ["sender_email"]
            }
        ),
        # Slack tools
        Tool(
            name="list_slack_notifications",
            description="List recent Slack messages/notifications with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "since_timestamp": {
                        "type": "string",
                        "description": "ISO-8601 timestamp to filter messages since this date"
                    },
                    "channel_filter": {
                        "type": "string",
                        "description": "Filter messages by channel name (partial match)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of messages to return",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="analyze_slack_user_importance",
            description="Analyze the importance of a Slack user based on communication history and role",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Slack user ID to analyze"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back for analysis",
                        "default": 30
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_slack_conversations",
            description="Get recent conversation history with a specific Slack user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Slack user ID to get conversations with"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 7
                    },
                    "max_messages": {
                        "type": "integer",
                        "description": "Maximum number of messages to return",
                        "default": 10
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="check_slack_user_workspace",
            description="Check Slack user workspace information and permissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Slack user ID to check"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_slack_channel_info",
            description="Get detailed information about a Slack channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Slack channel ID to get information for"
                    }
                },
                "required": ["channel_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""
    print(f"🔧 Client called tool: {name} with args: {arguments}")
    try:
        if name == "list_gmail_notifications":
            # Validate arguments
            args = ListNotificationsArgs(**arguments)
            max_results = arguments.get("max_results", 20)
            
            # Get notifications from Gmail
            notifications_data = await gmail_integration.list_notifications(
                since_iso=args.since,
                query=args.query,
                max_results=max_results
            )
            
            # Convert to Notification models
            notifications = []
            for data in notifications_data:
                notification = Notification(**data)
                notifications.append(notification.model_dump())
            
            logger.info(f"Retrieved {len(notifications)} Gmail notifications")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(notifications),
                    "notifications": notifications
                }, ensure_ascii=False)
            )]
            
        elif name == "analyze_sender_importance":
            sender_email = arguments["sender_email"]
            days_back = arguments.get("days_back", 30)
            
            importance_data = await gmail_integration.analyze_sender_importance(
                sender_email, days_back
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(importance_data, ensure_ascii=False)
            )]
            
        elif name == "get_recent_conversations":
            contact_email = arguments["contact_email"]
            days_back = arguments.get("days_back", 7)
            max_messages = arguments.get("max_messages", 10)
            
            conversations = await gmail_integration.get_recent_conversations(
                contact_email, days_back, max_messages
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "contact": contact_email,
                    "conversations": conversations
                }, ensure_ascii=False)
            )]
            
        elif name == "check_sender_domain":
            sender_email = arguments["sender_email"]
            domain_info = await gmail_integration.check_sender_domain(sender_email)
            
            return [TextContent(
                type="text",
                text=json.dumps(domain_info, ensure_ascii=False)
            )]
            
        # Slack tools
        elif name == "list_slack_notifications":
            if not slack_integration:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Slack integration not available"})
                )]
            
            args = SlackListNotificationsArgs(**arguments)
            
            notifications_data = await slack_integration.list_notifications(
                since_timestamp=args.since_timestamp,
                channel_filter=args.channel_filter,
                max_results=args.max_results
            )
            
            # Convert to Notification models
            notifications = []
            for data in notifications_data:
                notification = Notification(**data)
                notifications.append(notification.model_dump())
            
            logger.info(f"Retrieved {len(notifications)} Slack notifications")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(notifications),
                    "notifications": notifications
                }, ensure_ascii=False)
            )]
            
        elif name == "analyze_slack_user_importance":
            if not slack_integration:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Slack integration not available"})
                )]
            
            user_id = arguments["user_id"]
            days_back = arguments.get("days_back", 30)
            
            importance_data = await slack_integration.analyze_sender_importance(
                user_id, days_back
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(importance_data, ensure_ascii=False)
            )]
            
        elif name == "get_slack_conversations":
            if not slack_integration:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Slack integration not available"})
                )]
            
            user_id = arguments["user_id"]
            days_back = arguments.get("days_back", 7)
            max_messages = arguments.get("max_messages", 10)
            
            conversations = await slack_integration.get_recent_conversations(
                user_id, days_back, max_messages
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "user_id": user_id,
                    "conversations": conversations
                }, ensure_ascii=False)
            )]
            
        elif name == "check_slack_user_workspace":
            if not slack_integration:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Slack integration not available"})
                )]
            
            user_id = arguments["user_id"]
            user_info = await slack_integration.check_user_workspace(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(user_info, ensure_ascii=False)
            )]
            
        elif name == "get_slack_channel_info":
            if not slack_integration:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Slack integration not available"})
                )]
            
            channel_id = arguments["channel_id"]
            channel_info = await slack_integration.get_channel_info(channel_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(channel_info, ensure_ascii=False)
            )]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            })
        )]

async def run():
    """Run the server with lifespan management."""
    print("🌐 Starting stdio server...")
    
    async with stdio_server() as (read_stream, write_stream):
        print("📡 MCP Server running and listening for client connections...")
        print("💡 Server is ready to process requests!")
        print("⏳ Waiting for MCP client to connect...")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="communication-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(run())