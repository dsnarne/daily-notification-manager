"""
User management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import logging

from ...models.schemas import (
    UserCreate, UserUpdate, User,
    NotificationPreferenceCreate, NotificationPreferenceUpdate, NotificationPreference,
    SuccessResponse, ErrorResponse
)
from ...services.user_service import UserService
from ...core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SuccessResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user account"""
    try:
        service = UserService(db)
        result = await service.create_user(user)
        return SuccessResponse(
            message="User created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/", response_model=List[User])
async def list_users(
    db: Session = Depends(get_db)
):
    """List all users"""
    try:
        service = UserService(db)
        users = await service.list_users()
        return users
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    try:
        service = UserService(db)
        user = await service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )

@router.put("/{user_id}", response_model=SuccessResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing user"""
    try:
        service = UserService(db)
        result = await service.update_user(user_id, user)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return SuccessResponse(
            message="User updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user account"""
    try:
        service = UserService(db)
        result = await service.delete_user(user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return SuccessResponse(
            message="User deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.post("/{user_id}/preferences", response_model=SuccessResponse)
async def create_user_preference(
    user_id: int,
    preference: NotificationPreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create notification preferences for a user"""
    try:
        service = UserService(db)
        result = await service.create_notification_preference(user_id, preference)
        return SuccessResponse(
            message="Notification preference created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to create notification preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification preference: {str(e)}"
        )

@router.get("/{user_id}/preferences", response_model=List[NotificationPreference])
async def get_user_preferences(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get notification preferences for a user"""
    try:
        service = UserService(db)
        preferences = await service.get_notification_preferences(user_id)
        return preferences
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification preferences: {str(e)}"
        )

@router.put("/{user_id}/preferences/{preference_id}", response_model=SuccessResponse)
async def update_user_preference(
    user_id: int,
    preference_id: int,
    preference: NotificationPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update notification preferences for a user"""
    try:
        service = UserService(db)
        result = await service.update_notification_preference(user_id, preference_id, preference)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification preference not found"
            )
        return SuccessResponse(
            message="Notification preference updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preference: {str(e)}"
        ) 