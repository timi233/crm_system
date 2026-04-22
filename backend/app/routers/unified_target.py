from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.database import get_db
from app.models.unified_target import UnifiedTarget, TargetType
from app.models.user import User
from app.models.channel import Channel
from app.core.dependencies import get_current_user
from app.schemas.unified_target import (
    UnifiedTargetCreate,
    UnifiedTargetRead,
    UnifiedTargetUpdate,
)
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
)
from app.core.policy import policy_service, build_principal

router = APIRouter(prefix="/unified-targets", tags=["unified-targets"])
TARGET_METRIC_FIELDS = (
    ("performance_target", "业绩目标"),
    ("opportunity_target", "商机目标"),
    ("project_count_target", "项目目标"),
)


def _serialize_unified_target(target: UnifiedTarget) -> UnifiedTargetRead:
    return UnifiedTargetRead.model_validate(
        {
            "id": target.id,
            "target_type": target.target_type,
            "channel_id": target.channel_id,
            "user_id": target.user_id,
            "year": target.year,
            "quarter": target.quarter,
            "month": target.month,
            "performance_target": target.performance_target,
            "opportunity_target": target.opportunity_target,
            "project_count_target": target.project_count_target,
            "development_goal": target.development_goal,
            "created_at": target.created_at,
            "updated_at": target.updated_at,
            "created_by": target.created_by,
            "channel_name": target.channel.company_name if getattr(target, "channel", None) else None,
            "user_name": target.user.name if getattr(target, "user", None) else None,
            "achieved_performance": target.achieved_performance,
            "achieved_opportunity": target.achieved_opportunity,
            "achieved_project_count": target.achieved_project_count,
        }
    )


def _translate_target_integrity_error(exc: IntegrityError) -> HTTPException:
    message = str(getattr(exc, "orig", exc))
    if "uq_unified_targets_annual_scope" in message:
        return HTTPException(status_code=400, detail="同一主体同一年只能有一个年目标")
    if "uq_unified_targets_quarter_scope" in message:
        return HTTPException(status_code=400, detail="同一主体同一年同一季度只能有一个季度目标")
    return HTTPException(status_code=400, detail="目标数据冲突，请刷新后重试")


def _build_target_scope_filters(
    *,
    target_type: TargetType,
    year: int,
    channel_id: Optional[int],
    user_id: Optional[int],
):
    filters = [
        UnifiedTarget.target_type == target_type,
        UnifiedTarget.year == year,
        UnifiedTarget.channel_id == channel_id,
        UnifiedTarget.user_id == user_id,
    ]
    return filters


def _is_annual_target(*, quarter: Optional[int], month: Optional[int]) -> bool:
    return quarter is None and month is None


def _is_quarterly_target(*, quarter: Optional[int], month: Optional[int]) -> bool:
    return quarter is not None and month is None


def _decimal_or_zero(value):
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


async def _load_same_scope_targets(
    db: AsyncSession,
    *,
    target_type: TargetType,
    year: int,
    channel_id: Optional[int],
    user_id: Optional[int],
    exclude_id: Optional[int] = None,
):
    stmt = select(UnifiedTarget).where(
        *_build_target_scope_filters(
            target_type=target_type,
            year=year,
            channel_id=channel_id,
            user_id=user_id,
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(UnifiedTarget.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalars().all()


def _validate_target_owner_fields(*, channel_id: Optional[int], user_id: Optional[int]):
    if (channel_id is None and user_id is None) or (
        channel_id is not None and user_id is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="channel_id 和 user_id 必须且只能提供一个",
        )


def _classify_targets(targets: List[UnifiedTarget]):
    annual = None
    quarterly = []
    monthly = []
    for target in targets:
        if _is_annual_target(quarter=target.quarter, month=target.month):
            annual = target
        elif _is_quarterly_target(quarter=target.quarter, month=target.month):
            quarterly.append(target)
        else:
            monthly.append(target)
    return annual, quarterly, monthly


def _validate_quarterly_metrics(
    *,
    annual_target: UnifiedTarget,
    quarterly_targets: List[UnifiedTarget],
    current_quarter: int,
    current_values: dict,
):
    quarter_map = {target.quarter: target for target in quarterly_targets}
    if current_quarter in quarter_map:
        raise HTTPException(
            status_code=400,
            detail=f"Q{current_quarter} 目标已存在，不能重复创建",
        )

    planned_quarters = set(quarter_map.keys())
    planned_quarters.add(current_quarter)
    all_quarters_complete = planned_quarters == {1, 2, 3, 4}

    for field_name, label in TARGET_METRIC_FIELDS:
        annual_value = getattr(annual_target, field_name)
        current_value = current_values.get(field_name)
        siblings_total = sum(_decimal_or_zero(getattr(target, field_name)) for target in quarterly_targets)
        planned_total = siblings_total + _decimal_or_zero(current_value)

        if current_value is not None and annual_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"请先设置年{label}，再设置季度{label}",
            )

        if annual_value is not None and current_value is not None:
            if _decimal_or_zero(current_value) > _decimal_or_zero(annual_value):
                raise HTTPException(
                    status_code=400,
                    detail=f"单季度{label}不能超过年{label}",
                )

        if annual_value is not None and planned_total > _decimal_or_zero(annual_value):
            raise HTTPException(
                status_code=400,
                detail=f"季度{label}合计不能超过年{label}",
            )

        if annual_value is not None and all_quarters_complete and planned_total != _decimal_or_zero(annual_value):
            raise HTTPException(
                status_code=400,
                detail=f"Q1-Q4 {label}合计必须等于年{label}",
            )


def _validate_annual_metrics_against_children(
    *,
    annual_values: dict,
    quarterly_targets: List[UnifiedTarget],
):
    quarter_set = {target.quarter for target in quarterly_targets if target.quarter is not None}
    all_quarters_complete = quarter_set == {1, 2, 3, 4}

    for field_name, label in TARGET_METRIC_FIELDS:
        annual_value = annual_values.get(field_name)
        children_total = sum(_decimal_or_zero(getattr(target, field_name)) for target in quarterly_targets)

        if children_total > 0 and annual_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"已存在季度{label}，年{label}不能为空",
            )

        if annual_value is None:
            continue

        annual_decimal = _decimal_or_zero(annual_value)
        if children_total > annual_decimal:
            raise HTTPException(
                status_code=400,
                detail=f"已有季度{label}合计不能超过年{label}",
            )

        if all_quarters_complete and children_total != annual_decimal:
            raise HTTPException(
                status_code=400,
                detail=f"Q1-Q4 {label}合计必须等于年{label}",
            )


async def _validate_unified_target_payload(
    db: AsyncSession,
    *,
    payload: dict,
    exclude_id: Optional[int] = None,
):
    _validate_target_owner_fields(
        channel_id=payload.get("channel_id"),
        user_id=payload.get("user_id"),
    )

    quarter = payload.get("quarter")
    month = payload.get("month")
    if quarter is not None and quarter not in {1, 2, 3, 4}:
        raise HTTPException(status_code=400, detail="季度只能是 1-4")

    if month is not None:
        raise HTTPException(
            status_code=400,
            detail="当前仅支持年度目标和季度目标，不支持单独维护月度目标",
        )

    same_scope_targets = await _load_same_scope_targets(
        db,
        target_type=payload["target_type"],
        year=payload["year"],
        channel_id=payload.get("channel_id"),
        user_id=payload.get("user_id"),
        exclude_id=exclude_id,
    )
    annual_target, quarterly_targets, _monthly_targets = _classify_targets(same_scope_targets)

    if _is_annual_target(quarter=quarter, month=month):
        if annual_target is not None:
            raise HTTPException(status_code=400, detail="同一主体同一年只能有一个年目标")

        _validate_annual_metrics_against_children(
            annual_values=payload,
            quarterly_targets=quarterly_targets,
        )
        return

    if not _is_quarterly_target(quarter=quarter, month=month):
        raise HTTPException(
            status_code=400,
            detail="目标层级无效，仅支持年度目标或季度目标",
        )

    if annual_target is None:
        raise HTTPException(
            status_code=400,
            detail="请先创建年目标，再创建季度目标",
        )

    _validate_quarterly_metrics(
        annual_target=annual_target,
        quarterly_targets=quarterly_targets,
        current_quarter=quarter,
        current_values=payload,
    )


@router.get("/", response_model=List[UnifiedTargetRead])
async def list_unified_targets(
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    month: Optional[int] = None,
    channel_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UnifiedTarget).options(
        selectinload(UnifiedTarget.channel),
        selectinload(UnifiedTarget.user),
    )

    if year:
        stmt = stmt.where(UnifiedTarget.year == year)
    if quarter is not None:
        stmt = stmt.where(UnifiedTarget.quarter == quarter)
    if month is not None:
        stmt = stmt.where(UnifiedTarget.month == month)
    if channel_id:
        stmt = stmt.where(UnifiedTarget.channel_id == channel_id)
    if user_id:
        stmt = stmt.where(UnifiedTarget.user_id == user_id)

    principal = build_principal(current_user)
    stmt = await policy_service.scope_query(
        resource="unified_target",
        action="list",
        principal=principal,
        db=db,
        query=stmt,
        model=UnifiedTarget,
    )

    result = await db.execute(stmt)
    targets = result.scalars().all()

    return [_serialize_unified_target(target) for target in targets]


@router.post("/", response_model=UnifiedTargetRead)
async def create_unified_target(
    target: UnifiedTargetCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)

    # Check create permission
    await policy_service.authorize_create(
        resource="unified_target",
        principal=principal,
        db=db,
        payload=target,
    )

    # Validate: channel exists if channel_id provided
    if target.channel_id is not None:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == target.channel_id)
        )
        if not channel_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel not found")

    # Validate: user exists if user_id provided
    if target.user_id is not None:
        user_result = await db.execute(select(User).where(User.id == target.user_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User not found")

    await _validate_unified_target_payload(
        db,
        payload=target.model_dump(),
    )

    new_target = UnifiedTarget(
        target_type=target.target_type,
        channel_id=target.channel_id,
        user_id=target.user_id,
        year=target.year,
        quarter=target.quarter,
        month=target.month,
        performance_target=target.performance_target,
        opportunity_target=target.opportunity_target,
        project_count_target=target.project_count_target,
        development_goal=target.development_goal,
        created_at=datetime.now(),
        created_by=principal.user_id,
    )
    db.add(new_target)
    await db.flush()
    await db.refresh(new_target)

    await log_create(
        db=db,
        user_id=principal.user_id,
        user_name=principal.name,
        entity_type="unified_target",
        entity_id=new_target.id,
        entity_code=f"TARGET-{new_target.id}",
        entity_name=f"{target.target_type.value} target {new_target.year}",
        description=f"创建统一目标: {target.target_type.value} {new_target.year}",
        ip_address=request.client.host if request.client else None,
    )

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _translate_target_integrity_error(exc)

    result = await db.execute(
        select(UnifiedTarget)
        .options(
            selectinload(UnifiedTarget.channel),
            selectinload(UnifiedTarget.user),
        )
        .where(UnifiedTarget.id == new_target.id)
    )
    created_target = result.scalar_one()
    return _serialize_unified_target(created_target)


@router.get("/{target_id}", response_model=UnifiedTargetRead)
async def get_unified_target(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(UnifiedTarget)
        .where(UnifiedTarget.id == target_id)
        .options(
            selectinload(UnifiedTarget.channel),
            selectinload(UnifiedTarget.user),
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    # Check read permission using policy
    await policy_service.authorize(
        resource="unified_target",
        action="read",
        principal=principal,
        db=db,
        obj=target,
    )

    return _serialize_unified_target(target)


@router.put("/{target_id}", response_model=UnifiedTargetRead)
async def update_unified_target(
    target_id: int,
    target: UnifiedTargetUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)

    # Check update permission using policy
    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Unified target not found")

    await policy_service.authorize(
        resource="unified_target",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    # Validate: channel exists if channel_id provided
    if target.channel_id is not None:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == target.channel_id)
        )
        if not channel_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel not found")

    # Validate: user exists if user_id provided
    if target.user_id is not None:
        user_result = await db.execute(select(User).where(User.id == target.user_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User not found")

    update_data = target.model_dump(exclude_unset=True)
    merged_payload = {
        "target_type": existing.target_type,
        "channel_id": existing.channel_id,
        "user_id": existing.user_id,
        "year": existing.year,
        "quarter": existing.quarter,
        "month": existing.month,
        "performance_target": existing.performance_target,
        "opportunity_target": existing.opportunity_target,
        "project_count_target": existing.project_count_target,
        "development_goal": existing.development_goal,
    }
    merged_payload.update(update_data)

    await _validate_unified_target_payload(
        db,
        payload=merged_payload,
        exclude_id=existing.id,
    )

    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.flush()

    await log_update(
        db=db,
        user_id=principal.user_id,
        user_name=principal.name,
        entity_type="unified_target",
        entity_id=existing.id,
        entity_code=f"TARGET-{existing.id}",
        entity_name=f"{existing.target_type.value} target {existing.year}",
        description=f"更新统一目标: {existing.target_type.value} {existing.year}",
        ip_address=request.client.host if request.client else None,
    )

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _translate_target_integrity_error(exc)

    result = await db.execute(
        select(UnifiedTarget)
        .options(
            selectinload(UnifiedTarget.channel),
            selectinload(UnifiedTarget.user),
        )
        .where(UnifiedTarget.id == existing.id)
    )
    updated_target = result.scalar_one()
    return _serialize_unified_target(updated_target)


@router.delete("/{target_id}")
async def delete_unified_target(
    target_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    # Check delete permission using policy
    await policy_service.authorize(
        resource="unified_target",
        action="delete",
        principal=principal,
        db=db,
        obj=target,
    )

    same_scope_targets = await _load_same_scope_targets(
        db,
        target_type=target.target_type,
        year=target.year,
        channel_id=target.channel_id,
        user_id=target.user_id,
        exclude_id=target.id,
    )
    _annual_target, quarterly_targets, monthly_targets = _classify_targets(
        same_scope_targets
    )

    if _is_annual_target(quarter=target.quarter, month=target.month) and (
        quarterly_targets or monthly_targets
    ):
        raise HTTPException(
            status_code=400,
            detail="请先删除该年目标下的季度目标，再删除年目标",
        )

    await log_delete(
        db=db,
        user_id=principal.user_id,
        user_name=principal.name,
        entity_type="unified_target",
        entity_id=target.id,
        entity_code=f"TARGET-{target.id}",
        entity_name=f"{target.target_type.value} target {target.year}",
        description=f"删除统一目标: {target.target_type.value} {target.year}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(target)
    await db.commit()
    return {"message": "Unified target deleted successfully"}


@router.post("/{target_id}/calculate")
async def calculate_target_achievement(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    # Check read permission using policy
    await policy_service.authorize(
        resource="unified_target",
        action="read",
        principal=principal,
        db=db,
        obj=target,
    )

    # TODO: Implement achievement calculation from related projects/opportunities
    # For now, return a stub response
    return {
        "target_id": target_id,
        "message": "Achievement calculation not yet implemented",
    }
