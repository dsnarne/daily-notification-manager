# mcp-servers/communication-server/integrations/slack.py
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from collections import defaultdict, Counter

from dotenv import load_dotenv

try:
    from ..models import SenderImportance, ConversationMessage, DomainInfo, SlackUserInfo, SlackChannelInfo
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from mcp_servers.communication_server.models import SenderImportance, ConversationMessage, DomainInfo, SlackUserInfo, SlackChannelInfo

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class SlackIntegration:
    """Slack integration for notification and communication analysis using user tokens"""
    
    def __init__(self):
        self.user_token = os.getenv("SLACK_USER_TOKEN")
        self.base_url = "https://slack.com/api"
        
        if not self.user_token:
            raise RuntimeError("Missing env: SLACK_USER_TOKEN")
    
    async def _make_api_call(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make authenticated API call to Slack using user token"""
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if params:
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()
            else:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
        
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'Unknown error')}")
        
        return data
    
    async def list_notifications(self,
                                since_timestamp: Optional[str] = None,
                                channel_filter: Optional[str] = None,
                                max_results: int = 20) -> List[Dict]:
        """List recent Slack notifications/messages with filters"""
        
        try:
            # Get list of channels first
            channels_data = await self._make_api_call("conversations.list", {
                "types": "public_channel,private_channel,im,mpim",
                "exclude_archived": "true",
                "limit": 100
            })
            
            channels = channels_data.get("channels", [])
            notifications = []
            
            # Calculate since timestamp
            since_ts = None
            if since_timestamp:
                try:
                    dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
                    since_ts = str(dt.timestamp())
                except Exception:
                    # Default to 1 day ago if parsing fails
                    since_ts = str((datetime.now() - timedelta(days=1)).timestamp())
            else:
                since_ts = str((datetime.now() - timedelta(days=1)).timestamp())
            
            # Filter channels if specified
            if channel_filter:
                channels = [ch for ch in channels if channel_filter.lower() in ch.get("name", "").lower()]
            
            # Get messages from channels
            for channel in channels[:10]:  # Limit to first 10 channels to avoid rate limits
                try:
                    messages_data = await self._make_api_call("conversations.history", {
                        "channel": channel["id"],
                        "oldest": since_ts,
                        "limit": max_results // len(channels[:10]) + 1
                    })
                    
                    messages = messages_data.get("messages", [])
                    
                    for msg in messages:
                        # Skip bot messages and system messages
                        if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                            continue
                        
                        # Get user info
                        user_info = {}
                        if msg.get("user"):
                            try:
                                user_data = await self._make_api_call("users.info", {"user": msg["user"]})
                                user_info = user_data.get("user", {})
                            except:
                                user_info = {"real_name": "Unknown User", "profile": {"email": ""}}
                        
                        # Convert timestamp
                        created_at = datetime.fromtimestamp(float(msg.get("ts", "0")))
                        
                        # Build notification object
                        notification = {
                            "id": f"slack:{msg.get('ts', '')}",
                            "external_id": msg.get("ts", ""),
                            "thread_id": msg.get("thread_ts", ""),
                            "platform": "slack",
                            "notification_type": "message",
                            "title": f"Message in #{channel.get('name', 'unknown')}",
                            "content": msg.get("text", ""),
                            "sender": user_info.get("real_name", "Unknown User"),
                            "sender_id": msg.get("user", ""),
                            "recipient": f"#{channel.get('name', 'unknown')}",
                            "priority": self._determine_priority(msg, channel, user_info),
                            "metadata": {
                                "channel_id": channel["id"],
                                "channel_name": channel.get("name", ""),
                                "channel_type": channel.get("is_private", False) and "private" or "public",
                                "thread_ts": msg.get("thread_ts", ""),
                                "is_thread_reply": bool(msg.get("thread_ts")),
                                "reaction_count": len(msg.get("reactions", [])),
                                "reply_count": msg.get("reply_count", 0)
                            },
                            "created_at": created_at,
                            "link": f"https://app.slack.com/client/{channel.get('team_id', '')}/{channel['id']}/thread/{msg.get('ts', '')}"
                        }
                        
                        notifications.append(notification)
                        
                        if len(notifications) >= max_results:
                            break
                    
                except Exception as e:
                    print(f"Error processing channel {channel.get('name')}: {e}")
                    continue
                
                if len(notifications) >= max_results:
                    break
            
            # Sort by timestamp (newest first)
            notifications.sort(key=lambda x: x["created_at"], reverse=True)
            
            return notifications[:max_results]
            
        except Exception as e:
            print(f"Error fetching Slack notifications: {e}")
            return []
    
    def _determine_priority(self, message: Dict, channel: Dict, user_info: Dict) -> str:
        """Determine message priority based on content and context"""
        text = message.get("text", "").lower()
        channel_name = channel.get("name", "").lower()
        
        # Check for urgent keywords
        urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediate", "help", "issue", "down", "broken"]
        if any(keyword in text for keyword in urgent_keywords):
            return "urgent"
        
        # Check if it's a direct mention or DM
        if channel.get("is_im") or "@channel" in text or "@here" in text:
            return "high"
        
        # Check for important channels
        important_channels = ["alerts", "incidents", "urgent", "critical", "production", "ops"]
        if any(keyword in channel_name for keyword in important_channels):
            return "high"
        
        # Check for high priority keywords
        high_keywords = ["deadline", "meeting", "review", "approval", "action required", "fyi"]
        if any(keyword in text for keyword in high_keywords):
            return "high"
        
        return "medium"
    
    async def analyze_sender_importance(self,
                                      sender_id: str,
                                      days_back: int = 30) -> Dict:
        """Analyze sender importance based on communication history"""
        
        try:
            # Get user info
            user_data = await self._make_api_call("users.info", {"user": sender_id})
            user_info = user_data.get("user", {})
            
            # Get user's message activity across channels
            since_ts = str((datetime.now() - timedelta(days=days_back)).timestamp())
            
            # Search for messages from this user
            search_data = await self._make_api_call("search.messages", {
                "query": f"from:{sender_id} after:{since_ts}",
                "count": 100
            })
            
            messages = search_data.get("messages", {}).get("matches", [])
            message_count = len(messages)
            
            # Analyze user profile
            profile = user_info.get("profile", {})
            is_admin = user_info.get("is_admin", False)
            is_owner = user_info.get("is_owner", False)
            is_primary_owner = user_info.get("is_primary_owner", False)
            is_bot = user_info.get("is_bot", False)
            
            # Calculate importance score (0-10)
            importance_score = 5.0  # Base score
            
            # Adjust based on role
            if is_primary_owner:
                importance_score += 3.0
            elif is_owner:
                importance_score += 2.5
            elif is_admin:
                importance_score += 2.0
            elif is_bot:
                importance_score -= 2.0  # Bots are usually less important
            
            # Adjust based on communication frequency
            monthly_frequency = (message_count / days_back) * 30
            if monthly_frequency > 50:
                importance_score += 1.5  # Very active user
            elif monthly_frequency > 20:
                importance_score += 1.0  # Regular user
            elif monthly_frequency < 5:
                importance_score -= 0.5  # Inactive user
            
            # Adjust based on profile completeness (indicates active user)
            if profile.get("title") and profile.get("phone"):
                importance_score += 0.5
            
            # Cap at 10
            importance_score = min(10.0, max(0.0, importance_score))
            
            # Determine relationship type
            relationship_type = "external"
            if not user_info.get("is_restricted", True):
                relationship_type = "internal"
            elif user_info.get("is_ultra_restricted"):
                relationship_type = "guest"
            
            return {
                "sender": user_info.get("real_name", "Unknown User"),
                "sender_id": sender_id,
                "sender_email": profile.get("email", ""),
                "importance_score": importance_score,
                "message_frequency": int(monthly_frequency),
                "response_rate": 0.8,  # Mock value - would need conversation analysis
                "avg_response_time_hours": 4.0,  # Mock value
                "is_internal": relationship_type == "internal",
                "recent_interactions": message_count,
                "classification": "high_priority" if importance_score > 7 else "medium",
                "role": "admin" if is_admin else "owner" if is_owner else "user",
                "is_bot": is_bot,
                "title": profile.get("title", ""),
                "timezone": user_info.get("tz", "")
            }
            
        except Exception as e:
            # Return default low importance on error
            return {
                "sender_id": sender_id,
                "importance_score": 3.0,
                "relationship_type": "unknown",
                "message_frequency": 0,
                "avg_response_time_hours": None,
                "last_interaction": None,
                "context": f"Error analyzing sender: {str(e)}"
            }
    
    async def get_recent_conversations(self,
                                     user_id: str,
                                     days_back: int = 7,
                                     max_messages: int = 10) -> List[Dict]:
        """Get recent conversation history with a specific user"""
        
        try:
            # Get DM channel with the user
            dm_data = await self._make_api_call("conversations.open", {"users": user_id})
            channel_id = dm_data.get("channel", {}).get("id")
            
            if not channel_id:
                return []
            
            # Get conversation history
            since_ts = str((datetime.now() - timedelta(days=days_back)).timestamp())
            
            messages_data = await self._make_api_call("conversations.history", {
                "channel": channel_id,
                "oldest": since_ts,
                "limit": max_messages
            })
            
            messages = messages_data.get("messages", [])
            conversations = []
            
            for msg in messages:
                # Get user info for sender
                sender_name = "Unknown User"
                if msg.get("user"):
                    try:
                        user_data = await self._make_api_call("users.info", {"user": msg["user"]})
                        sender_name = user_data.get("user", {}).get("real_name", "Unknown User")
                    except:
                        pass
                
                timestamp = datetime.fromtimestamp(float(msg.get("ts", "0")))
                
                conversation = {
                    "id": msg.get("ts", ""),
                    "subject": f"DM with {sender_name}",
                    "sender": sender_name,
                    "sender_id": msg.get("user", ""),
                    "content_preview": msg.get("text", "")[:200],
                    "timestamp": timestamp,
                    "is_reply": bool(msg.get("thread_ts")),
                    "channel_id": channel_id,
                    "message_type": msg.get("subtype", "message")
                }
                
                conversations.append(conversation)
            
            # Sort by timestamp (newest first)
            conversations.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return conversations
            
        except Exception as e:
            print(f"Error getting conversations with user {user_id}: {e}")
            return []
    
    async def check_user_workspace(self, user_id: str) -> Dict:
        """Check user workspace information and permissions"""
        
        try:
            user_data = await self._make_api_call("users.info", {"user": user_id})
            user_info = user_data.get("user", {})
            
            # Get team info
            team_data = await self._make_api_call("team.info")
            team_info = team_data.get("team", {})
            
            # Determine user type
            user_type = "unknown"
            if user_info.get("is_bot"):
                user_type = "bot"
            elif user_info.get("is_primary_owner"):
                user_type = "primary_owner"
            elif user_info.get("is_owner"):
                user_type = "owner"
            elif user_info.get("is_admin"):
                user_type = "admin"
            elif user_info.get("is_restricted"):
                user_type = "guest"
            else:
                user_type = "member"
            
            return {
                "user_id": user_id,
                "user_name": user_info.get("real_name", "Unknown User"),
                "user_type": user_type,
                "is_internal": not user_info.get("is_restricted", True),
                "is_admin": user_info.get("is_admin", False),
                "is_bot": user_info.get("is_bot", False),
                "workspace_name": team_info.get("name", ""),
                "workspace_domain": team_info.get("domain", ""),
                "timezone": user_info.get("tz", ""),
                "profile_email": user_info.get("profile", {}).get("email", ""),
                "title": user_info.get("profile", {}).get("title", "")
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "user_type": "unknown",
                "is_internal": False,
                "error": f"Error checking user workspace: {str(e)}"
            }
    
    async def get_channel_info(self, channel_id: str) -> Dict:
        """Get detailed information about a Slack channel"""
        
        try:
            channel_data = await self._make_api_call("conversations.info", {"channel": channel_id})
            channel = channel_data.get("channel", {})
            
            # Get member count
            members_data = await self._make_api_call("conversations.members", {
                "channel": channel_id,
                "limit": 1
            })
            
            return {
                "channel_id": channel_id,
                "name": channel.get("name", ""),
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "is_private": channel.get("is_private", False),
                "is_archived": channel.get("is_archived", False),
                "member_count": len(members_data.get("members", [])),
                "created": datetime.fromtimestamp(channel.get("created", 0)),
                "creator": channel.get("creator", "")
            }
            
        except Exception as e:
            return {
                "channel_id": channel_id,
                "error": f"Error getting channel info: {str(e)}"
            }