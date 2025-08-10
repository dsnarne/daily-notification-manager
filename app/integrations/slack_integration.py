"""
Slack integration service for DaiLY Notification Manager
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json

from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.models.blocks import SectionBlock, DividerBlock, HeaderBlock

from ..models.schemas import SlackConfig
from ..core.config import SLACK_EVENT_TYPES

logger = logging.getLogger(__name__)

class SlackIntegration:
    """Slack integration service"""
    
    def __init__(self, config: SlackConfig):
        self.config = config
        self.web_client = None
        self.socket_client = None
        self.signature_verifier = None
        
        # Initialize clients
        if config.bot_token:
            self.web_client = WebClient(token=config.bot_token)
        
        if config.app_token:
            self.socket_client = SocketModeClient(
                app_token=config.app_token,
                web_client=self.web_client
            )
        
        if config.signing_secret:
            self.signature_verifier = SignatureVerifier(config.signing_secret)
    
    def verify_signature(self, timestamp: str, signature: str, body: str) -> bool:
        """Verify Slack request signature"""
        if not self.signature_verifier:
            return True  # Skip verification if no secret configured
        
        return self.signature_verifier.is_valid(
            timestamp=timestamp,
            signature=signature,
            body=body
        )
    
    def get_channels(self) -> List[Dict[str, Any]]:
        """Get list of channels the bot has access to"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return []
            
            response = self.web_client.conversations_list(
                types="public_channel,private_channel"
            )
            
            if response["ok"]:
                return response["channels"]
            else:
                logger.error(f"Failed to get channels: {response.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return []
    
    def get_channel_messages(self, channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent messages from a channel"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return []
            
            response = self.web_client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            
            if response["ok"]:
                return response["messages"]
            else:
                logger.error(f"Failed to get channel messages: {response.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting channel messages: {e}")
            return []
    
    def get_direct_messages(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get direct messages with a user"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return []
            
            # Open DM channel
            response = self.web_client.conversations_open(users=user_id)
            if not response["ok"]:
                logger.error(f"Failed to open DM: {response.get('error')}")
                return []
            
            channel_id = response["channel"]["id"]
            
            # Get messages
            response = self.web_client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            
            if response["ok"]:
                return response["messages"]
            else:
                logger.error(f"Failed to get DM messages: {response.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting DM messages: {e}")
            return []
    
    def get_mentions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages that mention the user"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return []
            
            # Search for messages mentioning the user
            query = f"<@{user_id}>"
            response = self.web_client.search_messages(
                query=query,
                count=limit
            )
            
            if response["ok"]:
                return response["messages"]["matches"]
            else:
                logger.error(f"Failed to search mentions: {response.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching mentions: {e}")
            return []
    
    def send_message(self, channel: str, text: str, blocks: Optional[List] = None) -> bool:
        """Send a message to a channel"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return False
            
            response = self.web_client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            
            if response["ok"]:
                logger.info(f"Message sent to {channel}")
                return True
            else:
                logger.error(f"Failed to send message: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_notification(self, channel: str, title: str, content: str, priority: str = "medium") -> bool:
        """Send a formatted notification message"""
        try:
            # Create blocks for rich formatting
            blocks = [
                HeaderBlock(text=title),
                DividerBlock(),
                SectionBlock(text=content)
            ]
            
            # Add priority indicator
            priority_emoji = {
                "low": "🔵",
                "medium": "🟡", 
                "high": "🟠",
                "urgent": "🔴"
            }
            
            priority_text = f"{priority_emoji.get(priority, '⚪')} Priority: {priority.upper()}"
            blocks.append(SectionBlock(text=priority_text))
            
            return self.send_message(channel, title, blocks)
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return None
            
            response = self.web_client.users_info(user=user_id)
            
            if response["ok"]:
                return response["user"]
            else:
                logger.error(f"Failed to get user info: {response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def get_workspace_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the workspace"""
        try:
            if not self.web_client:
                logger.error("Web client not initialized")
                return None
            
            response = self.web_client.team_info()
            
            if response["ok"]:
                return response["team"]
            else:
                logger.error(f"Failed to get team info: {response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            return None
    
    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Slack event"""
        try:
            event_type = event.get("type")
            event_data = event.get("event", {})
            
            if event_type not in SLACK_EVENT_TYPES:
                logger.warning(f"Unsupported event type: {event_type}")
                return {"processed": False, "reason": "unsupported_event_type"}
            
            # Process different event types
            if event_type == "message":
                return self._handle_message_event(event_data)
            elif event_type == "app_mention":
                return self._handle_mention_event(event_data)
            elif event_type == "direct_message":
                return self._handle_dm_event(event_data)
            else:
                return {"processed": True, "event_type": event_type}
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return {"processed": False, "error": str(e)}
    
    def _handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message event"""
        return {
            "processed": True,
            "event_type": "message",
            "channel": event_data.get("channel"),
            "user": event_data.get("user"),
            "text": event_data.get("text"),
            "ts": event_data.get("ts")
        }
    
    def _handle_mention_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app mention event"""
        return {
            "processed": True,
            "event_type": "app_mention",
            "channel": event_data.get("channel"),
            "user": event_data.get("user"),
            "text": event_data.get("text"),
            "ts": event_data.get("ts")
        }
    
    def _handle_dm_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct message event"""
        return {
            "processed": True,
            "event_type": "direct_message",
            "channel": event_data.get("channel"),
            "user": event_data.get("user"),
            "text": event_data.get("text"),
            "ts": event_data.get("ts")
        }
    
    def start_socket_mode(self, event_handler=None):
        """Start socket mode for real-time events"""
        if not self.socket_client:
            logger.error("Socket client not initialized")
            return
        
        if event_handler:
            self.socket_client.socket_mode_request_listeners.append(event_handler)
        
        try:
            self.socket_client.connect()
            logger.info("Slack socket mode started")
        except Exception as e:
            logger.error(f"Failed to start socket mode: {e}")
    
    def stop_socket_mode(self):
        """Stop socket mode"""
        if self.socket_client:
            self.socket_client.disconnect()
            logger.info("Slack socket mode stopped") 