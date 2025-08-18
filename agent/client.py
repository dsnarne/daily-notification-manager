# agent/notification_agent.py
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NotificationDecision:
    notification_id: str
    decision: str  # IMMEDIATE, BATCH, DIGEST, FILTER
    urgency_score: int
    importance_score: int
    reasoning: str
    context_used: List[str]
    suggested_action: str
    batch_group: Optional[str] = None

@dataclass
class BatchGroup:
    name: str
    notifications: List[str]
    summary: str
    suggested_timing: str

@dataclass
class ProcessingResult:
    analysis_summary: str
    decisions: List[NotificationDecision]
    batch_groups: Dict[str, BatchGroup]
    overall_recommendations: List[str]
    processing_time: float

class NotificationAgent:
    def __init__(self):
        self.anthropic = Anthropic()  # Uses ANTHROPIC_API_KEY from environment
        self.mcp_sessions: Dict[str, ClientSession] = {}
        
        # Simple system prompt for MVP
        self.system_prompt = """
You are an intelligent notification management agent for busy professionals. Your job is to analyze incoming notifications and decide which ones deserve immediate attention, which should be batched together, and which can be filtered out entirely.

## YOUR MISSION
Help users stay focused by intelligently filtering and prioritizing their communication. Reduce notification overwhelm while ensuring nothing truly important is missed.

## DECISION CATEGORIES
You must categorize each notification into exactly one of these categories:

**IMMEDIATE** - Requires attention within 5 minutes
- True emergencies or time-critical issues
- Communications from top-tier contacts (CEO, direct manager on urgent matters)
- Meeting starting in <15 minutes that user must attend
- System outages affecting current work
- Deadline reminders for tasks due today

**BATCH** - Important but can wait 15-30 minutes, group with similar items
- Communications from important colleagues about active projects
- Meeting invitations for upcoming days
- Client communications that aren't urgent
- Project updates from team members
- Time-sensitive but not emergency items

**DIGEST** - Include in hourly/daily summary
- Company announcements and updates
- Newsletter content
- Meeting notes and recordings
- Non-urgent project status updates
- Social platform notifications

**FILTER** - Hide entirely, too low value
- Marketing emails and promotional content
- Automated system reports that aren't actionable
- Spam and clearly irrelevant content

## DECISION PROCESS
For each notification:

1. **Use available tools** to gather context about the user's current situation, sender importance, and project relevance
2. **Assess urgency**: Is this about something happening today? Does it require immediate action?
3. **Evaluate importance**: Who is the sender? How relevant is this to current work?
4. **Make decision**: Apply the category definitions consistently

## RESPONSE FORMAT
You must respond with a structured JSON object:

```json
{
    "analysis_summary": "Brief overview of the notification batch and your approach",
    "decisions": [
        {
            "notification_id": "unique_id_from_notification",
            "decision": "IMMEDIATE|BATCH|DIGEST|FILTER",
            "urgency_score": 1-10,
            "importance_score": 1-10,
            "reasoning": "Clear explanation of why you made this decision",
            "context_used": ["tool_calls_made", "context_factors"],
            "suggested_action": "What the user should do with this notification",
            "batch_group": "group_name (if BATCH decision)"
        }
    ],
    "batch_groups": {
        "group_name": {
            "notifications": ["id1", "id2"],
            "summary": "Summary of this group",
            "suggested_timing": "when to deliver this batch"
        }
    },
    "overall_recommendations": [
        "Any patterns noticed",
        "Suggestions for optimization"
    ]
}
```

## TOOL USAGE GUIDELINES
Always gather context before making decisions:

1. **Start with situational awareness**: Check if user is in a meeting or has upcoming events
2. **Analyze sender importance**: Look up the sender's relationship and communication history
3. **Check project relevance**: See if the content relates to active work
4. **Consider team context**: Understand organizational relationships

Use tools efficiently - not every notification needs every tool call. For obviously low-priority items (newsletters, automated reports), make quick decisions.

## EXAMPLES

**IMMEDIATE Example**:
- "URGENT: Client demo environment is down, presentation in 1 hour"
- Decision: IMMEDIATE (urgency: 9, importance: 9)
- Reasoning: System outage affecting imminent client presentation

**BATCH Example**:
- "Sarah from design: Updated mockups for Q4 project ready for review"  
- Decision: BATCH, group: "project_updates"
- Reasoning: Important project update but not time-critical

**DIGEST Example**:
- "Weekly engineering newsletter - New features and updates"
- Decision: DIGEST
- Reasoning: Informational content, no urgency

**FILTER Example**:
- "LinkedIn: John Doe posted an update"
- Decision: FILTER
- Reasoning: Social media content not relevant to work priorities

Remember: When uncertain, err on the side of showing rather than hiding, but use BATCH or DIGEST rather than IMMEDIATE for uncertain cases.
        """
        
    async def initialize_mcp_servers(self):
        """Initialize MCP server connections"""
        try:
            servers = {
                "calendar": StdioServerParameters(
                    command="python",
                    args=["mcp-servers/calendar-server/server.py"]
                ),
                "communication": StdioServerParameters(
                    command="python",
                    args=["mcp-servers/communication-server/server.py"]
                ),
                "projects": StdioServerParameters(
                    command="python",
                    args=["mcp-servers/project-server/server.py"]
                ),
                "user_context": StdioServerParameters(
                    command="python",
                    args=["mcp-servers/user-context-server/server.py"]
                )
            }
            
            # Initialize connections
            for name, params in servers.items():
                try:
                    session = await stdio_client(params)
                    self.mcp_sessions[name] = session
                    logger.info(f"Initialized MCP server: {name}")
                except Exception as e:
                    logger.error(f"Failed to initialize {name} server: {e}")
                    # Continue without this server
                    
        except Exception as e:
            logger.error(f"Error initializing MCP servers: {e}")
            raise
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from MCP servers"""
        all_tools = []
        
        for server_name, session in self.mcp_sessions.items():
            try:
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    # Add server name to tool for routing
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "_server": server_name  # Internal routing info
                    }
                    all_tools.append(tool_dict)
            except Exception as e:
                logger.error(f"Error getting tools from {server_name}: {e}")
                
        return all_tools
    
    async def get_claude_tools_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Claude's tool format"""
        mcp_tools = await self.get_available_tools()
        claude_tools = []
        
        for tool in mcp_tools:
            claude_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            })
            
        return claude_tools
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific MCP tool and return results"""
        
        # Find which server has this tool
        tools = await self.get_available_tools()
        server_name = None
        
        for tool in tools:
            if tool["name"] == tool_name:
                server_name = tool["_server"]
                break
        
        if not server_name or server_name not in self.mcp_sessions:
            raise ValueError(f"Tool {tool_name} not found or server not available")
        
        try:
            session = self.mcp_sessions[server_name]
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return json.dumps({"error": str(e)})
    
    def format_notifications(self, notifications: List[Dict[str, Any]]) -> str:
        """Format notifications for Claude processing"""
        formatted = []
        
        for i, notification in enumerate(notifications, 1):
            formatted.append(f"""
Notification #{i}:
ID: {notification.get('id', f'notification_{i}')}
Platform: {notification.get('platform', 'unknown')}
From: {notification.get('sender', 'unknown')}
Subject/Title: {notification.get('subject', notification.get('title', 'No subject'))}
Content Preview: {notification.get('content', '')[:300]}{'...' if len(notification.get('content', '')) > 300 else ''}
Timestamp: {notification.get('timestamp', datetime.now().isoformat())}
Type: {notification.get('type', 'message')}
---
            """.strip())
        
        return "\n\n".join(formatted)
    
    async def process_notifications(self, notifications: List[Dict[str, Any]]) -> ProcessingResult:
        """Main processing function - analyze notifications and make decisions"""
        start_time = datetime.now()
        
        try:
            # Initialize MCP servers
            await self.initialize_mcp_servers()
            
            # Format notifications
            notifications_text = self.format_notifications(notifications)
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": f"""
Please analyze these {len(notifications)} notifications and make priority decisions.

{notifications_text}

Use available tools to gather context as needed, then provide your structured decision response following the exact JSON format specified in your instructions.
                    """
                }
            ]
            
            # Make initial request with tools
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=self.system_prompt,
                messages=messages,
                tools=await self.get_claude_tools_format(),
                tool_choice="auto"
            )
            
            # Handle tool calls and get final decisions
            final_response = await self.handle_tool_calls_conversation(response, messages)
            
            # Parse the final response
            result = self.parse_response(final_response)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"Processed {len(notifications)} notifications in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")
            raise
        finally:
            # Clean up MCP sessions
            await self.cleanup_mcp_sessions()
    
    async def handle_tool_calls_conversation(self, response, messages: List[Dict[str, Any]]) -> str:
        """Handle the conversation flow with tool calls"""
        
        # Check if response has tool calls
        if hasattr(response, 'content') and response.content:
            content_block = response.content[0]
            
            # If it's a tool use, handle the tool calls
            if hasattr(content_block, 'type') and content_block.type == "tool_use":
                # Add assistant message with tool call
                messages.append({
                    "role": "assistant", 
                    "content": [content_block]
                })
                
                # Execute tool calls
                tool_results = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == "tool_use":
                        try:
                            # Execute the tool call
                            result = await self.call_mcp_tool(block.name, block.input)
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })
                            
                        except Exception as e:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {str(e)}"
                            })
                
                # Add tool results to conversation
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Continue conversation with tool results
                follow_up = await self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    system=self.system_prompt,
                    messages=messages,
                    tools=await self.get_claude_tools_format()
                )
                
                # Recursively handle if more tool calls needed
                if (hasattr(follow_up, 'content') and follow_up.content and
                    hasattr(follow_up.content[0], 'type') and 
                    follow_up.content[0].type == "tool_use"):
                    return await self.handle_tool_calls_conversation(follow_up, messages)
                else:
                    return follow_up.content[0].text if follow_up.content else ""
            
            # If it's just text, return it
            elif hasattr(content_block, 'text'):
                return content_block.text
        
        return ""
    
    def parse_response(self, response_text: str) -> ProcessingResult:
        """Parse Claude's response into structured result"""
        try:
            # Try to extract JSON from response
            response_data = json.loads(response_text)
            
            # Parse decisions
            decisions = []
            for decision_data in response_data.get("decisions", []):
                decision = NotificationDecision(
                    notification_id=decision_data.get("notification_id"),
                    decision=decision_data.get("decision"),
                    urgency_score=decision_data.get("urgency_score", 0),
                    importance_score=decision_data.get("importance_score", 0),
                    reasoning=decision_data.get("reasoning", ""),
                    context_used=decision_data.get("context_used", []),
                    suggested_action=decision_data.get("suggested_action", ""),
                    batch_group=decision_data.get("batch_group")
                )
                decisions.append(decision)
            
            # Parse batch groups
            batch_groups = {}
            for group_name, group_data in response_data.get("batch_groups", {}).items():
                batch_groups[group_name] = BatchGroup(
                    name=group_name,
                    notifications=group_data.get("notifications", []),
                    summary=group_data.get("summary", ""),
                    suggested_timing=group_data.get("suggested_timing", "")
                )
            
            return ProcessingResult(
                analysis_summary=response_data.get("analysis_summary", ""),
                decisions=decisions,
                batch_groups=batch_groups,
                overall_recommendations=response_data.get("overall_recommendations", []),
                processing_time=0  # Will be set by caller
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {e}")
            # Fallback: create a basic result
            return ProcessingResult(
                analysis_summary="Error parsing response",
                decisions=[],
                batch_groups={},
                overall_recommendations=[f"Failed to parse response: {str(e)}"],
                processing_time=0
            )
    
    async def cleanup_mcp_sessions(self):
        """Clean up MCP server connections"""
        for name, session in self.mcp_sessions.items():
            try:
                await session.close()
            except Exception as e:
                logger.error(f"Error closing {name} session: {e}")
        
        self.mcp_sessions.clear()

# Usage example
async def main():
    """Example usage of the NotificationAgent"""
    agent = NotificationAgent()
    
    # Sample notifications for testing
    notifications = [
        {
            "id": "email_123",
            "platform": "gmail",
            "sender": "sarah.chen@company.com",
            "subject": "Q4 budget review - need your input",
            "content": "Hi John, can you review the attached budget proposal before tomorrow's meeting? We need to finalize numbers for the board presentation.",
            "timestamp": "2024-08-17T14:30:00Z",
            "type": "email"
        },
        {
            "id": "slack_456",
            "platform": "slack",
            "sender": "mike.jones",
            "subject": "Quick question about API endpoint",
            "content": "Hey, the /users endpoint is returning 500 errors. Is this a known issue?",
            "timestamp": "2024-08-17T14:35:00Z",
            "type": "direct_message"
        },
        {
            "id": "calendar_789",
            "platform": "calendar",
            "sender": "calendar@company.com",
            "subject": "Meeting reminder: Team standup in 15 minutes",
            "content": "Daily team standup starting at 3:00 PM in Conference Room A",
            "timestamp": "2024-08-17T14:45:00Z",
            "type": "meeting_reminder"
        },
        {
            "id": "newsletter_101",
            "platform": "gmail",
            "sender": "techcrunch@newsletter.com",
            "subject": "TechCrunch Daily: Latest startup news",
            "content": "Today's top stories from the world of technology and startups...",
            "timestamp": "2024-08-17T14:00:00Z",
            "type": "newsletter"
        }
    ]
    
    try:
        result = await agent.process_notifications(notifications)
        
        print("=" * 50)
        print("NOTIFICATION ANALYSIS RESULTS")
        print("=" * 50)
        
        print(f"\nAnalysis Summary: {result.analysis_summary}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        
        print(f"\nDecisions ({len(result.decisions)}):")
        for decision in result.decisions:
            print(f"\n📧 {decision.notification_id}")
            print(f"   Decision: {decision.decision}")
            print(f"   Scores: Urgency {decision.urgency_score}/10, Importance {decision.importance_score}/10")
            print(f"   Reasoning: {decision.reasoning}")
            print(f"   Action: {decision.suggested_action}")
            if decision.batch_group:
                print(f"   Batch Group: {decision.batch_group}")
        
        if result.batch_groups:
            print(f"\nBatch Groups ({len(result.batch_groups)}):")
            for group_name, group in result.batch_groups.items():
                print(f"\n📦 {group_name}")
                print(f"   Notifications: {len(group.notifications)}")
                print(f"   Summary: {group.summary}")
                print(f"   Timing: {group.suggested_timing}")
        
        if result.overall_recommendations:
            print(f"\nRecommendations:")
            for rec in result.overall_recommendations:
                print(f"   • {rec}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())