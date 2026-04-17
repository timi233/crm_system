from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import (
    get_current_user,
    require_roles,
    apply_data_scope_filter,
)
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.evaluation import Evaluation
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationRead,
    EvaluationUpdate,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/", response_model=List[EvaluationRead])
async def list_evaluations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    work_order_id: Optional[int] = Query(None, description="Filter by work order ID"),
):
    if current_user.get("role") != "admin":
        if work_order_id:
            wo_result = await db.execute(
                select(WorkOrder).where(WorkOrder.id == work_order_id)
            )
            work_order = wo_result.scalar_one_or_none()
            if work_order:
                user_id = current_user.get("id")
                if (
                    work_order.submitter_id != user_id
                    and work_order.related_sales_id != user_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="只能查看自己相关工单的评价",
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="非管理员必须指定工单ID",
            )

    stmt = select(Evaluation).options(
        selectinload(Evaluation.work_order),
    )

    if work_order_id:
        stmt = stmt.where(Evaluation.work_order_id == work_order_id)

    result = await db.execute(stmt)
    evaluations = result.scalars().all()
    return evaluations


@router.post("/", response_model=EvaluationRead)
async def create_evaluation(
    evaluation: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "sales"])),
):
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    stmt = select(WorkOrder).where(WorkOrder.id == evaluation.work_order_id)
    result = await db.execute(stmt)
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order with id {evaluation.work_order_id} not found",
        )

    if work_order.status != WorkOrderStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create evaluation for work order with status {work_order.status.value}. Only DONE status is allowed.",
        )

    if user_role == "sales":
        if (
            work_order.submitter_id != user_id
            and work_order.related_sales_id != user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能为自己提交或负责的工单创建评价",
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
    await db.flush()
    await db.commit()
    await db.refresh(new_evaluation)
    return new_evaluation


@router.get("/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user.get("id")

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

    if user_role == "admin":
        return evaluation

    if evaluation.work_order:
        wo = evaluation.work_order
        if user_role == "sales":
            if wo.submitter_id != user_id and wo.related_sales_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能查看自己相关工单的评价",
                )
            return evaluation

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看此评价"
    )


@router.put("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "sales"])),
):
    stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found"
        )

    if current_user.get("role") != "admin":
        stmt = select(WorkOrder).where(WorkOrder.id == existing.work_order_id)
        wo_result = await db.execute(stmt)
        work_order = wo_result.scalar_one_or_none()
        if work_order:
            user_id = current_user.get("id")
            if (
                work_order.submitter_id != user_id
                and work_order.related_sales_id != user_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能修改自己相关工单的评价",
                )

    update_data = evaluation.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.commit()
    await db.refresh(existing)
    return existing
