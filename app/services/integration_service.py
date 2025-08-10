"""
Integration service for managing all platform integrations
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.schemas import (
    IntegrationCreate, IntegrationUpdate, Integration,
    EmailConfig, GmailConfig, OutlookConfig,
    SlackConfig, TeamsConfig, WebhookConfig
)
from ..integrations.email_integration import EmailIntegration, GmailIntegration, OutlookIntegration
from ..integrations.slack_integration import SlackIntegration
from ..integrations.teams_integration import TeamsIntegration
from ..integrations.webhook_integration import WebhookIntegration, WebhookManager

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for managing integrations across all platforms"""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_manager = WebhookManager()
    
    async def create_integration(self, integration: IntegrationCreate) -> Dict[str, Any]:
        """Create a new integration"""
        try:
            # Validate configuration based on platform
            if integration.platform == "email":
                await self._validate_email_config(integration.config)
            elif integration.platform == "slack":
                await self._validate_slack_config(integration.config)
            elif integration.platform == "teams":
                await self._validate_teams_config(integration.config)
            elif integration.platform == "webhook":
                await self._validate_webhook_config(integration.config)
            
            # Test the integration connection
            test_result = await self._test_integration_connection(integration.platform, integration.config)
            if not test_result["success"]:
                raise ValueError(f"Integration test failed: {test_result['error']}")
            
            # TODO: Save to database
            # For now, return mock data
            return {
                "id": 1,
                "platform": integration.platform,
                "name": integration.name,
                "config": integration.config,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"Failed to create integration: {e}")
            raise
    
    async def list_integrations(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all integrations, optionally filtered by platform"""
        try:
            # TODO: Query database
            # For now, return mock data
            mock_integrations = [
                {
                    "id": 1,
                    "platform": "email",
                    "name": "Gmail Integration",
                    "config": {"provider": "gmail"},
                    "is_active": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "id": 2,
                    "platform": "slack",
                    "name": "Slack Workspace",
                    "config": {"workspace": "my-workspace"},
                    "is_active": True,
                    "created_at": datetime.utcnow()
                }
            ]
            
            if platform:
                mock_integrations = [i for i in mock_integrations if i["platform"] == platform]
            
            return mock_integrations
            
        except Exception as e:
            logger.error(f"Failed to list integrations: {e}")
            raise
    
    def list_integrations_sync(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Synchronous version of list_integrations"""
        try:
            # TODO: Query database
            # For now, return mock data
            mock_integrations = [
                {
                    "id": 1,
                    "platform": "email",
                    "name": "Gmail Integration",
                    "config": {"provider": "gmail"},
                    "is_active": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "id": 2,
                    "platform": "slack",
                    "name": "Slack Workspace",
                    "config": {"workspace": "my-workspace"},
                    "is_active": True,
                    "created_at": datetime.utcnow()
                }
            ]
            
            if platform:
                mock_integrations = [i for i in mock_integrations if i["platform"] == platform]
            
            return mock_integrations
            
        except Exception as e:
            logger.error(f"Failed to list integrations: {e}")
            raise
    
    async def get_integration(self, integration_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific integration by ID"""
        try:
            # TODO: Query database
            # For now, return mock data
            return {
                "id": integration_id,
                "platform": "email",
                "name": "Gmail Integration",
                "config": {"provider": "gmail"},
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get integration: {e}")
            raise
    
    def get_integration_sync(self, integration_id: int) -> Optional[Dict[str, Any]]:
        """Synchronous version of get_integration"""
        try:
            # TODO: Query database
            # For now, return mock data
            return {
                "id": integration_id,
                "platform": "email",
                "name": "Gmail Integration",
                "config": {"provider": "gmail"},
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get integration: {e}")
            raise
    
    async def update_integration(self, integration_id: int, integration: IntegrationUpdate) -> Optional[Dict[str, Any]]:
        """Update an existing integration"""
        try:
            # TODO: Update database
            # For now, return mock data
            return {
                "id": integration_id,
                "platform": "email",
                "name": integration.name or "Gmail Integration",
                "config": integration.config or {"provider": "gmail"},
                "is_active": True,
                "updated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to update integration: {e}")
            raise
    
    async def delete_integration(self, integration_id: int) -> bool:
        """Delete an integration"""
        try:
            # TODO: Delete from database
            # For now, return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete integration: {e}")
            raise
    
    async def test_integration(self, integration_id: int) -> Dict[str, Any]:
        """Test an integration connection"""
        try:
            integration = await self.get_integration(integration_id)
            if not integration:
                raise ValueError("Integration not found")
            
            test_result = await self._test_integration_connection(
                integration["platform"], 
                integration["config"]
            )
            
            return {
                "integration_id": integration_id,
                "test_result": test_result,
                "tested_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to test integration: {e}")
            raise
    
    async def sync_integration(self, integration_id: int) -> Dict[str, Any]:
        """Manually sync notifications from an integration"""
        try:
            integration = await self.get_integration(integration_id)
            if not integration:
                raise ValueError("Integration not found")
            
            # Get the appropriate integration instance
            integration_instance = await self._get_integration_instance(
                integration["platform"], 
                integration["config"]
            )
            
            # Sync notifications
            sync_result = await self._sync_notifications(integration_instance, integration["platform"])
            
            return {
                "integration_id": integration_id,
                "sync_result": sync_result,
                "synced_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync integration: {e}")
            raise
    
    def sync_integration_sync(self, integration_id: int) -> Dict[str, Any]:
        """Synchronous version of sync_integration"""
        try:
            integration = self.get_integration_sync(integration_id)
            if not integration:
                raise ValueError("Integration not found")
            
            # Get the appropriate integration instance
            integration_instance = self._get_integration_instance_sync(
                integration["platform"], 
                integration["config"]
            )
            
            # Sync notifications
            sync_result = self._sync_notifications_sync(integration_instance, integration["platform"])
            
            return {
                "integration_id": integration_id,
                "sync_result": sync_result,
                "synced_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync integration: {e}")
            raise
    
    async def _validate_email_config(self, config: Dict[str, Any]) -> bool:
        """Validate email configuration"""
        try:
            if "provider" in config:
                if config["provider"] == "gmail":
                    required_fields = ["client_id", "client_secret", "refresh_token"]
                elif config["provider"] == "outlook":
                    required_fields = ["client_id", "client_secret", "tenant_id"]
                else:
                    required_fields = ["server", "port", "username", "password"]
                
                for field in required_fields:
                    if field not in config:
                        raise ValueError(f"Missing required field: {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"Email config validation failed: {e}")
            raise
    
    async def _validate_slack_config(self, config: Dict[str, Any]) -> bool:
        """Validate Slack configuration"""
        try:
            required_fields = ["bot_token"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"Slack config validation failed: {e}")
            raise
    
    async def _validate_teams_config(self, config: Dict[str, Any]) -> bool:
        """Validate Teams configuration"""
        try:
            required_fields = ["client_id", "client_secret", "tenant_id"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"Teams config validation failed: {e}")
            raise
    
    async def _validate_webhook_config(self, config: Dict[str, Any]) -> bool:
        """Validate webhook configuration"""
        try:
            required_fields = ["url"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook config validation failed: {e}")
            raise
    
    async def _test_integration_connection(self, platform: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test integration connection"""
        try:
            integration_instance = await self._get_integration_instance(platform, config)
            
            if platform == "email":
                if isinstance(integration_instance, (GmailIntegration, OutlookIntegration)):
                    success = integration_instance.authenticate()
                else:
                    success = integration_instance.connect()
                    
            elif platform == "slack":
                success = True  # Slack client initialization is usually successful
                
            elif platform == "teams":
                success = integration_instance.authenticate()
                
            elif platform == "webhook":
                success = True  # Webhook validation is done during config validation
                
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            return {
                "success": success,
                "platform": platform,
                "tested_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Integration connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform,
                "tested_at": datetime.utcnow()
            }
    
    async def _get_integration_instance(self, platform: str, config: Dict[str, Any]):
        """Get integration instance based on platform and config"""
        try:
            if platform == "email":
                if config.get("provider") == "gmail":
                    return GmailIntegration(GmailConfig(**config))
                elif config.get("provider") == "outlook":
                    return OutlookIntegration(OutlookConfig(**config))
                else:
                    return EmailIntegration(EmailConfig(**config))
                    
            elif platform == "slack":
                return SlackIntegration(SlackConfig(**config))
                
            elif platform == "teams":
                return TeamsIntegration(TeamsConfig(**config))
                
            elif platform == "webhook":
                return WebhookIntegration(WebhookConfig(**config))
                
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            logger.error(f"Failed to create integration instance: {e}")
            raise
    
    async def _sync_notifications(self, integration_instance, platform: str) -> Dict[str, Any]:
        """Sync notifications from integration"""
        try:
            if platform == "email":
                # Fetch emails
                emails = integration_instance.fetch_emails(max_results=50)
                return {
                    "platform": platform,
                    "notifications_found": len(emails),
                    "details": emails[:5]  # Return first 5 for preview
                }
                
            elif platform == "slack":
                # Get channels and messages
                channels = integration_instance.get_channels()
                total_messages = 0
                for channel in channels[:3]:  # Check first 3 channels
                    messages = integration_instance.get_channel_messages(channel["id"], limit=20)
                    total_messages += len(messages)
                
                return {
                    "platform": platform,
                    "channels_checked": len(channels[:3]),
                    "notifications_found": total_messages
                }
                
            elif platform == "teams":
                # Get teams and channels
                teams = integration_instance.get_teams()
                total_messages = 0
                for team in teams[:2]:  # Check first 2 teams
                    channels = integration_instance.get_channels(team["id"])
                    for channel in channels[:2]:  # Check first 2 channels per team
                        messages = integration_instance.get_channel_messages(
                            team["id"], channel["id"], limit=20
                        )
                        total_messages += len(messages)
                
                return {
                    "platform": platform,
                    "teams_checked": len(teams[:2]),
                    "notifications_found": total_messages
                }
                
            elif platform == "webhook":
                # Webhooks are typically inbound, so just return status
                return {
                    "platform": platform,
                    "status": "webhook_endpoint_active",
                    "message": "Webhook endpoint is ready to receive notifications"
                }
                
            else:
                raise ValueError(f"Unsupported platform for sync: {platform}")
                
        except Exception as e:
            logger.error(f"Failed to sync notifications: {e}")
            raise
    
    def _get_integration_instance_sync(self, platform: str, config: Dict[str, Any]):
        """Synchronous version of _get_integration_instance"""
        try:
            if platform == "email":
                if config.get("provider") == "gmail":
                    return GmailIntegration(GmailConfig(**config))
                elif config.get("provider") == "outlook":
                    return OutlookIntegration(OutlookConfig(**config))
                else:
                    return EmailIntegration(EmailConfig(**config))
                    
            elif platform == "slack":
                return SlackIntegration(SlackConfig(**config))
                
            elif platform == "teams":
                return TeamsIntegration(TeamsConfig(**config))
                
            elif platform == "webhook":
                return WebhookIntegration(WebhookConfig(**config))
                
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            logger.error(f"Failed to create integration instance: {e}")
            raise
    
    def _sync_notifications_sync(self, integration_instance, platform: str) -> Dict[str, Any]:
        """Synchronous version of _sync_notifications"""
        try:
            if platform == "email":
                # Fetch emails
                emails = integration_instance.fetch_emails(max_results=50)
                return {
                    "platform": platform,
                    "notifications_found": len(emails),
                    "details": emails[:5]  # Return first 5 for preview
                }
                
            elif platform == "slack":
                # Get channels and messages
                channels = integration_instance.get_channels()
                total_messages = 0
                for channel in channels[:3]:  # Check first 3 channels
                    messages = integration_instance.get_channel_messages(channel["id"], limit=20)
                    total_messages += len(messages)
                
                return {
                    "platform": platform,
                    "channels_checked": len(channels[:3]),
                    "notifications_found": total_messages
                }
                
            elif platform == "teams":
                # Get teams and channels
                teams = integration_instance.get_teams()
                total_messages = 0
                for team in teams[:2]:  # Check first 2 teams
                    channels = integration_instance.get_channels(team["id"])
                    for channel in channels[:2]:  # Check first 2 channels per team
                        messages = integration_instance.get_channel_messages(
                            team["id"], channel["id"], limit=20
                        )
                        total_messages += len(messages)
                
                return {
                    "platform": platform,
                    "teams_checked": len(teams[:2]),
                    "notifications_found": total_messages
                }
                
            elif platform == "webhook":
                # Webhooks are typically inbound, so just return status
                return {
                    "platform": platform,
                    "status": "webhook_endpoint_active",
                    "message": "Webhook endpoint is ready to receive notifications"
                }
                
            else:
                raise ValueError(f"Unsupported platform for sync: {platform}")
                
        except Exception as e:
            logger.error(f"Failed to sync notifications: {e}")
            raise 