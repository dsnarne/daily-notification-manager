"""
Main API router for DaiLY Notification Manager
"""

from fastapi import APIRouter
from . import integrations, notifications, users, rules, preferences, assistant

api_router = APIRouter()

# Include all endpoint modules
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"]) 
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])

# Conditionally include MCP routes if the dependency is available
try:
    from . import mcp  # type: ignore
    api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])  # noqa: F401
except Exception:
    # MCP not available; skip exposing these routes
    pass