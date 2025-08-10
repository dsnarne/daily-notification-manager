"""
Webhook/WebX integration service for DaiLY Notification Manager
Handles custom integrations and third-party service notifications
"""

import logging
import hashlib
import hmac
import json
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import aiohttp
import requests
from urllib.parse import urlparse

from ..models.schemas import WebhookConfig
from ..core.config import settings

logger = logging.getLogger(__name__)

class WebhookIntegration:
    """Webhook integration service for custom integrations"""
    
    def __init__(self, config: WebhookConfig):
        self.config = config
        self.session = None
        self.verification_enabled = bool(config.secret)
        
    async def create_session(self):
        """Create aiohttp session for async operations"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=self.config.headers or {}
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def verify_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """Verify webhook signature for security"""
        if not self.verification_enabled:
            return True
        
        try:
            # Check timestamp to prevent replay attacks
            if timestamp:
                ts = int(timestamp)
                if abs(time.time() - ts) > 300:  # 5 minutes tolerance
                    logger.warning("Webhook timestamp too old")
                    return False
            
            # Create expected signature
            expected_signature = hmac.new(
                self.config.secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def send_webhook(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Send data to webhook endpoint"""
        try:
            await self.create_session()
            
            # Prepare headers
            webhook_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'DaiLY-Notification-Manager/1.0'
            }
            
            if headers:
                webhook_headers.update(headers)
            
            # Add timestamp for verification
            if self.verification_enabled:
                timestamp = str(int(time.time()))
                webhook_headers['X-Webhook-Timestamp'] = timestamp
                
                # Create signature
                payload = json.dumps(data, sort_keys=True)
                signature = hmac.new(
                    self.config.secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                webhook_headers['X-Webhook-Signature'] = f"sha256={signature}"
            
            # Send request
            async with self.session.post(
                self.config.url,
                json=data,
                headers=webhook_headers
            ) as response:
                if response.status in [200, 201, 202]:
                    logger.info(f"Webhook sent successfully to {self.config.url}")
                    return True
                else:
                    logger.error(f"Webhook failed with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False
    
    def send_webhook_sync(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Send webhook synchronously"""
        try:
            # Prepare headers
            webhook_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'DaiLY-Notification-Manager/1.0'
            }
            
            if headers:
                webhook_headers.update(headers)
            
            # Add timestamp for verification
            if self.verification_enabled:
                timestamp = str(int(time.time()))
                webhook_headers['X-Webhook-Timestamp'] = timestamp
                
                # Create signature
                payload = json.dumps(data, sort_keys=True)
                signature = hmac.new(
                    self.config.secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                webhook_headers['X-Webhook-Signature'] = f"sha256={signature}"
            
            # Send request
            response = requests.post(
                self.config.url,
                json=data,
                headers=webhook_headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook sent successfully to {self.config.url}")
                return True
            else:
                logger.error(f"Webhook failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False
    
    def handle_incoming_webhook(self, payload: str, signature: str, timestamp: str) -> Dict[str, Any]:
        """Handle incoming webhook data"""
        try:
            # Verify signature
            if not self.verify_signature(payload, signature, timestamp):
                logger.warning("Invalid webhook signature")
                return {"valid": False, "error": "Invalid signature"}
            
            # Parse payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error("Invalid JSON payload")
                return {"valid": False, "error": "Invalid JSON"}
            
            # Process webhook data
            return self._process_webhook_data(data)
            
        except Exception as e:
            logger.error(f"Error handling incoming webhook: {e}")
            return {"valid": False, "error": str(e)}
    
    def _process_webhook_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook data"""
        try:
            # Extract common fields
            webhook_type = data.get('type', 'unknown')
            source = data.get('source', 'unknown')
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            
            # Process based on webhook type
            if webhook_type == 'notification':
                return self._process_notification_webhook(data)
            elif webhook_type == 'alert':
                return self._process_alert_webhook(data)
            elif webhook_type == 'task':
                return self._process_task_webhook(data)
            elif webhook_type == 'event':
                return self._process_event_webhook(data)
            else:
                return self._process_generic_webhook(data)
                
        except Exception as e:
            logger.error(f"Error processing webhook data: {e}")
            return {"valid": False, "error": str(e)}
    
    def _process_notification_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process notification webhook"""
        return {
            "valid": True,
            "type": "notification",
            "title": data.get('title', 'Webhook Notification'),
            "content": data.get('content', ''),
            "priority": data.get('priority', 'medium'),
            "sender": data.get('sender', ''),
            "source": data.get('source', ''),
            "timestamp": data.get('timestamp'),
            "metadata": data.get('metadata', {})
        }
    
    def _process_alert_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process alert webhook"""
        return {
            "valid": True,
            "type": "alert",
            "title": data.get('title', 'Webhook Alert'),
            "content": data.get('message', ''),
            "priority": data.get('severity', 'medium'),
            "sender": data.get('source', ''),
            "source": data.get('source', ''),
            "timestamp": data.get('timestamp'),
            "metadata": {
                "alert_id": data.get('id'),
                "category": data.get('category'),
                "status": data.get('status')
            }
        }
    
    def _process_task_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process task webhook"""
        return {
            "valid": True,
            "type": "task",
            "title": data.get('title', 'Webhook Task'),
            "content": data.get('description', ''),
            "priority": data.get('priority', 'medium'),
            "sender": data.get('assignee', ''),
            "source": data.get('source', ''),
            "timestamp": data.get('timestamp'),
            "metadata": {
                "task_id": data.get('id'),
                "status": data.get('status'),
                "due_date": data.get('due_date')
            }
        }
    
    def _process_event_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process event webhook"""
        return {
            "valid": True,
            "type": "event",
            "title": data.get('title', 'Webhook Event'),
            "content": data.get('description', ''),
            "priority": data.get('priority', 'medium'),
            "sender": data.get('triggered_by', ''),
            "source": data.get('source', ''),
            "timestamp": data.get('timestamp'),
            "metadata": {
                "event_id": data.get('id'),
                "event_type": data.get('event_type'),
                "action": data.get('action')
            }
        }
    
    def _process_generic_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic webhook data"""
        return {
            "valid": True,
            "type": "generic",
            "title": data.get('title', 'Webhook Message'),
            "content": str(data.get('data', '')),
            "priority": data.get('priority', 'medium'),
            "sender": data.get('from', ''),
            "source": data.get('source', ''),
            "timestamp": data.get('timestamp'),
            "metadata": data
        }

class WebhookManager:
    """Manager for multiple webhook integrations"""
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookIntegration] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
    
    def add_webhook(self, name: str, config: WebhookConfig) -> bool:
        """Add a new webhook integration"""
        try:
            self.webhooks[name] = WebhookIntegration(config)
            logger.info(f"Webhook '{name}' added successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to add webhook '{name}': {e}")
            return False
    
    def remove_webhook(self, name: str) -> bool:
        """Remove a webhook integration"""
        try:
            if name in self.webhooks:
                del self.webhooks[name]
                logger.info(f"Webhook '{name}' removed successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove webhook '{name}': {e}")
            return False
    
    def get_webhook(self, name: str) -> Optional[WebhookIntegration]:
        """Get a webhook integration by name"""
        return self.webhooks.get(name)
    
    def list_webhooks(self) -> List[str]:
        """List all webhook names"""
        return list(self.webhooks.keys())
    
    async def send_to_all_webhooks(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """Send data to all webhook integrations"""
        results = {}
        
        for name, webhook in self.webhooks.items():
            try:
                success = await webhook.send_webhook(data, headers)
                results[name] = success
            except Exception as e:
                logger.error(f"Error sending to webhook '{name}': {e}")
                results[name] = False
        
        return results
    
    def send_to_all_webhooks_sync(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """Send data to all webhook integrations synchronously"""
        results = {}
        
        for name, webhook in self.webhooks.items():
            try:
                success = webhook.send_webhook_sync(data, headers)
                results[name] = success
            except Exception as e:
                logger.error(f"Error sending to webhook '{name}': {e}")
                results[name] = False
        
        return results
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for specific webhook events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Event handler registered for '{event_type}'")
    
    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"Event handler unregistered for '{event_type}'")
    
    async def handle_webhook_event(self, webhook_name: str, payload: str, signature: str, timestamp: str) -> Dict[str, Any]:
        """Handle incoming webhook event"""
        try:
            webhook = self.webhooks.get(webhook_name)
            if not webhook:
                return {"valid": False, "error": f"Webhook '{webhook_name}' not found"}
            
            # Process webhook
            result = webhook.handle_incoming_webhook(payload, signature, timestamp)
            
            if result.get("valid"):
                # Trigger event handlers
                event_type = result.get("type", "generic")
                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            await handler(result)
                        except Exception as e:
                            logger.error(f"Error in event handler: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
            return {"valid": False, "error": str(e)}
    
    async def close_all_sessions(self):
        """Close all webhook sessions"""
        for webhook in self.webhooks.values():
            await webhook.close_session() 