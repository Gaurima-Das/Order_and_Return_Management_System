from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models.return_model import ReturnStatus
from app.schemas.return_schema import (
    ReturnCreate,
    ReturnUpdate,
    ReturnResponse,
    ReturnStateUpdate,
)
from app.services.return_service import ReturnService

router = APIRouter()


@router.post("", response_model=ReturnResponse, status_code=status.HTTP_201_CREATED)
async def create_return(
    return_data: ReturnCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new return request."""
    try:
        return_obj = await ReturnService.create_return(db, return_data)
        return return_obj
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[ReturnResponse])
async def list_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order_id: Optional[int] = Query(None),
    status: Optional[ReturnStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List returns with optional filters."""
    returns = await ReturnService.list_returns(
        db, skip=skip, limit=limit, order_id=order_id, status=status
    )
    return returns


@router.get("/{return_id}", response_model=ReturnResponse)
async def get_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get return by ID."""
    return_obj = await ReturnService.get_return(db, return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    return return_obj


@router.patch("/{return_id}", response_model=ReturnResponse)
async def update_return(
    return_id: int,
    return_update: ReturnUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update return."""
    return_obj = await ReturnService.get_return(db, return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    
    return_obj = await ReturnService.update_return(db, return_obj, return_update)
    return return_obj


@router.post("/{return_id}/state", response_model=ReturnResponse)
async def update_return_state(
    return_id: int,
    state_update: ReturnStateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update return state (state machine transition)."""
    return_obj = await ReturnService.get_return(db, return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    
    try:
        return_obj = await ReturnService.transition_return_state(
            db, return_obj, state_update.action, state_update.reason
        )
        return return_obj
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{return_id}/approve", response_model=ReturnResponse)
async def approve_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Approve a return request."""
    return_obj = await ReturnService.get_return(db, return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    
    try:
        return_obj = await ReturnService.transition_return_state(db, return_obj, "approve")
        return return_obj
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{return_id}/reject", response_model=ReturnResponse)
async def reject_return(
    return_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    """Reject a return request."""
    return_obj = await ReturnService.get_return(db, return_id)
    if not return_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Return {return_id} not found",
        )
    
    try:
        return_obj = await ReturnService.transition_return_state(
            db, return_obj, "reject", reason=reason
        )
        return return_obj
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

