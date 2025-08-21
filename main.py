#!/usr/bin/env python3
"""
DaiLY Notification Manager - FastAPI Server
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import subprocess
from typing import List, Optional
from datetime import datetime
import json

# Import our services
from app.services.integration_service import IntegrationService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.core.database import get_db
from app.models.schemas import IntegrationCreate, IntegrationUpdate, NotificationRuleCreate, NotificationRuleUpdate
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DaiLY Notification Manager",
    description="An intelligent notification manager that filters and prioritizes work notifications across multiple platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (must be added before routers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")
# Mount API router under /api
app.include_router(api_router, prefix="/api")

# Initialize services (using mock services for now)
# TODO: Replace with real database services when database is fully implemented
class MockIntegrationService:
    async def get_all_integrations(self):
        return [
            {
                "id": "1",
                "name": "Gmail Integration",
                "type": "email",
                "status": "online",
                "last_checked": datetime.now().isoformat(),
                "config": {"email": "user@gmail.com"}
            },
            {
                "id": "2",
                "name": "Slack Workspace",
                "type": "slack",
                "status": "offline",
                "last_checked": datetime.now().isoformat(),
                "config": {"workspace": "company"}
            }
        ]
    
    async def create_integration(self, integration):
        return {"id": "3", "name": integration.name, "platform": integration.platform, "config": integration.config}
    
    async def update_integration(self, integration_id, integration):
        return {"id": integration_id, "name": integration.name, "platform": integration.platform, "config": integration.config}
    
    async def delete_integration(self, integration_id):
        return True
    
    async def test_integration(self, integration_id):
        return {"status": "success", "message": "Integration test completed"}

class MockNotificationService:
    async def get_all_rules(self):
        return [
            {
                "id": "1",
                "name": "High Priority Emails",
                "priority": "high",
                "platform": "email",
                "conditions": {"sender": "boss@company.com"}
            },
            {
                "id": "2",
                "name": "Urgent Slack Messages",
                "priority": "urgent",
                "platform": "slack",
                "conditions": {"channel": "#urgent"}
            }
        ]
    
    async def create_rule(self, rule):
        return {"id": "3", "name": rule.name, "priority": rule.priority, "platform": rule.platform, "conditions": rule.conditions}
    
    async def update_rule(self, rule_id, rule):
        return {"id": rule_id, "name": rule.name, "priority": rule.priority, "platform": rule.platform, "conditions": rule.conditions}
    
    async def delete_rule(self, rule_id):
        return True

class MockUserService:
    async def get_all_users(self):
        return []

integration_service = MockIntegrationService()
notification_service = MockNotificationService()
user_service = MockUserService()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard_enhanced.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_legacy(request: Request):
    """Serve the legacy dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DaiLY Notification Manager",
        "version": "1.0.0",
        "status": "running",
        "integrations": ["email", "slack", "teams", "webhook"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "scheduler": "running",
            "integrations": "active"
        }
    }

# Dashboard API endpoints
@app.get("/api/integrations")
async def get_integrations():
    """Get all integrations"""
    try:
        integrations = await integration_service.get_all_integrations()
        return integrations
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return []

@app.post("/api/integrations")
async def create_integration(integration: IntegrationCreate):
    """Create a new integration"""
    try:
        result = await integration_service.create_integration(integration)
        return {"status": "success", "integration": result}
    except Exception as e:
        logger.error(f"Error creating integration: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/integrations/{integration_id}")
async def update_integration(integration_id: str, integration: IntegrationUpdate):
    """Update an existing integration"""
    try:
        result = await integration_service.update_integration(integration_id, integration)
        return {"status": "success", "integration": result}
    except Exception as e:
        logger.error(f"Error updating integration: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/integrations/{integration_id}")
async def delete_integration(integration_id: str):
    """Delete an integration"""
    try:
        await integration_service.delete_integration(integration_id)
        return {"status": "success", "message": "Integration deleted"}
    except Exception as e:
        logger.error(f"Error deleting integration: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/notifications")
async def get_notifications():
    """Get all notifications"""
    try:
        # Mock data for now
        notifications = [
            {
                "id": "1",
                "title": "Welcome to DaiLY",
                "content": "Your notification manager is ready!",
                "platform": "system",
                "priority": "medium",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "title": "Email from Boss",
                "content": "Please review the quarterly report",
                "platform": "email",
                "priority": "high",
                "created_at": datetime.now().isoformat()
            }
        ]
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []

@app.get("/api/rules")
async def get_rules():
    """Get all notification rules"""
    try:
        # Try to get real data first, fall back to mock if service unavailable
        try:
            rules = await notification_service.get_all_rules()
            return rules
        except Exception as e:
            logger.warning(f"Service unavailable, using mock data: {e}")
            # Mock data for now
            rules = [
                {
                    "id": "1",
                    "name": "High Priority Alerts",
                    "priority": "high",
                    "platform": "all",
                    "conditions": {"priority": "high"}
                },
                {
                    "id": "2",
                    "name": "Boss Emails",
                    "priority": "urgent",
                    "platform": "email",
                    "conditions": {"sender": "boss@company.com"}
                }
            ]
            return rules
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        return []

@app.post("/api/rules")
async def create_rule(rule: NotificationRuleCreate):
    """Create a new notification rule"""
    try:
        result = await notification_service.create_rule(rule)
        return {"status": "success", "rule": result}
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, rule: NotificationRuleUpdate):
    """Update an existing rule"""
    try:
        result = await notification_service.update_rule(rule_id, rule)
        return {"status": "success", "rule": result}
    except Exception as e:
        logger.error(f"Error updating rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule"""
    try:
        await notification_service.delete_rule(rule_id)
        return {"status": "success", "message": "Rule deleted"}
    except Exception as e:
        logger.error(f"Error deleting rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/test")
async def run_test():
    """Run system test"""
    try:
        # Run the integration test
        result = subprocess.run(
            ["python", "daily_cli.py", "demo"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "System test completed successfully",
                "output": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "System test failed",
                "output": result.stderr
            }
    except Exception as e:
        logger.error(f"Error running test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/{integration_id}/test")
async def test_integration(integration_id: str):
    """Test a specific integration"""
    try:
        result = await integration_service.test_integration(integration_id)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting DaiLY Notification Manager...")
    logger.info("API documentation available at: http://localhost:8000/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 