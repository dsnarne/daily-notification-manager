"""
Notification rules API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import logging

from ...models.schemas import (
    NotificationRuleCreate, NotificationRuleUpdate, NotificationRule,
    RuleCondition, RuleAction,
    SuccessResponse, ErrorResponse
)
from ...services.rule_service import RuleService
from ...core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SuccessResponse)
async def create_rule(
    rule: NotificationRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification rule"""
    try:
        service = RuleService(db)
        result = await service.create_rule(rule)
        return SuccessResponse(
            message="Rule created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}"
        )

@router.get("/", response_model=List[NotificationRule])
async def list_rules(
    user_id: int = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """List notification rules, optionally filtered by user and status"""
    try:
        service = RuleService(db)
        rules = await service.list_rules(user_id=user_id, is_active=is_active)
        return rules
    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rules: {str(e)}"
        )

@router.get("/{rule_id}", response_model=NotificationRule)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific rule by ID"""
    try:
        service = RuleService(db)
        rule = await service.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule: {str(e)}"
        )

@router.put("/{rule_id}", response_model=SuccessResponse)
async def update_rule(
    rule_id: int,
    rule: NotificationRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing rule"""
    try:
        service = RuleService(db)
        result = await service.update_rule(rule_id, rule)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        return SuccessResponse(
            message="Rule updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}"
        )

@router.delete("/{rule_id}", response_model=SuccessResponse)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Delete a rule"""
    try:
        service = RuleService(db)
        result = await service.delete_rule(rule_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        return SuccessResponse(
            message="Rule deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}"
        )

@router.post("/{rule_id}/activate", response_model=SuccessResponse)
async def activate_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Activate a rule"""
    try:
        service = RuleService(db)
        result = await service.activate_rule(rule_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        return SuccessResponse(
            message="Rule activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate rule: {str(e)}"
        )

@router.post("/{rule_id}/deactivate", response_model=SuccessResponse)
async def deactivate_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a rule"""
    try:
        service = RuleService(db)
        result = await service.deactivate_rule(rule_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        return SuccessResponse(
            message="Rule deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate rule: {str(e)}"
        )

@router.post("/{rule_id}/test", response_model=SuccessResponse)
async def test_rule(
    rule_id: int,
    test_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Test a rule with sample data"""
    try:
        service = RuleService(db)
        result = await service.test_rule(rule_id, test_data)
        return SuccessResponse(
            message="Rule test completed",
            data=result
        )
    except Exception as e:
        logger.error(f"Rule test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule test failed: {str(e)}"
        )

@router.post("/bulk-apply", response_model=SuccessResponse)
async def bulk_apply_rules(
    notification_ids: List[int],
    db: Session = Depends(get_db)
):
    """Apply all active rules to a list of notifications"""
    try:
        service = RuleService(db)
        result = await service.bulk_apply_rules(notification_ids)
        return SuccessResponse(
            message=f"Applied rules to {len(result)} notifications",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to bulk apply rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk apply rules: {str(e)}"
        ) 