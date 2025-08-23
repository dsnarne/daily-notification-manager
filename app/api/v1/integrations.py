"""
Integration management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import logging

from ...models.schemas import (
    IntegrationCreate, IntegrationUpdate, Integration,
    EmailConfig, GmailConfig, OutlookConfig,
    SlackConfig, TeamsConfig, WebhookConfig,
    SuccessResponse, ErrorResponse
)
from ...services.integration_service import IntegrationService
from ...core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SuccessResponse)
async def create_integration(
    integration: IntegrationCreate,
    db: Session = Depends(get_db)
):
    """Create a new integration"""
    try:
        service = IntegrationService(db)
        result = await service.create_integration(integration)
        return SuccessResponse(
            message="Integration created successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to create integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def list_integrations(
    platform: str = None,
    db: Session = Depends(get_db)
):
    """List all integrations, optionally filtered by platform"""
    try:
        service = IntegrationService(db)
        integrations = await service.list_integrations(platform=platform)
        return integrations
    except Exception as e:
        logger.error(f"Failed to list integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}"
        )

@router.get("/{integration_id}", response_model=Integration)
async def get_integration(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific integration by ID"""
    try:
        service = IntegrationService(db)
        integration = await service.get_integration(integration_id)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration: {str(e)}"
        )

@router.put("/{integration_id}", response_model=SuccessResponse)
async def update_integration(
    integration_id: int,
    integration: IntegrationUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing integration"""
    try:
        service = IntegrationService(db)
        result = await service.update_integration(integration_id, integration)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        return SuccessResponse(
            message="Integration updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update integration: {str(e)}"
        )

@router.delete("/{integration_id}", response_model=SuccessResponse)
async def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Delete an integration"""
    try:
        service = IntegrationService(db)
        result = await service.delete_integration(integration_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        return SuccessResponse(
            message="Integration deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete integration: {str(e)}"
        )

@router.post("/{integration_id}/test", response_model=SuccessResponse)
async def test_integration(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Test an integration connection"""
    try:
        service = IntegrationService(db)
        result = await service.test_integration(integration_id)
        return SuccessResponse(
            message="Integration test successful",
            data=result
        )
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration test failed: {str(e)}"
        )

@router.post("/{integration_id}/sync", response_model=SuccessResponse)
async def sync_integration(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Manually sync notifications from an integration"""
    try:
        service = IntegrationService(db)
        result = await service.sync_integration(integration_id)
        return SuccessResponse(
            message="Integration sync completed",
            data=result
        )
    except Exception as e:
        logger.error(f"Integration sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration sync failed: {str(e)}"
        ) 