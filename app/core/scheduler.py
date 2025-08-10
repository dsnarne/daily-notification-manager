"""
Notification scheduler for DaiLY Notification Manager
Handles periodic checking of all integrations and notification delivery
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import schedule
import time
from concurrent.futures import ThreadPoolExecutor

from ..services.integration_service import IntegrationService
from ..services.notification_service import NotificationService
from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Scheduler for managing notification checks and delivery"""
    
    def __init__(self):
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.scheduled_tasks = {}
        self.check_interval = settings.NOTIFICATION_CHECK_INTERVAL
        
    async def start(self):
        """Start the notification scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        logger.info("Starting notification scheduler")
        
        # Schedule periodic tasks
        self._schedule_periodic_tasks()
        
        # Start the scheduler loop
        asyncio.create_task(self._scheduler_loop())
        
    async def stop(self):
        """Stop the notification scheduler"""
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping notification scheduler")
        
        # Cancel all scheduled tasks
        for task in self.scheduled_tasks.values():
            if not task.done():
                task.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
    def _schedule_periodic_tasks(self):
        """Schedule periodic notification checks"""
        # Check notifications every minute
        schedule.every(1).minutes.do(self._check_all_integrations)
        
        # Process notification rules every 5 minutes
        schedule.every(5).minutes.do(self._process_notification_rules)
        
        # Clean up old notifications every hour
        schedule.every(1).hour.do(self._cleanup_old_notifications)
        
        logger.info("Scheduled periodic tasks")
        
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Run pending scheduled tasks
                schedule.run_pending()
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
    def _check_all_integrations(self):
        """Check all integrations for new notifications"""
        try:
            # Run in thread pool to avoid blocking
            future = self.executor.submit(self._check_integrations_sync)
            future.add_done_callback(self._on_integration_check_complete)
            
        except Exception as e:
            logger.error(f"Failed to schedule integration check: {e}")
            
    def _check_integrations_sync(self):
        """Synchronous integration check (runs in thread pool)"""
        try:
            # Get database session
            db = next(get_db())
            
            # Get integration service
            integration_service = IntegrationService(db)
            
            # Get all active integrations
            integrations = integration_service.list_integrations_sync()
            
            for integration in integrations:
                try:
                    # Sync notifications for this integration
                    result = integration_service.sync_integration_sync(integration["id"])
                    logger.info(f"Synced integration {integration['name']}: {result}")
                    
                except Exception as e:
                    logger.error(f"Failed to sync integration {integration['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in integration check: {e}")
            
    def _on_integration_check_complete(self, future):
        """Callback when integration check completes"""
        try:
            result = future.result()
            logger.debug("Integration check completed successfully")
        except Exception as e:
            logger.error(f"Integration check failed: {e}")
            
    def _process_notification_rules(self):
        """Process notification rules for filtering and actions"""
        try:
            # Run in thread pool
            future = self.executor.submit(self._process_rules_sync)
            future.add_done_callback(self._on_rules_processing_complete)
            
        except Exception as e:
            logger.error(f"Failed to schedule rules processing: {e}")
            
    def _process_rules_sync(self):
        """Synchronous rules processing (runs in thread pool)"""
        try:
            # Get database session
            db = next(get_db())
            
            # Get notification service
            notification_service = NotificationService(db)
            
            # Process rules for all users
            result = notification_service.process_all_rules_sync()
            logger.info(f"Processed notification rules: {result}")
            
        except Exception as e:
            logger.error(f"Error in rules processing: {e}")
            
    def _on_rules_processing_complete(self, future):
        """Callback when rules processing completes"""
        try:
            result = future.result()
            logger.debug("Rules processing completed successfully")
        except Exception as e:
            logger.error(f"Rules processing failed: {e}")
            
    def _cleanup_old_notifications(self):
        """Clean up old notifications and history"""
        try:
            # Run in thread pool
            future = self.executor.submit(self._cleanup_sync)
            future.add_done_callback(self._on_cleanup_complete)
            
        except Exception as e:
            logger.error(f"Failed to schedule cleanup: {e}")
            
    def _cleanup_sync(self):
        """Synchronous cleanup (runs in thread pool)"""
        try:
            # Get database session
            db = next(get_db())
            
            # Get notification service
            notification_service = NotificationService(db)
            
            # Clean up old notifications (older than 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = notification_service.cleanup_old_notifications_sync(cutoff_date)
            logger.info(f"Cleanup completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            
    def _on_cleanup_complete(self, future):
        """Callback when cleanup completes"""
        try:
            result = future.result()
            logger.debug("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            
    async def schedule_notification(self, notification_data: Dict[str, Any], delay_seconds: int = 0):
        """Schedule a notification for delivery"""
        try:
            if delay_seconds > 0:
                # Schedule for later delivery
                await asyncio.sleep(delay_seconds)
                
            # Deliver notification immediately or after delay
            await self._deliver_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            
    async def _deliver_notification(self, notification_data: Dict[str, Any]):
        """Deliver a notification through the appropriate channel"""
        try:
            # Get database session
            db = next(get_db())
            
            # Get notification service
            notification_service = NotificationService(db)
            
            # Deliver the notification
            result = await notification_service.deliver_notification(notification_data)
            logger.info(f"Notification delivered: {result}")
            
        except Exception as e:
            logger.error(f"Failed to deliver notification: {e}")
            
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "scheduled_tasks": len(self.scheduled_tasks),
            "executor_workers": self.executor._max_workers,
            "last_check": getattr(self, '_last_check', None)
        } 