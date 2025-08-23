"""
Notification management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json

from ...models.schemas import (
    NotificationCreate, NotificationUpdate, Notification,
    NotificationFilter, NotificationPriority, NotificationStatus,
    SuccessResponse, ErrorResponse, PaginationParams, PaginatedResponse
)
from ...services.notification_service import NotificationService
from ...core.database import get_db
from ...core.event_emitter import notification_emitter
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/reprioritize", response_model=SuccessResponse)
async def reprioritize_notifications(
    db: Session = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """
    Reprioritize all existing notifications based on current user context.
    This endpoint is called when user updates their working context.
    """
    try:
        # Import here to avoid circular imports
        from agent.client import NotificationAgent
        
        # Get recent notifications (last 24 hours) for reprioritization
        service = NotificationService(db)
        recent_notifications = await service.get_recent_notifications(user_id, hours_back=24)
        
        if not recent_notifications:
            return SuccessResponse(
                message="No recent notifications to reprioritize"
            )
        
        # Convert to format expected by agent
        notification_list = []
        for notif in recent_notifications:
            # Handle both database objects and dictionaries
            if hasattr(notif, 'id'):
                # Database object
                notification_data = {
                    "id": str(notif.id),
                    "platform": notif.platform,
                    "sender": notif.sender,
                    "subject": notif.title,
                    "content": notif.content,
                    "timestamp": notif.created_at.isoformat() if notif.created_at else "",
                    "type": notif.notification_type,
                    "priority": notif.priority
                }
            else:
                # Dictionary
                notification_data = {
                    "id": str(notif.get("id")),
                    "platform": notif.get("platform"),
                    "sender": notif.get("sender"),
                    "subject": notif.get("title") or notif.get("subject"),
                    "content": notif.get("content"),
                    "timestamp": notif.get("created_at") or notif.get("timestamp", ""),
                    "type": notif.get("notification_type") or notif.get("type"),
                    "priority": notif.get("priority")
                }
            notification_list.append(notification_data)
        
        # Process with agent using current context
        agent = NotificationAgent()
        result = await agent.process_notifications(notification_list, user_id=user_id)
        
        # Update notification priorities based on agent decisions
        updated_count = 0
        updated_notifications = []
        if result.decisions:
            for decision in result.decisions:
                # Map agent categories to priority levels
                priority_mapping = {
                    "IMMEDIATE": "urgent",
                    "BATCH": "high", 
                    "DIGEST": "medium",
                    "FILTER": "low"
                }
                
                new_priority = priority_mapping.get(decision.decision, "medium")
                
                # Update in database
                success = await service.update_notification_priority(
                    int(decision.notification_id), 
                    new_priority
                )
                if success:
                    updated_count += 1
                    # Get the updated notification for emission
                    updated_notif = await service.get_notification(int(decision.notification_id))
                    if updated_notif:
                        # Handle both database objects and dictionaries
                        if hasattr(updated_notif, 'id'):
                            # Database object
                            notification_dict = {
                                "id": str(updated_notif.id),
                                "platform": updated_notif.platform,
                                "sender": updated_notif.sender,
                                "subject": updated_notif.title,
                                "content": updated_notif.content,
                                "timestamp": updated_notif.created_at.isoformat() if updated_notif.created_at else "",
                                "type": updated_notif.notification_type,
                                "priority": updated_notif.priority,
                                "classification": {
                                    "decision": decision.decision,
                                    "urgency_score": decision.urgency_score,
                                    "importance_score": decision.importance_score,
                                    "reasoning": decision.reasoning,
                                    "suggested_action": decision.suggested_action,
                                    "batch_group": decision.batch_group,
                                    "context_used": decision.context_used
                                }
                            }
                        else:
                            # Dictionary
                            notification_dict = {
                                "id": str(updated_notif.get("id")),
                                "platform": updated_notif.get("platform"),
                                "sender": updated_notif.get("sender"),
                                "subject": updated_notif.get("title") or updated_notif.get("subject"),
                                "content": updated_notif.get("content"),
                                "timestamp": updated_notif.get("created_at") or updated_notif.get("timestamp", ""),
                                "type": updated_notif.get("notification_type") or updated_notif.get("type"),
                                "priority": updated_notif.get("priority"),
                                "classification": {
                                    "decision": decision.decision,
                                    "urgency_score": decision.urgency_score,
                                    "importance_score": decision.importance_score,
                                    "reasoning": decision.reasoning,
                                    "suggested_action": decision.suggested_action,
                                    "batch_group": decision.batch_group,
                                    "context_used": decision.context_used
                                }
                            }
                        updated_notifications.append(notification_dict)
        
        # Emit updated notifications via SSE to frontend
        if updated_notifications:
            await notification_emitter.emit_reprioritized_notifications(
                updated_notifications, 
                result.analysis_summary or f"Reprioritized {updated_count} notifications based on current context"
            )
        
        return SuccessResponse(
            message=f"Successfully reprioritized {updated_count} notifications based on current context"
        )
        
    except Exception as e:
        logger.error(f"Error reprioritizing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprioritize notifications: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_notifications(
    platform: Optional[str] = None,
    priority: Optional[NotificationPriority] = None,
    status: Optional[NotificationStatus] = None,
    notification_type: Optional[str] = None,
    sender: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List notifications with filtering and pagination"""
    try:
        service = NotificationService(db)
        notifications, total = await service.list_notifications(
            platform=platform,
            priority=priority,
            status=status,
            notification_type=notification_type,
            sender=sender,
            page=page,
            size=size
        )
        
        pages = (total + size - 1) // size
        
        return PaginatedResponse(
            items=notifications,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}"
        )

@router.get("/fetch-real", response_model=List[Dict[str, Any]])
async def fetch_real_notifications():
    """Fetch real Gmail and Slack notifications directly"""
    try:
        # For now, return mock "real" notifications to demonstrate the functionality
        # This simulates what your real Gmail/Slack notifications would look like
        from datetime import datetime, timedelta
        import uuid
        
        mock_real_notifications = [
            {
                "id": f"gmail_real_{uuid.uuid4().hex[:8]}",
                "platform": "gmail",
                "sender": "your.boss@company.com",
                "title": "🔴 URGENT: Q4 Budget Review",
                "content": "Please review the Q4 budget numbers before tomorrow's meeting...",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "email",
                "priority": "urgent",
                "status": "unread"
            },
            {
                "id": f"gmail_real_{uuid.uuid4().hex[:8]}",
                "platform": "gmail", 
                "sender": "newsletter@techcrunch.com",
                "title": "Daily Tech News - August 23rd",
                "content": "Today's top tech stories: AI developments, startup news...",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "newsletter",
                "priority": "low",
                "status": "unread"
            },
            {
                "id": f"slack_real_{uuid.uuid4().hex[:8]}",
                "platform": "slack",
                "sender": "sarah.dev",
                "title": "Slack: Hey, can you review my PR?",
                "content": "Just pushed the new feature implementation, would love your feedback",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "type": "message",
                "priority": "medium",
                "status": "unread"
            },
            {
                "id": f"slack_real_{uuid.uuid4().hex[:8]}",
                "platform": "slack",
                "sender": "alerts-bot",
                "title": "Slack: Production Alert",
                "content": "CPU usage spike detected on server-prod-01",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "type": "alert",
                "priority": "high",
                "status": "unread"
            }
        ]
        
        logger.info(f"Returning {len(mock_real_notifications)} mock real notifications")
        return mock_real_notifications
        
    except Exception as e:
        logger.error(f"Error fetching real notifications: {e}")
        return []

@router.get("/stream", response_class=StreamingResponse)
async def notification_stream():
    """Simple SSE stream for reprioritized notifications"""
    async def event_generator():
        # Store outbound messages queue for this stream
        message_queue = asyncio.Queue()
        
        # Register this stream with the event emitter to receive reprioritized notifications
        async def queue_message(sse_data):
            await message_queue.put(sse_data)
        
        notification_emitter.add_listener(queue_message)
        
        try:
            # Send initial heartbeat
            yield f"data: {json.dumps({'source': 'system', 'type': 'connected', 'message': 'Notification stream connected'})}\n\n"
            
            while True:
                try:
                    # Check for queued messages from reprioritization
                    try:
                        queued_message = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                        yield queued_message
                    except asyncio.TimeoutError:
                        # Send heartbeat every 30 seconds to keep connection alive
                        yield f"data: {json.dumps({'source': 'system', 'type': 'heartbeat', 'message': 'Stream active'})}\n\n"
                        
                except Exception as e:
                    logger.error(f"Error in notification stream: {e}")
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                    break
                    
        finally:
            # Clean up: remove this stream from the event emitter
            try:
                notification_emitter.remove_listener(queue_message)
            except Exception as e:
                logger.error(f"Error removing stream listener: {e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific notification by ID"""
    try:
        service = NotificationService(db)
        notification = await service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification: {str(e)}"
        )

@router.put("/{notification_id}", response_model=SuccessResponse)
async def update_notification(
    notification_id: int,
    notification: NotificationUpdate,
    db: Session = Depends(get_db)
):
    """Update a notification (e.g., mark as read, change priority)"""
    try:
        service = NotificationService(db)
        result = await service.update_notification(notification_id, notification)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )

@router.delete("/{notification_id}", response_model=SuccessResponse)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    try:
        service = NotificationService(db)
        result = await service.delete_notification(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

@router.post("/{notification_id}/mark-read", response_model=SuccessResponse)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    try:
        service = NotificationService(db)
        result = await service.mark_notification_read(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification marked as read"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.post("/{notification_id}/archive", response_model=SuccessResponse)
async def archive_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Archive a notification"""
    try:
        service = NotificationService(db)
        result = await service.archive_notification(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification archived successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive notification: {str(e)}"
        )

@router.post("/bulk-mark-read", response_model=SuccessResponse)
async def bulk_mark_read(
    notification_ids: List[int],
    db: Session = Depends(get_db)
):
    """Mark multiple notifications as read"""
    try:
        service = NotificationService(db)
        count = await service.bulk_mark_read(notification_ids)
        return SuccessResponse(
            message=f"Marked {count} notifications as read"
        )
    except Exception as e:
        logger.error(f"Failed to bulk mark notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk mark notifications as read: {str(e)}"
        )

@router.get("/summary/stats", response_model=Dict[str, Any])
async def get_notification_stats(
    db: Session = Depends(get_db)
):
    """Get notification statistics and summary"""
    try:
        service = NotificationService(db)
        stats = await service.get_notification_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification stats: {str(e)}"
        )

@router.post("/filter", response_model=List[Notification])
async def filter_notifications(
    filter_criteria: NotificationFilter,
    db: Session = Depends(get_db)
):
    """Filter notifications based on custom criteria"""
    try:
        service = NotificationService(db)
        notifications = await service.filter_notifications(filter_criteria)
        return notifications
    except Exception as e:
        logger.error(f"Failed to filter notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter notifications: {str(e)}"
        )

