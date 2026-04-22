from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.evaluation import Evaluation
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationRead,
    EvaluationUpdate,
)
from app.core.policy.service import policy_service, build_principal

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/", response_model=List[EvaluationRead])
async def list_evaluations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    work_order_id: Optional[int] = Query(None, description="Filter by work order ID"),
):
    principal = build_principal(current_user)

    stmt = select(Evaluation).options(
        selectinload(Evaluation.work_order),
    )

    if work_order_id:
        stmt = stmt.where(Evaluation.work_order_id == work_order_id)

    stmt = await policy_service.scope_query(
        resource="evaluation",
        action="list",
        principal=principal,
        db=db,
        query=stmt,
        model=Evaluation,
    )

    result = await db.execute(stmt)
    evaluations = result.scalars().all()
    return evaluations


@router.post("/", response_model=EvaluationRead)
async def create_evaluation(
    evaluation: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)

    stmt = select(WorkOrder).where(WorkOrder.id == evaluation.work_order_id)
    result = await db.execute(stmt)
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order with id {evaluation.work_order_id} not found",
        )

    if work_order.status != WorkOrderStatus.DONE:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create evaluation for work order with status {work_order.status.value}. Only DONE status is allowed.",
        )

    await policy_service.authorize_create(
        resource="evaluation",
        principal=principal,
        db=db,
        payload=evaluation,
    )

    check_stmt = select(Evaluation).where(
        Evaluation.work_order_id == evaluation.work_order_id
    )
    check_result = await db.execute(check_stmt)
    existing_evaluation = check_result.scalar_one_or_none()

    if existing_evaluation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order {evaluation.work_order_id} has already been evaluated",
        )

    new_evaluation = Evaluation(
        work_order_id=evaluation.work_order_id,
        quality_rating=evaluation.quality_rating,
        response_rating=evaluation.response_rating,
        customer_feedback=evaluation.customer_feedback,
        improvement_suggestion=evaluation.improvement_suggestion,
        recommend=evaluation.recommend,
        evaluator_id=current_user["id"],
    )

    db.add(new_evaluation)

    await db.commit()
    await db.refresh(new_evaluation)
    return new_evaluation


@router.get("/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    stmt = (
        select(Evaluation)
        .options(selectinload(Evaluation.work_order))
        .where(Evaluation.id == evaluation_id)
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found"
        )

    await policy_service.authorize(
        resource="evaluation",
        action="read",
        principal=principal,
        db=db,
        obj=evaluation,
    )

    return evaluation


@router.put("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found"
        )

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="evaluation",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    update_data = evaluation.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.commit()
    await db.refresh(existing)
    return existing
