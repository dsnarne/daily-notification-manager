"""
Microsoft Teams integration service for DaiLY Notification Manager
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import requests

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

from ..models.schemas import TeamsConfig
from ..core.config import TEAMS_EVENT_TYPES

logger = logging.getLogger(__name__)

class TeamsIntegration:
    """Microsoft Teams integration service"""
    
    def __init__(self, config: TeamsConfig):
        self.config = config
        self.graph_client = None
        self.credential = None
        
        # Initialize credential
        if config.client_id and config.client_secret and config.tenant_id:
            self.credential = ClientSecretCredential(
                tenant_id=config.tenant_id,
                client_id=config.client_id,
                client_secret=config.client_secret
            )
            
            # Initialize Graph client
            self.graph_client = GraphClient(credential=self.credential)
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        try:
            if not self.credential:
                logger.error("Teams credentials not configured")
                return False
            
            # Test authentication by getting user info
            response = self.graph_client.get('/me')
            if response.status_code == 200:
                logger.info("Teams API authenticated successfully")
                return True
            else:
                logger.error(f"Teams authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Teams authentication error: {e}")
            return False
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get list of teams the user has access to"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return []
            
            response = self.graph_client.get('/me/joinedTeams')
            
            if response.status_code == 200:
                teams_data = response.json()
                return teams_data.get('value', [])
            else:
                logger.error(f"Failed to get teams: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []
    
    def get_channels(self, team_id: str) -> List[Dict[str, Any]]:
        """Get channels in a team"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return []
            
            response = self.graph_client.get(f'/teams/{team_id}/channels')
            
            if response.status_code == 200:
                channels_data = response.json()
                return channels_data.get('value', [])
            else:
                logger.error(f"Failed to get channels: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return []
    
    def get_channel_messages(self, team_id: str, channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from a channel"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return []
            
            response = self.graph_client.get(
                f'/teams/{team_id}/channels/{channel_id}/messages',
                params={'$top': limit, '$orderby': 'createdDateTime desc'}
            )
            
            if response.status_code == 200:
                messages_data = response.json()
                return messages_data.get('value', [])
            else:
                logger.error(f"Failed to get channel messages: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting channel messages: {e}")
            return []
    
    def get_chat_messages(self, chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from a chat"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return []
            
            response = self.graph_client.get(
                f'/chats/{chat_id}/messages',
                params={'$top': limit, '$orderby': 'createdDateTime desc'}
            )
            
            if response.status_code == 200:
                messages_data = response.json()
                return messages_data.get('value', [])
            else:
                logger.error(f"Failed to get chat messages: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    def get_mentions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages that mention the user"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return []
            
            # Search for messages mentioning the user
            response = self.graph_client.get(
                '/search/query',
                json={
                    "requests": [{
                        "entityTypes": ["message"],
                        "query": f"mentions:{user_id}",
                        "from": 0,
                        "size": limit
                    }]
                }
            )
            
            if response.status_code == 200:
                search_data = response.json()
                return search_data.get('value', [])
            else:
                logger.error(f"Failed to search mentions: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching mentions: {e}")
            return []
    
    def send_message(self, team_id: str, channel_id: str, content: str, content_type: str = "text") -> bool:
        """Send a message to a channel"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return False
            
            message_body = {
                "body": {
                    "content": content,
                    "contentType": content_type
                }
            }
            
            response = self.graph_client.post(
                f'/teams/{team_id}/channels/{channel_id}/messages',
                json=message_body
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Message sent to channel {channel_id}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_chat_message(self, chat_id: str, content: str, content_type: str = "text") -> bool:
        """Send a message to a chat"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return False
            
            message_body = {
                "body": {
                    "content": content,
                    "contentType": content_type
                }
            }
            
            response = self.graph_client.post(
                f'/chats/{chat_id}/messages',
                json=message_body
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Message sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to send chat message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            return False
    
    def send_notification(self, team_id: str, channel_id: str, title: str, content: str, priority: str = "medium") -> bool:
        """Send a formatted notification message"""
        try:
            # Create rich text content
            rich_content = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <h2 style="color: #0078d4; margin-bottom: 10px;">{title}</h2>
                <div style="background-color: #f3f2f1; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    {content}
                </div>
                <div style="margin-top: 15px; font-size: 12px; color: #666;">
                    Priority: {priority.upper()}
                </div>
            </div>
            """
            
            return self.send_message(team_id, channel_id, rich_content, "html")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return None
            
            response = self.graph_client.get(f'/users/{user_id}')
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def get_team_info(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a team"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return None
            
            response = self.graph_client.get(f'/teams/{team_id}')
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get team info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            return None
    
    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Teams webhook event"""
        try:
            event_type = event.get("eventType")
            resource_data = event.get("resourceData", {})
            
            if event_type not in TEAMS_EVENT_TYPES:
                logger.warning(f"Unsupported Teams event type: {event_type}")
                return {"processed": False, "reason": "unsupported_event_type"}
            
            # Process different event types
            if event_type == "message":
                return self._handle_message_event(resource_data)
            elif event_type == "mention":
                return self._handle_mention_event(resource_data)
            elif event_type == "reaction":
                return self._handle_reaction_event(resource_data)
            elif event_type == "teamMemberAdded":
                return self._handle_member_event(resource_data, "added")
            elif event_type == "teamMemberRemoved":
                return self._handle_member_event(resource_data, "removed")
            else:
                return {"processed": True, "event_type": event_type}
                
        except Exception as e:
            logger.error(f"Error handling Teams event: {e}")
            return {"processed": False, "error": str(e)}
    
    def _handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message event"""
        return {
            "processed": True,
            "event_type": "message",
            "team_id": event_data.get("teamId"),
            "channel_id": event_data.get("channelId"),
            "user_id": event_data.get("from", {}).get("user", {}).get("id"),
            "content": event_data.get("body", {}).get("content"),
            "created_time": event_data.get("createdDateTime")
        }
    
    def _handle_mention_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mention event"""
        return {
            "processed": True,
            "event_type": "mention",
            "team_id": event_data.get("teamId"),
            "channel_id": event_data.get("channelId"),
            "user_id": event_data.get("from", {}).get("user", {}).get("id"),
            "mentioned_user": event_data.get("mentions", []),
            "content": event_data.get("body", {}).get("content")
        }
    
    def _handle_reaction_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reaction event"""
        return {
            "processed": True,
            "event_type": "reaction",
            "team_id": event_data.get("teamId"),
            "channel_id": event_data.get("channelId"),
            "user_id": event_data.get("from", {}).get("user", {}).get("id"),
            "reaction": event_data.get("reactionType"),
            "message_id": event_data.get("messageId")
        }
    
    def _handle_member_event(self, event_data: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Handle team member event"""
        return {
            "processed": True,
            "event_type": f"teamMember{action.capitalize()}",
            "team_id": event_data.get("teamId"),
            "user_id": event_data.get("userId"),
            "action": action
        }
    
    def create_webhook_subscription(self, resource: str, change_type: str = "created,updated,deleted") -> Optional[str]:
        """Create a webhook subscription for Teams events"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return None
            
            subscription_body = {
                "changeType": change_type,
                "notificationUrl": f"https://your-domain.com/api/v1/teams/webhook",
                "resource": resource,
                "expirationDateTime": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
                "clientState": "daily-notification-manager"
            }
            
            response = self.graph_client.post('/subscriptions', json=subscription_body)
            
            if response.status_code in [200, 201]:
                subscription_data = response.json()
                logger.info(f"Webhook subscription created: {subscription_data.get('id')}")
                return subscription_data.get('id')
            else:
                logger.error(f"Failed to create webhook subscription: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating webhook subscription: {e}")
            return None
    
    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """Delete a webhook subscription"""
        try:
            if not self.graph_client:
                logger.error("Graph client not initialized")
                return False
            
            response = self.graph_client.delete(f'/subscriptions/{subscription_id}')
            
            if response.status_code == 204:
                logger.info(f"Webhook subscription deleted: {subscription_id}")
                return True
            else:
                logger.error(f"Failed to delete webhook subscription: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting webhook subscription: {e}")
            return False 