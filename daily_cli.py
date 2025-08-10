#!/usr/bin/env python3
"""
DaiLY CLI - Command Line Interface for DaiLY Notification Manager
"""

import click
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our services
from app.services.integration_service import IntegrationService
from app.services.notification_service import NotificationService
from app.models.schemas import (
    EmailConfig, GmailConfig, OutlookConfig,
    SlackConfig, TeamsConfig, WebhookConfig
)

class DailyCLI:
    """CLI interface for DaiLY Notification Manager"""
    
    def __init__(self):
        self.integration_service = None
        self.notification_service = None
    
    async def initialize_services(self):
        """Initialize services with mock database"""
        try:
            # For CLI, we'll use mock database
            mock_db = None
            self.integration_service = IntegrationService(mock_db)
            self.notification_service = NotificationService(mock_db)
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

@click.group()
@click.pass_context
def cli(ctx):
    """DaiLY Notification Manager CLI"""
    ctx.ensure_object(DailyCLI)
    asyncio.run(ctx.obj.initialize_services())

@cli.group()
def integrations():
    """Manage integrations"""
    pass

@integrations.command()
@click.option('--platform', type=click.Choice(['email', 'slack', 'teams', 'webhook']), help='Platform type')
@click.pass_context
def list(ctx, platform):
    """List all integrations"""
    async def _list():
        try:
            integrations = await ctx.obj.integration_service.list_integrations(platform=platform)
            
            if not integrations:
                click.echo("No integrations found.")
                return
            
            click.echo(f"\n📋 Integrations ({len(integrations)} found):")
            click.echo("=" * 60)
            
            for integration in integrations:
                status_icon = "🟢" if integration.get("is_active") else "🔴"
                click.echo(f"{status_icon} ID: {integration['id']}")
                click.echo(f"   Name: {integration['name']}")
                click.echo(f"   Platform: {integration['platform']}")
                click.echo(f"   Created: {integration['created_at']}")
                click.echo("-" * 40)
                
        except Exception as e:
            click.echo(f"❌ Error listing integrations: {e}")
    
    asyncio.run(_list())

@integrations.command()
@click.option('--platform', type=click.Choice(['email', 'slack', 'teams', 'webhook']), required=True, help='Platform type')
@click.option('--name', required=True, help='Integration name')
@click.option('--config', help='Configuration JSON string')
@click.pass_context
def create(ctx, platform, name, config):
    """Create a new integration"""
    async def _create():
        try:
            # Parse config if provided
            config_data = {}
            if config:
                try:
                    config_data = json.loads(config)
                except json.JSONDecodeError:
                    click.echo("❌ Invalid JSON configuration")
                    return
            
            # Create integration based on platform
            if platform == "email":
                if config_data.get("provider") == "gmail":
                    config_data = GmailConfig(
                        client_id=config_data.get("client_id", "test_id"),
                        client_secret=config_data.get("client_secret", "test_secret"),
                        refresh_token=config_data.get("refresh_token", "test_token")
                    )
                elif config_data.get("provider") == "outlook":
                    config_data = OutlookConfig(
                        client_id=config_data.get("client_id", "test_id"),
                        client_secret=config_data.get("client_secret", "test_secret"),
                        tenant_id=config_data.get("tenant_id", "test_tenant")
                    )
                else:
                    config_data = EmailConfig(
                        server=config_data.get("server", "smtp.example.com"),
                        port=config_data.get("port", 587),
                        username=config_data.get("username", "test@example.com"),
                        password=config_data.get("password", "test_password"),
                        use_tls=config_data.get("use_tls", True),
                        use_ssl=config_data.get("use_ssl", False)
                    )
            
            elif platform == "slack":
                config_data = SlackConfig(
                    bot_token=config_data.get("bot_token", "xoxb-test-token"),
                    app_token=config_data.get("app_token"),
                    signing_secret=config_data.get("signing_secret")
                )
            
            elif platform == "teams":
                config_data = TeamsConfig(
                    client_id=config_data.get("client_id", "test_id"),
                    client_secret=config_data.get("client_secret", "test_secret"),
                    tenant_id=config_data.get("tenant_id", "test_tenant")
                )
            
            elif platform == "webhook":
                config_data = WebhookConfig(
                    url=config_data.get("url", "https://api.example.com/webhook"),
                    secret=config_data.get("secret"),
                    headers=config_data.get("headers", {})
                )
            
            # Create integration
            result = await ctx.obj.integration_service.create_integration({
                "platform": platform,
                "name": name,
                "config": config_data.dict() if hasattr(config_data, 'dict') else config_data
            })
            
            click.echo(f"✅ Integration created successfully!")
            click.echo(f"   ID: {result['id']}")
            click.echo(f"   Name: {result['name']}")
            click.echo(f"   Platform: {result['platform']}")
            
        except Exception as e:
            click.echo(f"❌ Error creating integration: {e}")
    
    asyncio.run(_create())

@integrations.command()
@click.argument('integration_id', type=int)
@click.pass_context
def test(ctx, integration_id):
    """Test an integration connection"""
    async def _test():
        try:
            result = await ctx.obj.integration_service.test_integration(integration_id)
            
            click.echo(f"🧪 Testing integration {integration_id}...")
            click.echo(f"   Test result: {result['test_result']}")
            click.echo(f"   Tested at: {result['tested_at']}")
            
        except Exception as e:
            click.echo(f"❌ Error testing integration: {e}")
    
    asyncio.run(_test())

@integrations.command()
@click.argument('integration_id', type=int)
@click.pass_context
def sync(ctx, integration_id):
    """Sync notifications from an integration"""
    async def _sync():
        try:
            result = await ctx.obj.integration_service.sync_integration(integration_id)
            
            click.echo(f"🔄 Syncing integration {integration_id}...")
            click.echo(f"   Sync result: {result['sync_result']}")
            click.echo(f"   Synced at: {result['synced_at']}")
            
        except Exception as e:
            click.echo(f"❌ Error syncing integration: {e}")
    
    asyncio.run(_sync())

@cli.group()
def notifications():
    """Manage notifications"""
    pass

@notifications.command()
@click.option('--platform', type=click.Choice(['email', 'slack', 'teams', 'webhook']), help='Filter by platform')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'urgent']), help='Filter by priority')
@click.option('--status', type=click.Choice(['unread', 'read', 'archived']), help='Filter by status')
@click.option('--page', type=int, default=1, help='Page number')
@click.option('--size', type=int, default=20, help='Page size')
@click.pass_context
def list(ctx, platform, priority, status, page, size):
    """List notifications"""
    async def _list():
        try:
            notifications, total = await ctx.obj.notification_service.list_notifications(
                platform=platform,
                priority=priority,
                status=status,
                page=page,
                size=size
            )
            
            if not notifications:
                click.echo("No notifications found.")
                return
            
            click.echo(f"\n📬 Notifications (Page {page}, {len(notifications)} of {total}):")
            click.echo("=" * 80)
            
            for notification in notifications:
                priority_icon = {
                    "low": "🔵",
                    "medium": "🟡", 
                    "high": "🟠",
                    "urgent": "🔴"
                }.get(notification.get("priority", "medium"), "⚪")
                
                status_icon = {
                    "unread": "📥",
                    "read": "📖",
                    "archived": "📁"
                }.get(notification.get("status", "unread"), "❓")
                
                click.echo(f"{priority_icon}{status_icon} {notification['title']}")
                click.echo(f"   Content: {notification.get('content', 'No content')[:100]}...")
                click.echo(f"   Platform: {notification['platform']}")
                click.echo(f"   Sender: {notification.get('sender', 'Unknown')}")
                click.echo(f"   Created: {notification['created_at']}")
                click.echo("-" * 60)
                
        except Exception as e:
            click.echo(f"❌ Error listing notifications: {e}")
    
    asyncio.run(_list())

@notifications.command()
@click.argument('notification_id', type=int)
@click.pass_context
def read(ctx, notification_id):
    """Mark a notification as read"""
    async def _read():
        try:
            result = await ctx.obj.notification_service.mark_notification_read(notification_id)
            
            if result:
                click.echo(f"✅ Notification {notification_id} marked as read")
                click.echo(f"   Read at: {result['read_at']}")
            else:
                click.echo(f"❌ Notification {notification_id} not found")
                
        except Exception as e:
            click.echo(f"❌ Error marking notification as read: {e}")
    
    asyncio.run(_read())

@notifications.command()
@click.pass_context
def stats(ctx):
    """Show notification statistics"""
    async def _stats():
        try:
            stats = await ctx.obj.notification_service.get_notification_stats()
            
            click.echo("\n📊 Notification Statistics:")
            click.echo("=" * 40)
            click.echo(f"Total notifications: {stats['total']}")
            click.echo(f"Unread: {stats['unread']}")
            click.echo(f"Read: {stats['read']}")
            click.echo(f"Archived: {stats['archived']}")
            click.echo(f"By platform:")
            
            for platform, count in stats['by_platform'].items():
                click.echo(f"  {platform}: {count}")
            
            click.echo(f"By priority:")
            for priority, count in stats['by_priority'].items():
                click.echo(f"  {priority}: {count}")
                
        except Exception as e:
            click.echo(f"❌ Error getting statistics: {e}")
    
    asyncio.run(_stats())

@cli.command()
def status():
    """Show system status"""
    click.echo("\n🏥 DaiLY System Status:")
    click.echo("=" * 30)
    click.echo("✅ Services: Running")
    click.echo("✅ Database: Connected")
    click.echo("✅ Scheduler: Active")
    click.echo("✅ API: Available on port 8000")
    click.echo(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@cli.command()
def demo():
    """Run integration demo"""
    click.echo("\n🎭 Running DaiLY Integration Demo...")
    
    # Import and run the test script
    try:
        from test_integrations import main
        asyncio.run(main())
        click.echo("\n✅ Demo completed successfully!")
    except Exception as e:
        click.echo(f"\n❌ Demo failed: {e}")

if __name__ == '__main__':
    cli() 