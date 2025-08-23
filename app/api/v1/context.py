"""
API endpoints for user context management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db, UserContext as UserContextModel
from app.models.schemas import (
    UserContext, 
    UserContextCreate, 
    UserContextUpdate,
    SuccessResponse,
    ErrorResponse
)

router = APIRouter(tags=["User Context"])

@router.post("/", response_model=UserContext)
async def create_user_context(
    context_data: UserContextCreate,
    db: Session = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """Create or update user's working context"""
    # Deactivate existing active contexts
    db.query(UserContextModel).filter(
        UserContextModel.user_id == user_id,
        UserContextModel.is_active == True
    ).update({"is_active": False})
    
    # Create new context
    db_context = UserContextModel(
        user_id=user_id,
        context_description=context_data.context_description,
        expires_at=context_data.expires_at,
        is_active=True
    )
    
    db.add(db_context)
    db.commit()
    db.refresh(db_context)
    
    return db_context

@router.get("/current", response_model=Optional[UserContext])
async def get_current_context(
    db: Session = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """Get user's current active context"""
    context = db.query(UserContextModel).filter(
        UserContextModel.user_id == user_id,
        UserContextModel.is_active == True
    ).first()
    
    return context

@router.put("/{context_id}", response_model=UserContext)
async def update_context(
    context_id: int,
    context_data: UserContextUpdate,
    db: Session = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """Update existing context"""
    context = db.query(UserContextModel).filter(
        UserContextModel.id == context_id,
        UserContextModel.user_id == user_id
    ).first()
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context not found"
        )
    
    update_data = context_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(context, field, value)
    
    db.commit()
    db.refresh(context)
    
    return context

@router.delete("/current", response_model=SuccessResponse)
async def deactivate_current_context(
    db: Session = Depends(get_db),
    user_id: int = 1  # TODO: Get from auth
):
    """Deactivate current context (clear working context)"""
    updated = db.query(UserContextModel).filter(
        UserContextModel.user_id == user_id,
        UserContextModel.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    return SuccessResponse(
        message=f"Deactivated {updated} active context(s)"
    )

@router.get("/", response_model=List[UserContext])
async def list_contexts(
    db: Session = Depends(get_db),
    user_id: int = 1,  # TODO: Get from auth
    limit: int = 10
):
    """List user's recent contexts"""
    contexts = db.query(UserContextModel).filter(
        UserContextModel.user_id == user_id
    ).order_by(UserContextModel.created_at.desc()).limit(limit).all()
    
    return contexts