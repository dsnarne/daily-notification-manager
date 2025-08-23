"""
Shared event emitter for SSE notifications
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationEventEmitter:
    """
    Centralized event emitter for notification updates.
    Allows different parts of the system to emit events that get sent via SSE.
    """
    
    _instance = None
    _listeners = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._listeners = []
            self._initialized = True
    
    def add_listener(self, callback):
        """Add a listener function that will be called when events are emitted"""
        if callback not in self._listeners:
            self._listeners.append(callback)
            logger.info(f"Added event listener: {callback}")
    
    def remove_listener(self, callback):
        """Remove a listener function"""
        if callback in self._listeners:
            self._listeners.remove(callback)
            logger.info(f"Removed event listener: {callback}")
    
    async def emit_reprioritized_notifications(self, notifications: List[Dict[str, Any]], summary: str = ""):
        """
        Emit reprioritized notifications to all active SSE streams
        
        Args:
            notifications: List of notification data with updated priorities
            summary: Optional summary of the reprioritization process
        """
        if not notifications:
            return
            
        logger.info(f"Emitting {len(notifications)} reprioritized notifications")
        
        # Create payload compatible with existing SSE format
        for notification in notifications:
            payload = {
                "source": "reprioritization",
                "type": "notification_update",
                "notification": notification,
                "analysis_summary": summary,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to all listeners (active SSE streams)
            await self._emit_event(payload)
    
    async def emit_context_update(self, user_id: int, context: str):
        """Emit a context update notification"""
        payload = {
            "source": "system",
            "type": "context_update", 
            "user_id": user_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._emit_event(payload)
    
    async def _emit_event(self, payload: Dict[str, Any]):
        """Send event to all registered listeners"""
        if not self._listeners:
            logger.debug("No active listeners for event emission")
            return
            
        # Convert to SSE format
        sse_data = f"data: {json.dumps(payload, default=str)}\n\n"
        
        # Send to all listeners (these are async generators from SSE streams)
        for listener in self._listeners[:]:  # Copy to avoid mutation during iteration
            try:
                await listener(sse_data)
            except Exception as e:
                logger.error(f"Error sending event to listener: {e}")
                # Remove broken listeners
                try:
                    self._listeners.remove(listener)
                except ValueError:
                    pass  # Already removed

# Global instance
notification_emitter = NotificationEventEmitter()