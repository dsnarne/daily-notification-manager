"""
Notification service for managing and filtering notifications
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.schemas import (
    NotificationCreate, NotificationUpdate, Notification,
    NotificationFilter, NotificationPriority, NotificationStatus,
    NotificationType
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications across all platforms"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def list_notifications(
        self,
        platform: Optional[str] = None,
        priority: Optional[NotificationPriority] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[str] = None,
        sender: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List notifications with filtering and pagination"""
        try:
            # TODO: Query database with filters
            # For now, return mock data
            mock_notifications = self._generate_mock_notifications()
            
            # Apply filters
            filtered_notifications = self._apply_filters(
                mock_notifications,
                platform=platform,
                priority=priority,
                status=status,
                notification_type=notification_type,
                sender=sender
            )
            
            # Apply pagination
            total = len(filtered_notifications)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_notifications = filtered_notifications[start_idx:end_idx]
            
            return paginated_notifications, total
            
        except Exception as e:
            logger.error(f"Failed to list notifications: {e}")
            raise
    
    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific notification by ID"""
        try:
            # TODO: Query database
            # For now, return mock data
            mock_notifications = self._generate_mock_notifications()
            for notification in mock_notifications:
                if notification["id"] == notification_id:
                    return notification
            return None
            
        except Exception as e:
            logger.error(f"Failed to get notification: {e}")
            raise
    
    async def update_notification(self, notification_id: int, notification: NotificationUpdate) -> Optional[Dict[str, Any]]:
        """Update a notification"""
        try:
            # TODO: Update database
            # For now, return mock data
            existing_notification = await self.get_notification(notification_id)
            if not existing_notification:
                return None
            
            # Apply updates
            updated_notification = existing_notification.copy()
            if notification.title is not None:
                updated_notification["title"] = notification.title
            if notification.content is not None:
                updated_notification["content"] = notification.content
            if notification.priority is not None:
                updated_notification["priority"] = notification.priority
            if notification.status is not None:
                updated_notification["status"] = notification.status
            if notification.read_at is not None:
                updated_notification["read_at"] = notification.read_at
            
            updated_notification["updated_at"] = datetime.utcnow()
            
            return updated_notification
            
        except Exception as e:
            logger.error(f"Failed to update notification: {e}")
            raise
    
    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        try:
            # TODO: Delete from database
            # For now, return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            raise
    
    async def mark_notification_read(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Mark a notification as read"""
        try:
            notification = await self.get_notification(notification_id)
            if not notification:
                return None
            
            # Update status and read_at
            update_data = NotificationUpdate(
                status=NotificationStatus.READ,
                read_at=datetime.utcnow()
            )
            
            return await self.update_notification(notification_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            raise
    
    async def archive_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Archive a notification"""
        try:
            notification = await self.get_notification(notification_id)
            if not notification:
                return None
            
            # Update status to archived
            update_data = NotificationUpdate(status=NotificationStatus.ARCHIVED)
            
            return await self.update_notification(notification_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to archive notification: {e}")
            raise
    
    async def bulk_mark_read(self, notification_ids: List[int]) -> int:
        """Mark multiple notifications as read"""
        try:
            count = 0
            for notification_id in notification_ids:
                result = await self.mark_notification_read(notification_id)
                if result:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to bulk mark notifications as read: {e}")
            raise
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics and summary"""
        try:
            # TODO: Query database for actual stats
            # For now, return mock stats
            mock_notifications = self._generate_mock_notifications()
            
            total = len(mock_notifications)
            unread = len([n for n in mock_notifications if n["status"] == NotificationStatus.UNREAD])
            read = len([n for n in mock_notifications if n["status"] == NotificationStatus.READ])
            archived = len([n for n in mock_notifications if n["status"] == NotificationStatus.ARCHIVED])
            
            # Priority breakdown
            priority_stats = {}
            for priority in NotificationPriority:
                priority_stats[priority] = len([n for n in mock_notifications if n["priority"] == priority])
            
            # Platform breakdown
            platform_stats = {}
            for notification in mock_notifications:
                platform = notification["platform"]
                platform_stats[platform] = platform_stats.get(platform, 0) + 1
            
            # Recent activity (last 24 hours)
            now = datetime.utcnow()
            recent = len([n for n in mock_notifications if 
                         now - n["created_at"] < timedelta(hours=24)])
            
            return {
                "total": total,
                "unread": unread,
                "read": read,
                "archived": archived,
                "priority_breakdown": priority_stats,
                "platform_breakdown": platform_stats,
                "recent_24h": recent,
                "generated_at": now
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            raise
    
    async def filter_notifications(self, filter_criteria: NotificationFilter) -> List[Dict[str, Any]]:
        """Filter notifications based on custom criteria"""
        try:
            mock_notifications = self._generate_mock_notifications()
            
            filtered_notifications = self._apply_advanced_filters(
                mock_notifications, filter_criteria
            )
            
            return filtered_notifications
            
        except Exception as e:
            logger.error(f"Failed to filter notifications: {e}")
            raise
    
    def _generate_mock_notifications(self) -> List[Dict[str, Any]]:
        """Generate mock notifications for testing"""
        now = datetime.utcnow()
        
        return [
            {
                "id": 1,
                "title": "New email from boss",
                "content": "Please review the quarterly report",
                "sender": "boss@company.com",
                "recipient": "user@company.com",
                "platform": "email",
                "notification_type": NotificationType.MESSAGE,
                "priority": NotificationPriority.HIGH,
                "status": NotificationStatus.UNREAD,
                "metadata": {"email_id": "12345"},
                "created_at": now - timedelta(minutes=30),
                "read_at": None,
                "updated_at": now - timedelta(minutes=30)
            },
            {
                "id": 2,
                "title": "Slack mention in #general",
                "content": "@user can you join the meeting?",
                "sender": "colleague",
                "recipient": "user",
                "platform": "slack",
                "notification_type": NotificationType.MENTION,
                "priority": NotificationPriority.MEDIUM,
                "status": NotificationStatus.UNREAD,
                "metadata": {"channel": "general", "message_id": "67890"},
                "created_at": now - timedelta(hours=1),
                "read_at": None,
                "updated_at": now - timedelta(hours=1)
            },
            {
                "id": 3,
                "title": "Teams message in Project Alpha",
                "content": "Project deadline moved to next week",
                "sender": "project_manager",
                "recipient": "team",
                "platform": "teams",
                "notification_type": NotificationType.MESSAGE,
                "priority": NotificationPriority.MEDIUM,
                "status": NotificationStatus.READ,
                "metadata": {"team": "Project Alpha", "channel": "updates"},
                "created_at": now - timedelta(hours=2),
                "read_at": now - timedelta(hours=1),
                "updated_at": now - timedelta(hours=1)
            },
            {
                "id": 4,
                "title": "System alert: High CPU usage",
                "content": "Server CPU usage is at 95%",
                "sender": "monitoring_system",
                "recipient": "admin",
                "platform": "webhook",
                "notification_type": NotificationType.ALERT,
                "priority": NotificationPriority.URGENT,
                "status": NotificationStatus.UNREAD,
                "metadata": {"server": "prod-01", "metric": "cpu_usage"},
                "created_at": now - timedelta(minutes=15),
                "read_at": None,
                "updated_at": now - timedelta(minutes=15)
            },
            {
                "id": 5,
                "title": "Task reminder: Code review",
                "content": "Please review PR #123 by end of day",
                "sender": "task_system",
                "recipient": "developer",
                "platform": "webhook",
                "notification_type": NotificationType.REMINDER,
                "priority": NotificationPriority.LOW,
                "status": NotificationStatus.UNREAD,
                "metadata": {"pr_id": "123", "repository": "main-app"},
                "created_at": now - timedelta(hours=3),
                "read_at": None,
                "updated_at": now - timedelta(hours=3)
            }
        ]
    
    def _apply_filters(
        self,
        notifications: List[Dict[str, Any]],
        platform: Optional[str] = None,
        priority: Optional[NotificationPriority] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[str] = None,
        sender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Apply basic filters to notifications"""
        filtered = notifications
        
        if platform:
            filtered = [n for n in filtered if n["platform"] == platform]
        
        if priority:
            filtered = [n for n in filtered if n["priority"] == priority]
        
        if status:
            filtered = [n for n in filtered if n["status"] == status]
        
        if notification_type:
            filtered = [n for n in filtered if n["notification_type"] == notification_type]
        
        if sender:
            filtered = [n for n in filtered if n["sender"] == sender]
        
        return filtered
    
    def _apply_advanced_filters(
        self,
        notifications: List[Dict[str, Any]],
        filter_criteria: NotificationFilter
    ) -> List[Dict[str, Any]]:
        """Apply advanced filtering criteria"""
        filtered = notifications
        
        # Keywords filter
        if filter_criteria.keywords:
            filtered = [n for n in filtered if any(
                keyword.lower() in n["title"].lower() or 
                keyword.lower() in (n["content"] or "").lower()
                for keyword in filter_criteria.keywords
            )]
        
        # Senders filter
        if filter_criteria.senders:
            filtered = [n for n in filtered if n["sender"] in filter_criteria.senders]
        
        # Channels filter (for platform-specific metadata)
        if filter_criteria.channels:
            filtered = [n for n in filtered if any(
                channel in str(n.get("metadata", {}).values())
                for channel in filter_criteria.channels
            )]
        
        # Exclude keywords filter
        if filter_criteria.exclude_keywords:
            filtered = [n for n in filtered if not any(
                keyword.lower() in n["title"].lower() or 
                keyword.lower() in (n["content"] or "").lower()
                for keyword in filter_criteria.exclude_keywords
            )]
        
        # Minimum priority filter
        if filter_criteria.min_priority:
            priority_order = {
                NotificationPriority.LOW: 1,
                NotificationPriority.MEDIUM: 2,
                NotificationPriority.HIGH: 3,
                NotificationPriority.URGENT: 4
            }
            min_priority_value = priority_order[filter_criteria.min_priority]
            filtered = [n for n in filtered if priority_order[n["priority"]] >= min_priority_value]
        
        return filtered
    
    def process_all_rules_sync(self) -> Dict[str, Any]:
        """Synchronous version of process_all_rules for scheduler"""
        try:
            # TODO: Implement actual rules processing
            # For now, return mock data
            return {
                "rules_processed": 5,
                "notifications_updated": 12,
                "actions_executed": 8,
                "processed_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to process rules: {e}")
            raise
    
    def cleanup_old_notifications_sync(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Synchronous version of cleanup_old_notifications for scheduler"""
        try:
            # TODO: Implement actual cleanup
            # For now, return mock data
            return {
                "notifications_cleaned": 25,
                "history_cleaned": 150,
                "cutoff_date": cutoff_date,
                "cleaned_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {e}")
            raise
    
    async def deliver_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver a notification through the appropriate channel"""
        try:
            # TODO: Implement actual notification delivery
            # For now, return mock data
            return {
                "notification_id": notification_data.get("id", "unknown"),
                "delivery_status": "delivered",
                "delivery_method": notification_data.get("platform", "unknown"),
                "delivered_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to deliver notification: {e}")
            raise 