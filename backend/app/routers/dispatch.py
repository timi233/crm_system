import hashlib
import hmac
import os
import time

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.database import get_db
from app.models.dispatch_record import DispatchRecord
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.user import User
from app.models.work_order import WorkOrder, WorkOrderApprovalStatus, WorkOrderStatus
from app.schemas.dispatch import (
    DispatchApplicationRequest,
    DispatchApplicationResponse,
    DispatchRecordRead,
    DispatchWebhookPayload,
    TechnicianInfo,
)
from app.services.local_dispatch_service import LocalDispatchService
from app.services.work_order_notification_service import queue_dispatch_card_notifications


WEBHOOK_TIMESTAMP_WINDOW_SECONDS = 300


router = APIRouter(tags=["dispatch"])

WEBHOOK_STATUS_MAP = {
    "pending": WorkOrderStatus.PENDING,
    "accepted": WorkOrderStatus.ACCEPTED,
    "in_service": WorkOrderStatus.IN_SERVICE,
    "in_progress": WorkOrderStatus.IN_SERVICE,
    "done": WorkOrderStatus.DONE,
    "completed": WorkOrderStatus.DONE,
    "cancelled": WorkOrderStatus.CANCELLED,
    "canceled": WorkOrderStatus.CANCELLED,
    "rejected": WorkOrderStatus.REJECTED,
}

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
    return new_status in VALID_STATUS_TRANSITIONS.get(current_status, [])


def _has_approved_assignment(work_order: WorkOrder) -> bool:
    return any(
        technician.approval_status == WorkOrderApprovalStatus.APPROVED
        for technician in work_order.technicians
    )


def _apply_status_timestamp(work_order: WorkOrder, new_status: WorkOrderStatus) -> None:
    if new_status == WorkOrderStatus.ACCEPTED:
        work_order.accepted_at = datetime.utcnow()
    elif new_status == WorkOrderStatus.IN_SERVICE:
        work_order.started_at = datetime.utcnow()
    elif new_status in {
        WorkOrderStatus.DONE,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.REJECTED,
    }:
        work_order.completed_at = datetime.utcnow()


async def fill_technician_names(db: AsyncSession, records: list) -> list:
    all_ids = set()
    work_order_ids = set()
    for record in records:
        if record.technician_ids:
            for technician_id in record.technician_ids:
                try:
                    all_ids.add(int(technician_id))
                except (ValueError, TypeError):
                    pass
        if record.work_order_id:
            work_order_ids.add(record.work_order_id)

    user_map = {}
    if all_ids:
        result = await db.execute(select(User.id, User.name).where(User.id.in_(all_ids)))
        user_map = {row[0]: row[1] for row in result.fetchall()}

    work_order_map = {}
    if work_order_ids:
        result = await db.execute(
            select(
                WorkOrder.id,
                WorkOrder.estimated_start_date,
                WorkOrder.estimated_start_period,
                WorkOrder.estimated_end_date,
                WorkOrder.estimated_end_period,
            ).where(WorkOrder.id.in_(work_order_ids))
        )
        for row in result.fetchall():
            work_order_map[row[0]] = {
                "estimated_start_date": row[1],
                "estimated_start_period": row[2],
                "estimated_end_date": row[3],
                "estimated_end_period": row[4],
            }

    for record in records:
        if record.technician_ids:
            names = []
            for technician_id in record.technician_ids:
                try:
                    user_id = int(technician_id)
                    if user_id in user_map:
                        names.append(user_map[user_id])
                except (ValueError, TypeError):
                    pass
            record.technician_names = names
        else:
            record.technician_names = []

        if record.work_order_id:
            work_order_id = record.work_order_id
            if work_order_id in work_order_map:
                work_order = work_order_map[work_order_id]
                record.estimated_start_date = work_order["estimated_start_date"]
                record.estimated_start_period = work_order["estimated_start_period"]
                record.estimated_end_date = work_order["estimated_end_date"]
                record.estimated_end_period = work_order["estimated_end_period"]

    return records


async def _create_dispatch_for_source(
    source_type: str,
    source_id: int,
    request: DispatchApplicationRequest,
    current_user: dict,
    db: AsyncSession,
):
    if not request.technician_ids:
        raise HTTPException(status_code=400, detail="请选择服务工程师")

    if source_type == "lead":
        result = await db.execute(select(Lead).where(Lead.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Lead not found")
        owner_id = source.sales_owner_id
        forbidden_detail = "只有管理员或线索负责人才能创建派工"
    elif source_type == "opportunity":
        result = await db.execute(select(Opportunity).where(Opportunity.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        owner_id = source.sales_owner_id
        forbidden_detail = "只有管理员或商机负责人才能创建派工"
    else:
        result = await db.execute(select(Project).where(Project.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Project not found")
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="dispatch_record",
        principal=principal,
        db=db,
        payload=request,
        source_obj=source,
        source_type=source_type,
    )

    dispatch_service = LocalDispatchService()
    try:
        await dispatch_service.validate_technicians(db, request.technician_ids)
        if source_type == "lead":
            crm_data = await dispatch_service.get_customer_data_from_lead(db, source)
        elif source_type == "opportunity":
            crm_data = await dispatch_service.get_customer_data_from_opportunity(db, source)
        else:
            crm_data = await dispatch_service.get_customer_data_from_project(db, source)

        work_order, dispatch_record = await dispatch_service.create_dispatch_atomically(
            db=db,
            crm_data=crm_data,
            source_type=source_type,
            source_id=source.id,
            technician_ids=request.technician_ids,
            submitter_id=current_user["id"],
            service_mode=request.service_mode,
            start_date=request.start_date,
            start_period=request.start_period,
            end_date=request.end_date,
            end_period=request.end_period,
            work_type=request.work_type,
        )
        queue_dispatch_card_notifications(work_order.id, request.technician_ids)

        return DispatchApplicationResponse(
            success=True,
            message="派工创建成功",
            work_order_id=str(work_order.id),
            work_order_no=work_order.work_order_no,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(exc)}")


@router.get("/dispatch/technicians", response_model=list[TechnicianInfo])
async def get_dispatch_technicians(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query = select(User).where(User.functional_role == "TECHNICIAN", User.is_active == True)
    query = await policy_service.scope_query(
        resource="user",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=User,
        functional_role="TECHNICIAN",
    )
    result = await db.execute(query)
    technicians = result.scalars().all()
    return [
        TechnicianInfo(
            id=tech.id,
            name=tech.name,
            phone=tech.phone,
            department=tech.department,
        )
        for tech in technicians
    ]


@router.post("/leads/{lead_id}/create-dispatch", response_model=DispatchApplicationResponse)
async def create_dispatch_from_lead(
    lead_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_dispatch_for_source("lead", lead_id, request, current_user, db)


@router.post(
    "/opportunities/{opportunity_id}/create-dispatch",
    response_model=DispatchApplicationResponse,
)
async def create_dispatch_from_opportunity(
    opportunity_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_dispatch_for_source(
        "opportunity",
        opportunity_id,
        request,
        current_user,
        db,
    )


@router.post("/projects/{project_id}/create-dispatch", response_model=DispatchApplicationResponse)
async def create_dispatch_from_project(
    project_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_dispatch_for_source("project", project_id, request, current_user, db)


@router.post("/webhooks/dispatch")
async def dispatch_webhook(
    request: Request,
    payload: DispatchWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    dispatch_webhook_secret = os.environ.get("DISPATCH_WEBHOOK_SECRET")
    if not dispatch_webhook_secret:
        raise HTTPException(status_code=500, detail="DISPATCH_WEBHOOK_SECRET not configured")

    signature = request.headers.get("X-Dispatch-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Dispatch-Signature header")

    timestamp = request.headers.get("X-Dispatch-Timestamp")
    event_id = request.headers.get("X-Dispatch-Event-Id")
    if not timestamp or not event_id:
        raise HTTPException(status_code=400, detail="Missing X-Dispatch-Timestamp or X-Dispatch-Event-Id header")

    try:
        ts_int = int(timestamp)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid X-Dispatch-Timestamp format")

    if abs(time.time() - ts_int) > WEBHOOK_TIMESTAMP_WINDOW_SECONDS:
        raise HTTPException(status_code=401, detail="Webhook timestamp expired")

    body = await request.body()
    signed_payload = f"{timestamp}.".encode() + body
    expected_signature = hmac.new(
        dispatch_webhook_secret.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    existing_event = await db.execute(
        select(DispatchRecord).where(
            DispatchRecord.dispatch_data["event_id"].astext == event_id
        )
    )
    if existing_event.scalar_one_or_none():
        return {"success": True, "message": "Duplicate event ignored"}

    try:
        work_order_id = int(payload.work_order_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid work_order_id")

    work_order_result = await db.execute(
        select(WorkOrder)
        .options(selectinload(WorkOrder.technicians))
        .where(WorkOrder.id == work_order_id)
    )
    local_work_order = work_order_result.scalar_one_or_none()
    if not local_work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    new_status = WEBHOOK_STATUS_MAP.get(payload.status.lower())
    if not new_status:
        raise HTTPException(status_code=400, detail="Unknown dispatch status")

    if local_work_order.status != new_status:
        if not _is_valid_status_transition(local_work_order.status, new_status):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid status transition: "
                    f"{local_work_order.status.value} -> {new_status.value}"
                ),
            )

        if new_status in {WorkOrderStatus.IN_SERVICE, WorkOrderStatus.DONE}:
            if not _has_approved_assignment(local_work_order):
                raise HTTPException(
                    status_code=400,
                    detail="至少需要一位审批通过的技术员后，工单才能继续流转",
                )

    result = await db.execute(
        select(DispatchRecord).where(DispatchRecord.work_order_id == work_order_id)
    )
    dispatch_record = result.scalar_one_or_none()

    dispatch_data = payload.model_dump()
    dispatch_data["event_id"] = event_id
    dispatch_data["processed_timestamp"] = time.time()

    try:
        if not dispatch_record:
            dispatch_record = DispatchRecord(
                work_order_id=work_order_id,
                work_order_no=payload.work_order_no,
                source_type=local_work_order.source_type.value
                if local_work_order.source_type
                else (
                    payload.metadata.get("source_type", "unknown")
                    if payload.metadata
                    else "unknown"
                ),
                lead_id=local_work_order.lead_id,
                opportunity_id=local_work_order.opportunity_id,
                project_id=local_work_order.project_id,
                status=payload.status,
                previous_status=payload.previous_status,
                status_updated_at=datetime.utcnow(),
                order_type=payload.metadata.get("order_type") if payload.metadata else None,
                dispatch_data=dispatch_data,
            )
            db.add(dispatch_record)
        else:
            dispatch_record.status = payload.status
            dispatch_record.previous_status = payload.previous_status
            dispatch_record.status_updated_at = datetime.utcnow()
            dispatch_record.work_order_no = payload.work_order_no
            if dispatch_record.dispatch_data:
                dispatch_record.dispatch_data.update(dispatch_data)
            else:
                dispatch_record.dispatch_data = dispatch_data

        if local_work_order.status != new_status:
            local_work_order.status = new_status
            _apply_status_timestamp(local_work_order, new_status)

        await db.commit()
        await db.refresh(dispatch_record)
        return {"success": True, "message": "Webhook processed successfully"}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process webhook: {str(exc)}",
        )


@router.get("/leads/{lead_id}/dispatch-history", response_model=list[DispatchRecordRead])
async def get_lead_dispatch_history(
    lead_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await policy_service.authorize(
        resource="lead",
        action="read",
        principal=principal,
        db=db,
        obj=lead,
    )
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.lead_id == lead_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return await fill_technician_names(db, records)


@router.get(
    "/opportunities/{opportunity_id}/dispatch-history",
    response_model=list[DispatchRecordRead],
)
async def get_opportunity_dispatch_history(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    await policy_service.authorize(
        resource="opportunity",
        action="read",
        principal=principal,
        db=db,
        obj=opportunity,
    )
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.opportunity_id == opportunity_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return await fill_technician_names(db, records)


@router.get("/projects/{project_id}/dispatch-history", response_model=list[DispatchRecordRead])
async def get_project_dispatch_history(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await policy_service.authorize(
        resource="project",
        action="read",
        principal=principal,
        db=db,
        obj=project,
    )
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.project_id == project_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return await fill_technician_names(db, records)


@router.get("/dispatch-records", response_model=list[DispatchRecordRead])
async def list_dispatch_records(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query = await policy_service.scope_query(
        resource="dispatch_record",
        action="list",
        principal=principal,
        db=db,
        query=select(DispatchRecord).order_by(DispatchRecord.created_at.desc()),
        model=DispatchRecord,
    )
    result = await db.execute(query)
    records = result.scalars().all()
    return await fill_technician_names(db, records)


@router.get("/dispatch-records/{record_id}", response_model=DispatchRecordRead)
async def get_dispatch_record(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(DispatchRecord).where(DispatchRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Dispatch record not found")
    await policy_service.authorize(
        resource="dispatch_record",
        action="read",
        principal=principal,
        db=db,
        obj=record,
    )
    records = await fill_technician_names(db, [record])
    return records[0]
