import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.services.handover_service import HandoverService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handover", tags=["handover"])

# Permission summary:
# - list/get/assets-preview: scoped by HandoverService (admin=all, others=team_manager only)
# - assign/execute/cancel: admin can operate any request; a department manager
#   can operate requests where team_manager_user_id matches their user id.


@router.get("/requests", response_model=List[dict])
async def list_handover_requests(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User
    principal = build_principal(current_user)

    user_result = await db.execute(select(User).where(User.id == principal.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    requests = await service.get_handover_requests(user, status, skip, limit)

    return [
        {
            "id": r.id,
            "from_user_id": r.from_user_id,
            "to_user_id": r.to_user_id,
            "team_manager_user_id": r.team_manager_user_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "decided_at": r.decided_at.isoformat() if r.decided_at else None,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            "error_message": r.error_message,
        }
        for r in requests
    ]


@router.get("/requests/{request_id}")
async def get_handover_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User
    principal = build_principal(current_user)

    user_result = await db.execute(select(User).where(User.id == principal.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    request = await service.get_handover_request(request_id, user)

    if not request:
        raise HTTPException(status_code=404, detail="Handover request not found")

    return {
        "id": request.id,
        "from_user_id": request.from_user_id,
        "to_user_id": request.to_user_id,
        "team_manager_user_id": request.team_manager_user_id,
        "status": request.status,
        "scope_config": request.scope_config,
        "preview_summary": request.preview_summary,
        "execution_summary": request.execution_summary,
        "created_at": request.created_at.isoformat() if request.created_at else None,
        "decided_at": request.decided_at.isoformat() if request.decided_at else None,
        "executed_at": request.executed_at.isoformat() if request.executed_at else None,
        "error_message": request.error_message,
    }


@router.get("/requests/{request_id}/assets-preview")
async def get_handover_assets_preview(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User
    principal = build_principal(current_user)

    user_result = await db.execute(select(User).where(User.id == principal.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    request = await service.get_handover_request(request_id, user)

    if not request:
        raise HTTPException(status_code=404, detail="Handover request not found")

    preview = await service.get_assets_preview(request)
    return preview


@router.post("/requests/{request_id}/assign")
async def assign_handover_request(
    request_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User

    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    request = await service.get_handover_request(request_id, user)

    if not request:
        raise HTTPException(status_code=404, detail="Handover request not found")

    if request.status != HandoverRequestStatus.PENDING_ASSIGNMENT:
        raise HTTPException(status_code=400, detail=f"Request status must be pending_assignment, current: {request.status}")

    to_user_id = body.get("to_user_id")
    if not to_user_id:
        raise HTTPException(status_code=400, detail="to_user_id is required")

    scope_config = body.get("scope_config")

    try:
        updated_request = await service.assign_handover(request, to_user_id, scope_config)
        return {
            "success": True,
            "request_id": updated_request.id,
            "status": updated_request.status,
            "to_user_id": updated_request.to_user_id,
            "preview_summary": updated_request.preview_summary,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/execute")
async def execute_handover_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User

    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    request = await service.get_handover_request(request_id, user)

    if not request:
        raise HTTPException(status_code=404, detail="Handover request not found")

    try:
        result = await service.execute_handover(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/cancel")
async def cancel_handover_request(
    request_id: int,
    body: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.user import User

    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = HandoverService(db)
    request = await service.get_handover_request(request_id, user)

    if not request:
        raise HTTPException(status_code=404, detail="Handover request not found")

    reason = body.get("reason") if body else None

    try:
        updated_request = await service.cancel_handover(request, reason)
        return {
            "success": True,
            "request_id": updated_request.id,
            "status": updated_request.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
