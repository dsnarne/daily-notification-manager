#!/usr/bin/env python3
"""
DaiLY Notification Manager - FastAPI Server
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import subprocess

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

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard"""
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
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Dashboard API endpoints
@app.get("/api/integrations")
async def get_integrations():
    """Get all integrations"""
    try:
        # Return mock data for now
        return [
            {
                "id": "1",
                "name": "Gmail Integration",
                "type": "email",
                "status": "online",
                "last_checked": "2024-01-01T00:00:00Z"
            },
            {
                "id": "2",
                "name": "Slack Workspace",
                "type": "slack",
                "status": "offline",
                "last_checked": "2024-01-01T00:00:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return []

@app.get("/api/notifications")
async def get_notifications():
    """Get all notifications"""
    try:
        # Mock data for now - replace with actual service call
        notifications = [
            {
                "id": "1",
                "title": "Welcome to DaiLY",
                "content": "Your notification manager is ready!",
                "platform": "system",
                "priority": "medium",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "2",
                "title": "Email from Boss",
                "content": "Please review the quarterly report",
                "platform": "email",
                "priority": "high",
                "created_at": "2024-01-01T10:00:00Z"
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
        # Mock data for now - replace with actual service call
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