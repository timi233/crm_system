from datetime import date as date_cls
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import build_principal, policy_service
from app.database import get_db
from app.models.sales_target import SalesTarget
from app.models.actual_performance import ActualPerformance
from app.schemas.sales_target import (
    SalesTargetCreate,
    SalesTargetUpdate,
    SalesTargetRead,
    QuarterlyDecomposeRequest,
    ActualPerformanceCreate,
    ActualPerformanceUpdate,
    ActualPerformanceRead,
)

router = APIRouter(prefix="/sales-targets", tags=["sales_targets"])


async def _remaining(db: AsyncSession, parent_id: int) -> tuple[float, float]:
    """计算父级目标下已分配的子级总和，返回 (剩余营收, 剩余毛利)"""
    result = await db.execute(
        select(SalesTarget).where(SalesTarget.parent_id == parent_id)
    )
    children = result.scalars().all()
    rev_sum = sum(float(c.target_amount or 0) for c in children)
    gp_sum = sum(float(c.gross_profit_target or 0) for c in children)

    parent_result = await db.execute(
        select(SalesTarget).where(SalesTarget.id == parent_id)
    )
    parent = parent_result.scalar_one_or_none()
    if not parent:
        return 0.0, 0.0

    return (
        round(float(parent.target_amount or 0) - rev_sum, 2),
        round(float(parent.gross_profit_target or 0) - gp_sum, 2),
    )


async def _validate_actual_target(
    db: AsyncSession,
    target_id: int,
    *,
    user_id: int,
    year: int,
    month: int,
) -> None:
    target = await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )
    t = target.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=400, detail="目标不存在")
    if t.target_type != "monthly":
        raise HTTPException(status_code=400, detail="只能关联月度目标")
    if t.target_year != year:
        raise HTTPException(status_code=400, detail="年月与目标不匹配")
    if t.target_period != month:
        raise HTTPException(status_code=400, detail="月份与目标不匹配")
    if t.user_id != user_id:
        raise HTTPException(status_code=400, detail="目标归属与填报人不一致")


@router.get("/", response_model=List[SalesTargetRead])
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    target_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query: Any = select(SalesTarget)
    if year:
        query = query.where(SalesTarget.target_year == year)
    if target_type:
        query = query.where(SalesTarget.target_type == target_type)
    if user_id:
        query = query.where(SalesTarget.user_id == user_id)

    query = await policy_service.scope_query(
        resource="sales_target",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=SalesTarget,
    )
    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()

    response: list = []
    for item in items:
        rem_rev, rem_gp = 0.0, 0.0
        if item.target_type in ("yearly", "quarterly"):
            rem_rev, rem_gp = await _remaining(db, item.id)
        response.append(
            SalesTargetRead(
                id=item.id,
                user_id=item.user_id,
                target_type=item.target_type,
                target_year=item.target_year,
                target_period=item.target_period,
                target_amount=item.target_amount,
                gross_profit_target=item.gross_profit_target or 0.0,
                parent_id=item.parent_id,
                remaining_rev=rem_rev,
                remaining_gp=rem_gp,
                created_at=str(item.created_at) if item.created_at else None,
                updated_at=str(item.updated_at) if item.updated_at else None,
            )
        )
    return response


@router.get("/tree")
async def tree_targets(
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """树形结构，带完成度"""
    principal = build_principal(current_user)
    query = select(SalesTarget).where(SalesTarget.target_type == "yearly")
    if year:
        query = query.where(SalesTarget.target_year == year)
    query = await policy_service.scope_query(
        resource="sales_target", action="list", principal=principal,
        db=db, query=query, model=SalesTarget,
    )
    years = (await db.execute(query)).scalars().all()

    payload = []
    for y in years:
        rem_rev, rem_gp = await _remaining(db, y.id)
        quarters_r = (await db.execute(
            select(SalesTarget).where(
                SalesTarget.parent_id == y.id, SalesTarget.target_type == "quarterly"
            )
        )).scalars().all()

        quarter_nodes = []
        for q in quarters_r:
            q_rem_rev, q_rem_gp = await _remaining(db, q.id)
            months = (await db.execute(
                select(SalesTarget).where(
                    SalesTarget.parent_id == q.id, SalesTarget.target_type == "monthly"
                )
            )).scalars().all()

            month_nodes = []
            for m in months:
                m_rem_rev, m_rem_gp = await _remaining(db, m.id)
                month_nodes.append({
                    "id": m.id,
                    "period": m.target_period,
                    "target_amount": m.target_amount,
                    "gross_profit_target": m.gross_profit_target or 0.0,
                    "remaining_rev": m_rem_rev,
                    "remaining_gp": m_rem_gp,
                })

            quarter_nodes.append({
                "id": q.id,
                "period": q.target_period,
                "target_amount": q.target_amount,
                "gross_profit_target": q.gross_profit_target or 0.0,
                "remaining_rev": q_rem_rev,
                "remaining_gp": q_rem_gp,
                "months": month_nodes,
            })

        payload.append({
            "id": y.id,
            "user_id": y.user_id,
            "target_year": y.target_year,
            "target_amount": y.target_amount,
            "gross_profit_target": y.gross_profit_target or 0.0,
            "remaining_rev": rem_rev,
            "remaining_gp": rem_gp,
            "quarters": quarter_nodes,
        })
    return payload


@router.post("/year", response_model=SalesTargetRead)
async def create_year(
    target: SalesTargetCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="sales_target", principal=principal, db=db, payload=target,
    )

    existing = await db.execute(
        select(SalesTarget).where(
            SalesTarget.user_id == target.user_id,
            SalesTarget.target_type == "yearly",
            SalesTarget.target_year == target.target_year,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户此年度目标已存在")

    new_target = SalesTarget(
        user_id=target.user_id,
        target_type="yearly",
        target_year=target.target_year,
        target_period=1,
        target_amount=target.target_amount,
        gross_profit_target=target.gross_profit_target,
        created_at=date_cls.today(),
    )
    db.add(new_target)
    await db.commit()
    await db.refresh(new_target)

    rem_rev, rem_gp = await _remaining(db, new_target.id)
    return SalesTargetRead(
        id=new_target.id,
        user_id=new_target.user_id,
        target_type=new_target.target_type,
        target_year=new_target.target_year,
        target_period=new_target.target_period,
        target_amount=new_target.target_amount,
        gross_profit_target=new_target.gross_profit_target or 0.0,
        parent_id=new_target.parent_id,
        remaining_rev=rem_rev,
        remaining_gp=rem_gp,
        created_at=str(new_target.created_at),
    )


@router.post("/{target_id}/decompose/")
async def decompose(
    target_id: int,
    request: QuarterlyDecomposeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """幂等拆分：已存在的季度/月度更新金额，不存在则创建"""
    year_r = await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )
    year_target = year_r.scalar_one_or_none()
    if not year_target or year_target.target_type != "yearly":
        raise HTTPException(status_code=404, detail="年目标不存在")

    await policy_service.authorize(
        resource="sales_target",
        action="update",
        principal=build_principal(current_user),
        db=db,
        obj=year_target,
    )

    requested_quarters = set(request.quarters.keys())
    extra_quarter_gp = set(request.quarters_gp.keys()) - requested_quarters
    if extra_quarter_gp:
        raise HTTPException(
            status_code=400,
            detail=f"季度毛利包含未提交营收目标的季度: {sorted(extra_quarter_gp)}",
        )
    extra_month_quarters = (
        set(request.months_by_quarter.keys()) | set(request.months_gp_by_quarter.keys())
    ) - requested_quarters
    if extra_month_quarters:
        raise HTTPException(
            status_code=400,
            detail=f"月度拆分必须包含对应季度目标: {sorted(extra_month_quarters)}",
        )

    for q_num in requested_quarters:
        if q_num not in {1, 2, 3, 4}:
            raise HTTPException(status_code=400, detail=f"季度编号{q_num}无效，必须为1-4")

    if not request.quarters:
        raise HTTPException(status_code=400, detail="至少拆分一个季度")

    existing_quarters = (await db.execute(
        select(SalesTarget).where(
            SalesTarget.parent_id == year_target.id,
            SalesTarget.target_type == "quarterly",
        )
    )).scalars().all()
    quarter_by_period = {q.target_period: q for q in existing_quarters}
    quarter_amounts = {
        q.target_period: float(q.target_amount or 0) for q in existing_quarters
    }
    quarter_gp_amounts = {
        q.target_period: float(q.gross_profit_target or 0) for q in existing_quarters
    }

    for q_num, q_amt in request.quarters.items():
        quarter_amounts[q_num] = float(q_amt)
        if q_num in request.quarters_gp:
            quarter_gp_amounts[q_num] = float(request.quarters_gp[q_num])
        elif q_num not in quarter_gp_amounts:
            quarter_gp_amounts[q_num] = 0.0

    sum_q = sum(quarter_amounts.values())
    sum_q_gp = sum(quarter_gp_amounts.values())
    if sum_q > year_target.target_amount + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"季度营收合计({sum_q})超出年目标({year_target.target_amount})",
        )
    if sum_q_gp > (year_target.gross_profit_target or 0) + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"季度毛利合计({sum_q_gp})超出年毛利目标({year_target.gross_profit_target or 0})",
        )
    created_q = 0
    updated_q = 0
    created_m = 0
    updated_m = 0

    for q_num in sorted(request.quarters.keys()):
        q_amt = request.quarters[q_num]
        q_gp = quarter_gp_amounts.get(q_num, 0.0)

        q_t = quarter_by_period.get(q_num)

        if q_t:
            q_t.target_amount = q_amt
            q_t.gross_profit_target = q_gp
            updated_q += 1
        else:
            q_t = SalesTarget(
                user_id=year_target.user_id,
                target_type="quarterly",
                target_year=year_target.target_year,
                target_period=q_num,
                target_amount=q_amt,
                gross_profit_target=q_gp,
                parent_id=year_target.id,
                created_at=date_cls.today(),
            )
            db.add(q_t)
            await db.flush()
            created_q += 1

        months_req = request.months_by_quarter.get(q_num, {})
        months_gp_req = request.months_gp_by_quarter.get(q_num, {})
        extra_month_gp = set(months_gp_req.keys()) - set(months_req.keys())
        if extra_month_gp:
            raise HTTPException(
                status_code=400,
                detail=f"Q{q_num}月度毛利包含未提交营收目标的月份: {sorted(extra_month_gp)}",
            )

        existing_months = (await db.execute(
            select(SalesTarget).where(
                SalesTarget.parent_id == q_t.id,
                SalesTarget.target_type == "monthly",
            )
        )).scalars().all()
        month_by_period = {m.target_period: m for m in existing_months}

        valid_months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
        for m_num in months_req.keys():
            if m_num not in valid_months[q_num]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Q{q_num}月份{m_num}无效，应为{valid_months[q_num]}",
                )

        month_amounts = {
            m.target_period: float(m.target_amount or 0) for m in existing_months
        }
        month_gp_amounts = {
            m.target_period: float(m.gross_profit_target or 0) for m in existing_months
        }
        for m_num, m_amt in months_req.items():
            month_amounts[m_num] = float(m_amt)
            if m_num in months_gp_req:
                month_gp_amounts[m_num] = float(months_gp_req[m_num])
            elif m_num not in month_gp_amounts:
                month_gp_amounts[m_num] = 0.0

        m_sum = sum(month_amounts.values())
        m_sum_gp = sum(month_gp_amounts.values())
        if m_sum > q_amt + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Q{q_num}月度营收合计({m_sum})超出季度目标({q_amt})",
            )
        if m_sum_gp > q_gp + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Q{q_num}月度毛利合计({m_sum_gp})超出季度毛利目标({q_gp})",
            )

        if months_req:
            for m_num in sorted(months_req.keys()):
                m_t = month_by_period.get(m_num)

                if m_t:
                    m_t.target_amount = months_req[m_num]
                    m_t.gross_profit_target = month_gp_amounts.get(m_num, 0.0)
                    updated_m += 1
                else:
                    m_t = SalesTarget(
                        user_id=year_target.user_id,
                        target_type="monthly",
                        target_year=year_target.target_year,
                        target_period=m_num,
                        target_amount=months_req[m_num],
                        gross_profit_target=month_gp_amounts.get(m_num, 0.0),
                        parent_id=q_t.id,
                        created_at=date_cls.today(),
                    )
                    db.add(m_t)
                    created_m += 1

    await db.commit()
    return {
        "success": True,
        "created_quarters": created_q,
        "updated_quarters": updated_q,
        "created_months": created_m,
        "updated_months": updated_m,
    }


@router.get("/actual/", response_model=List[ActualPerformanceRead])
async def list_actual(
    user_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query: Any = select(ActualPerformance)
    if user_id:
        query = query.where(ActualPerformance.user_id == user_id)
    if year:
        query = query.where(ActualPerformance.year == year)
    if month:
        query = query.where(ActualPerformance.month == month)

    if principal.role != "admin":
        query = query.where(ActualPerformance.user_id == principal.user_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/actual/summary")
async def actual_summary(
    group_by: str = Query("month", pattern="^(month|quarter|year)$"),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    user_id: Optional[int] = Query(None, gt=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按月/季/年聚合实际业绩金额"""
    principal = build_principal(current_user)
    filters = []
    if user_id:
        filters.append(ActualPerformance.user_id == user_id)
    if year:
        filters.append(ActualPerformance.year == year)
    if principal.role != "admin":
        filters.append(ActualPerformance.user_id == principal.user_id)

    if filters:
        base_query = select(ActualPerformance).where(and_(*filters))
    else:
        base_query = select(ActualPerformance)

    rows = (await db.execute(base_query)).scalars().all()

    if group_by == "month":
        grouped = {}
        for r in rows:
            key = (r.year, r.month, r.user_id)
            if key not in grouped:
                grouped[key] = {"year": r.year, "month": r.month, "user_id": r.user_id, "amount_actual": 0.0, "gross_profit_actual": 0.0}
            grouped[key]["amount_actual"] += float(r.amount_actual or 0)
            grouped[key]["gross_profit_actual"] += float(r.gross_profit_actual or 0)
        return list(grouped.values())

    if group_by == "quarter":
        grouped = {}
        for r in rows:
            quarter = (r.month - 1) // 3 + 1
            key = (r.year, quarter, r.user_id)
            if key not in grouped:
                grouped[key] = {"year": r.year, "quarter": quarter, "user_id": r.user_id, "amount_actual": 0.0, "gross_profit_actual": 0.0}
            grouped[key]["amount_actual"] += float(r.amount_actual or 0)
            grouped[key]["gross_profit_actual"] += float(r.gross_profit_actual or 0)
        return list(grouped.values())

    if group_by == "year":
        grouped = {}
        for r in rows:
            key = (r.year, r.user_id)
            if key not in grouped:
                grouped[key] = {"year": r.year, "user_id": r.user_id, "amount_actual": 0.0, "gross_profit_actual": 0.0}
            grouped[key]["amount_actual"] += float(r.amount_actual or 0)
            grouped[key]["gross_profit_actual"] += float(r.gross_profit_actual or 0)
        return list(grouped.values())

    return []


@router.post("/actual/", response_model=ActualPerformanceRead)
async def create_actual(
    data: ActualPerformanceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    uid = data.user_id if data.user_id else principal.user_id
    if principal.role != "admin" and uid != principal.user_id:
        raise HTTPException(status_code=403, detail="只能填报自己的实际业绩")

    existing = await db.execute(
        select(ActualPerformance).where(
            ActualPerformance.user_id == uid,
            ActualPerformance.year == data.year,
            ActualPerformance.month == data.month,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该月实际业绩已存在，请使用 PUT 更新")

    if data.target_id:
        await _validate_actual_target(
            db,
            data.target_id,
            user_id=uid,
            year=data.year,
            month=data.month,
        )

    record = ActualPerformance(
        user_id=uid,
        target_id=data.target_id,
        year=data.year,
        month=data.month,
        amount_actual=data.amount_actual,
        gross_profit_actual=data.gross_profit_actual,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.put("/actual/{pid}", response_model=ActualPerformanceRead)
async def update_actual(
    pid: int, data: ActualPerformanceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    existing = await db.execute(
        select(ActualPerformance).where(ActualPerformance.id == pid)
    )
    record = existing.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if principal.role != "admin" and record.user_id != principal.user_id:
        raise HTTPException(status_code=403, detail="无权限")

    if data.target_id is not None:
        await _validate_actual_target(
            db,
            data.target_id,
            user_id=record.user_id,
            year=record.year,
            month=record.month,
        )
        record.target_id = data.target_id
    if data.amount_actual is not None:
        record.amount_actual = data.amount_actual
    if data.gross_profit_actual is not None:
        record.gross_profit_actual = data.gross_profit_actual

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/actual/{pid}")
async def delete_actual(
    pid: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    existing = await db.execute(
        select(ActualPerformance).where(ActualPerformance.id == pid)
    )
    record = existing.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if principal.role != "admin" and record.user_id != principal.user_id:
        raise HTTPException(status_code=403, detail="无权限")

    await db.delete(record)
    await db.commit()
    return {"success": True}


@router.put("/{target_id}", response_model=SalesTargetRead)
async def update_target(
    target_id: int,
    data: SalesTargetUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新任意类型目标(yearly/quarterly/monthly)，校验父子金额约束"""
    principal = build_principal(current_user)

    target = (await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    await policy_service.authorize(
        resource="sales_target",
        action="update",
        principal=principal,
        db=db,
        obj=target,
    )

    new_amount = data.target_amount if data.target_amount is not None else target.target_amount
    new_gp = data.gross_profit_target if data.gross_profit_target is not None else (target.gross_profit_target or 0)

    children = (await db.execute(
        select(SalesTarget).where(SalesTarget.parent_id == target_id)
    )).scalars().all()
    child_sum = sum(float(c.target_amount or 0) for c in children)
    child_gp_sum = sum(float(c.gross_profit_target or 0) for c in children)

    if child_sum > float(new_amount) + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"子目标营收合计({child_sum})超过新目标({new_amount})，请先调整下级目标"
        )
    if child_gp_sum > float(new_gp) + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"子目标毛利合计({child_gp_sum})超过新毛利目标({new_gp})，请先调整下级目标"
        )

    if target.parent_id:
        parent = (await db.execute(
            select(SalesTarget).where(SalesTarget.id == target.parent_id)
        )).scalar_one_or_none()
        if parent:
            siblings = (await db.execute(
                select(SalesTarget).where(
                    SalesTarget.parent_id == parent.id,
                    SalesTarget.id != target_id,
                )
            )).scalars().all()
            sibling_sum = sum(float(s.target_amount or 0) for s in siblings)
            sibling_gp_sum = sum(float(s.gross_profit_target or 0) for s in siblings)

            if sibling_sum + float(new_amount) > float(parent.target_amount) + 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"同级目标营收合计将超父目标({parent.target_amount})"
                )
            if sibling_gp_sum + float(new_gp) > float(parent.gross_profit_target or 0) + 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"同级目标毛利合计将超父毛利目标({parent.gross_profit_target or 0})"
                )

    if data.target_amount is not None:
        target.target_amount = data.target_amount
    if data.gross_profit_target is not None:
        target.gross_profit_target = data.gross_profit_target
    target.updated_at = date_cls.today()

    await db.commit()
    await db.refresh(target)

    rem_rev, rem_gp = await _remaining(db, target.id)
    return SalesTargetRead(
        id=target.id,
        user_id=target.user_id,
        target_type=target.target_type,
        target_year=target.target_year,
        target_period=target.target_period,
        target_amount=target.target_amount,
        gross_profit_target=target.gross_profit_target or 0.0,
        parent_id=target.parent_id,
        remaining_rev=rem_rev,
        remaining_gp=rem_gp,
        created_at=str(target.created_at) if target.created_at else None,
        updated_at=str(target.updated_at) if target.updated_at else None,
    )


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除任意类型目标，有子目标时禁止删除"""
    principal = build_principal(current_user)

    target = (await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    await policy_service.authorize(
        resource="sales_target",
        action="delete",
        principal=principal,
        db=db,
        obj=target,
    )

    children = (await db.execute(
        select(SalesTarget).where(SalesTarget.parent_id == target_id)
    )).scalars().all()
    if children:
        raise HTTPException(status_code=400, detail="请先删除下级目标")

    if target.target_type == "monthly":
        actuals = (await db.execute(
            select(ActualPerformance).where(ActualPerformance.target_id == target_id)
        )).scalars().all()
        if actuals:
            raise HTTPException(
                status_code=400,
                detail="月度目标已关联实际业绩，请先解除关联或删除实际业绩"
            )

    await db.delete(target)
    await db.commit()
    return {"success": True}
