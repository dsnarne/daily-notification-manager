"""
Notification management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Any, Optional
import logging

from ...models.schemas import (
    NotificationCreate, NotificationUpdate, Notification,
    NotificationFilter, NotificationPriority, NotificationStatus,
    SuccessResponse, ErrorResponse, PaginationParams, PaginatedResponse
)
from ...services.notification_service import NotificationService
from ...core.database import get_db
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
            notification_list.append(notification_data)
        
        # Process with agent using current context
        agent = NotificationAgent()
        result = await agent.process_notifications(notification_list, user_id=user_id)
        
        # Update notification priorities based on agent decisions
        updated_count = 0
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