"""
Preferences API: allow users to configure notification priorities and filters.
This uses an in-memory store for now.
"""

from fastapi import APIRouter, HTTPException
from typing import Any, Dict
import logging

from ...models.schemas import (
    NotificationPreference, NotificationPreferenceUpdate, PriorityLevel,
    QuietHours, NotificationFilter, PlatformType
)
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


# Simple in-memory preferences store (single-user demo)
PREF_STATE: Dict[str, Any] = {
    "platform": PlatformType.EMAIL,  # not used heavily in demo
    "priority_levels": PriorityLevel().model_dump(),
    "quiet_hours": QuietHours().model_dump(),
    "filters": NotificationFilter().model_dump(),
    "updated_at": datetime.utcnow().isoformat(),
}


@router.get("/")
async def get_preferences() -> Dict[str, Any]:
    return PREF_STATE


@router.put("/")
async def update_preferences(prefs: NotificationPreferenceUpdate) -> Dict[str, Any]:
    try:
        if prefs.priority_levels is not None:
            PREF_STATE["priority_levels"] = prefs.priority_levels.model_dump()
        if prefs.quiet_hours is not None:
            PREF_STATE["quiet_hours"] = prefs.quiet_hours.model_dump()
        if prefs.filters is not None:
            PREF_STATE["filters"] = prefs.filters.model_dump()
        PREF_STATE["updated_at"] = datetime.utcnow().isoformat()
        return PREF_STATE
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=400, detail=str(e))


