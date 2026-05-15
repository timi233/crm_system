from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.todo import TodoListResponse, TodoFilterParams
from app.services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=TodoListResponse)
async def list_todos(
    type: Optional[str] = Query(None, description="Filter by todo type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0, description="Skip offset"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    filters = TodoFilterParams(
        type=type,
        priority=priority,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )

    service = TodoService(db)
    items = await service.list_todos(
        user_id=current_user["id"],
        role=current_user["role"],
        filters=filters,
    )

    total = len(items)
    items = items[skip : skip + limit]

    return TodoListResponse(items=items, total=total)