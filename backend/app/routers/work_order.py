import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.work_order import (
    WorkOrder,
    WorkOrderTechnician,
    OrderType,
    WorkOrderPriority,
    WorkOrderStatus,
    SourceType,
)
from app.models.user import User
from app.models.channel import Channel
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderUpdate,
    WorkOrderStatusUpdate,
    WorkOrderAssignRequest,
    WorkOrderListResponse,
)
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
)
from app.services.auto_number_service import generate_code

router = APIRouter(prefix="/work-orders", tags=["work-orders"])
logger = logging.getLogger(__name__)


def check_work_order_access(
    work_order: WorkOrder, current_user: dict, require_owner: bool = False
):
    """Check if user can access/modify a work order.

    Admin can access all.
    Business can access all work orders.
    Sales can access work orders they submitted or are related to.
    Technician can access work orders assigned to them.
    Finance has no access (not financial data).
    """
    from sqlalchemy import select
    from app.database import AsyncSession
    import asyncio

    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_role == "admin":
        return

    if user_role == "business":
        return

    if user_role == "sales":
        if require_owner:
            if (
                work_order.submitter_id != user_id
                and work_order.related_sales_id != user_id
            ):
                raise HTTPException(
                    status_code=403, detail="您只能操作自己提交或负责的工单"
                )
        else:
            if (
                work_order.submitter_id != user_id
                and work_order.related_sales_id != user_id
            ):
                raise HTTPException(
                    status_code=403, detail="您只能查看自己提交或负责的工单"
                )
        return

    if user_role == "technician":
        if not work_order.technicians:
            raise HTTPException(status_code=403, detail="您只能查看被分配给自己的工单")
        assigned = any(tech.technician_id == user_id for tech in work_order.technicians)
        if not assigned:
            raise HTTPException(status_code=403, detail="您只能查看被分配给自己的工单")
        return

    raise HTTPException(status_code=403, detail="无权限访问此工单")


VALID_STATUS_TRANSITIONS = {
    WorkOrderStatus.PENDING: [
        WorkOrderStatus.ACCEPTED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.REJECTED,
    ],
    WorkOrderStatus.ACCEPTED: [
        WorkOrderStatus.IN_SERVICE,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.REJECTED,
    ],
    WorkOrderStatus.IN_SERVICE: [WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED],
    WorkOrderStatus.DONE: [],
    WorkOrderStatus.CANCELLED: [],
    WorkOrderStatus.REJECTED: [],
}


def _is_valid_status_transition(
    current_status: WorkOrderStatus, new_status: WorkOrderStatus
) -> bool:
    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed


def _build_response(work_order: WorkOrder) -> dict:
    response = WorkOrderRead.model_validate(work_order)
    response.submitter_name = (
        work_order.submitter.name if work_order.submitter else None
    )
    response.related_sales_name = (
        work_order.related_sales.name if work_order.related_sales else None
    )
    response.channel_name_display = work_order.channel_name or (
        work_order.channel.company_name if work_order.channel else None
    )
    response.technician_names = [
        t.technician.name for t in work_order.technicians if t.technician
    ]
    return response


@router.get("/", response_model=List[WorkOrderRead])
async def list_work_orders(
    status: Optional[WorkOrderStatus] = None,
    submitter_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.core.dependencies import apply_data_scope_filter

    query = select(WorkOrder).options(
        selectinload(WorkOrder.submitter),
        selectinload(WorkOrder.related_sales),
        selectinload(WorkOrder.channel),
        selectinload(WorkOrder.technicians).selectinload(
            WorkOrderTechnician.technician
        ),
    )

    query = apply_data_scope_filter(query, WorkOrder, current_user, db)

    if status is not None:
        query = query.where(WorkOrder.status == status)
    if submitter_id is not None:
        query = query.where(WorkOrder.submitter_id == submitter_id)
    if channel_id is not None:
        query = query.where(WorkOrder.channel_id == channel_id)

    result = await db.execute(query)
    work_orders = result.scalars().all()

    return [_build_response(wo) for wo in work_orders]


@router.post("/", response_model=WorkOrderRead)
async def create_work_order(
    request: Request,
    work_order: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "sales", "technician"])),
):
    submitter_id = current_user["id"]
    if current_user.get("role") != "admin" and work_order.submitter_id is not None:
        if work_order.submitter_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="只能以自己作为工单提交人")

    related_sales_id = work_order.related_sales_id
    if current_user.get("role") != "admin":
        if related_sales_id is None:
            related_sales_id = current_user["id"]
        elif related_sales_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="只能将自己设为负责销售")

    if work_order.has_channel and work_order.channel_id is not None:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == work_order.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(
                status_code=400,
                detail=f"Channel with id {work_order.channel_id} not found",
            )

    new_work_order = WorkOrder(
        work_order_no=await generate_code(db, "work_order"),
        order_type=work_order.order_type,
        submitter_id=submitter_id,
        related_sales_id=related_sales_id,
        customer_name=work_order.customer_name,
        customer_contact=work_order.customer_contact,
        customer_phone=work_order.customer_phone,
        has_channel=work_order.has_channel,
        channel_id=work_order.channel_id,
        channel_name=work_order.channel_name,
        channel_contact=work_order.channel_contact,
        channel_phone=work_order.channel_phone,
        manufacturer_contact=work_order.manufacturer_contact,
        work_type=work_order.work_type,
        priority=work_order.priority,
        description=work_order.description,
        status=WorkOrderStatus.PENDING,
        estimated_start_date=work_order.estimated_start_date,
        estimated_start_period=work_order.estimated_start_period,
        estimated_end_date=work_order.estimated_end_date,
        estimated_end_period=work_order.estimated_end_period,
        source_type=work_order.source_type,
        lead_id=work_order.lead_id,
        opportunity_id=work_order.opportunity_id,
        project_id=work_order.project_id,
    )
    db.add(new_work_order)
    await db.commit()
    await db.refresh(new_work_order)

    result = await db.execute(
        select(WorkOrder)
        .options(
            selectinload(WorkOrder.submitter),
            selectinload(WorkOrder.related_sales),
            selectinload(WorkOrder.channel),
            selectinload(WorkOrder.technicians).selectinload(
                WorkOrderTechnician.technician
            ),
        )
        .where(WorkOrder.id == new_work_order.id)
    )
    new_work_order = result.scalar_one_or_none()

    try:
        await log_create(
            db=db,
            user_id=current_user.get("id", 0),
            user_name=current_user.get("name", ""),
            entity_type="work_order",
            entity_id=new_work_order.id,
            entity_code=new_work_order.work_order_no,
            entity_name=new_work_order.customer_name,
            description=f"创建工单: {new_work_order.work_order_no} - {new_work_order.customer_name}",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to write work order creation audit log",
            extra={"work_order_id": new_work_order.id},
        )

    response = _build_response(new_work_order)
    return response


@router.get("/{work_order_id}", response_model=WorkOrderRead)
async def get_work_order(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkOrder)
        .options(
            selectinload(WorkOrder.submitter),
            selectinload(WorkOrder.related_sales),
            selectinload(WorkOrder.channel),
            selectinload(WorkOrder.technicians).selectinload(
                WorkOrderTechnician.technician
            ),
        )
        .where(WorkOrder.id == work_order_id)
    )
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    check_work_order_access(work_order, current_user, require_owner=False)

    return _build_response(work_order)


@router.put("/{work_order_id}", response_model=WorkOrderRead)
async def update_work_order(
    work_order_id: int,
    work_order: WorkOrderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkOrder)
        .options(selectinload(WorkOrder.technicians))
        .where(WorkOrder.id == work_order_id)
    )
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="Work order not found")

    check_work_order_access(existing, current_user, require_owner=True)

    if (
        work_order.related_sales_id is not None
        and work_order.related_sales_id != existing.related_sales_id
    ):
        sales_result = await db.execute(
            select(User).where(User.id == work_order.related_sales_id)
        )
        sales_user = sales_result.scalar_one_or_none()
        if not sales_user:
            raise HTTPException(
                status_code=400,
                detail=f"Related sales user with id {work_order.related_sales_id} not found",
            )

    if (
        work_order.channel_id is not None
        and work_order.channel_id != existing.channel_id
    ):
        if work_order.has_channel or work_order.channel_id is not None:
            channel_result = await db.execute(
                select(Channel).where(Channel.id == work_order.channel_id)
            )
            channel = channel_result.scalar_one_or_none()
            if not channel:
                raise HTTPException(
                    status_code=400,
                    detail=f"Channel with id {work_order.channel_id} not found",
                )

    update_data = work_order.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.commit()

    result = await db.execute(
        select(WorkOrder)
        .options(
            selectinload(WorkOrder.submitter),
            selectinload(WorkOrder.related_sales),
            selectinload(WorkOrder.channel),
            selectinload(WorkOrder.technicians).selectinload(
                WorkOrderTechnician.technician
            ),
        )
        .where(WorkOrder.id == work_order_id)
    )
    existing = result.scalar_one_or_none()

    try:
        await log_update(
            db=db,
            user_id=current_user.get("id", 0),
            user_name=current_user.get("name", ""),
            entity_type="work_order",
            entity_id=existing.id,
            entity_code=existing.work_order_no,
            entity_name=existing.customer_name,
            description=f"更新工单: {existing.work_order_no} - {existing.customer_name}",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to write work order update audit log",
            extra={"work_order_id": existing.id},
        )

    return _build_response(existing)


@router.patch("/{work_order_id}/status", response_model=WorkOrderRead)
async def update_work_order_status(
    work_order_id: int,
    status_update: WorkOrderStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkOrder)
        .options(selectinload(WorkOrder.technicians))
        .where(WorkOrder.id == work_order_id)
    )
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    check_work_order_access(work_order, current_user, require_owner=True)

    old_status = work_order.status

    if not _is_valid_status_transition(old_status, status_update.status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {old_status.value} -> {status_update.status.value}. "
            f"Valid transitions: {[s.value for s in VALID_STATUS_TRANSITIONS.get(old_status, [])]}",
        )

    work_order.status = status_update.status
    if status_update.service_summary is not None:
        work_order.service_summary = status_update.service_summary
    if status_update.cancel_reason is not None:
        work_order.cancel_reason = status_update.cancel_reason

    if status_update.status == WorkOrderStatus.ACCEPTED:
        work_order.accepted_at = datetime.utcnow()
    elif status_update.status == WorkOrderStatus.IN_SERVICE:
        work_order.started_at = datetime.utcnow()
    elif status_update.status == WorkOrderStatus.DONE:
        work_order.completed_at = datetime.utcnow()

    await db.commit()

    try:
        await log_update(
            db=db,
            user_id=current_user.get("id", 0),
            user_name=current_user.get("name", ""),
            entity_type="work_order",
            entity_id=work_order.id,
            entity_code=work_order.work_order_no,
            entity_name=work_order.customer_name,
            old_value={"status": old_status.value},
            new_value={"status": status_update.status.value},
            description=f"工单状态变更: {work_order.work_order_no} - {old_status.value} -> {status_update.status.value}",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to write work order status audit log",
            extra={"work_order_id": work_order.id},
        )

    result = await db.execute(
        select(WorkOrder)
        .options(
            selectinload(WorkOrder.submitter),
            selectinload(WorkOrder.related_sales),
            selectinload(WorkOrder.channel),
            selectinload(WorkOrder.technicians).selectinload(
                WorkOrderTechnician.technician
            ),
        )
        .where(WorkOrder.id == work_order_id)
    )
    work_order = result.scalar_one_or_none()
    return _build_response(work_order)


@router.post("/{work_order_id}/assign")
async def assign_technicians(
    work_order_id: int,
    assign_request: WorkOrderAssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "sales"])),
):
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    check_work_order_access(work_order, current_user, require_owner=True)

    for technician_id in assign_request.technician_ids:
        technician_result = await db.execute(
            select(User).where(User.id == technician_id)
        )
        technician = technician_result.scalar_one_or_none()
        if not technician:
            raise HTTPException(
                status_code=400, detail=f"用户 id={technician_id} 不存在"
            )
        if technician.functional_role != "TECHNICIAN":
            raise HTTPException(
                status_code=400,
                detail=f"用户 {technician.name} 不是技术员（functional_role={technician.functional_role})",
            )

        existing_assignment = await db.execute(
            select(WorkOrderTechnician).where(
                WorkOrderTechnician.work_order_id == work_order_id,
                WorkOrderTechnician.technician_id == technician_id,
            )
        )
        if existing_assignment.scalar_one_or_none():
            continue

        assignment = WorkOrderTechnician(
            work_order_id=work_order_id,
            technician_id=technician_id,
        )
        db.add(assignment)

    await db.commit()

    try:
        await log_update(
            db=db,
            user_id=current_user.get("id", 0),
            user_name=current_user.get("name", ""),
            entity_type="work_order",
            entity_id=work_order.id,
            entity_code=work_order.work_order_no,
            entity_name=work_order.customer_name,
            description=f"工单技术员分配: {work_order.work_order_no} - {', '.join([str(t) for t in assign_request.technician_ids])}",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to write work order assignment audit log",
            extra={"work_order_id": work_order.id},
        )

    result = await db.execute(
        select(WorkOrder)
        .options(
            selectinload(WorkOrder.submitter),
            selectinload(WorkOrder.related_sales),
            selectinload(WorkOrder.channel),
            selectinload(WorkOrder.technicians).selectinload(
                WorkOrderTechnician.technician
            ),
        )
        .where(WorkOrder.id == work_order_id)
    )
    work_order = result.scalar_one_or_none()
    return _build_response(work_order)


@router.delete("/{work_order_id}")
async def delete_work_order(
    work_order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin"])),
):
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
    work_order = result.scalar_one_or_none()

    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    await log_delete(
        db=db,
        user_id=current_user.get("id", 0),
        user_name=current_user.get("name", ""),
        entity_type="work_order",
        entity_id=work_order_id,
        entity_code=work_order.work_order_no,
        entity_name=work_order.customer_name,
        description=f"删除工单: {work_order.work_order_no} - {work_order.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(work_order)
    await db.commit()

    return {"message": "Work order deleted successfully"}
