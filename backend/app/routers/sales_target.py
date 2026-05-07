from datetime import date as date_cls
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import build_principal, policy_service
from app.database import get_db
from app.models.sales_target import SalesTarget
from app.models.actual_performance import ActualPerformance
from app.schemas.sales_target import (
    SalesTargetCreate,
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


@router.get("/", response_model=List[SalesTargetRead])
async def list_targets(
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
    result = await db.execute(query)
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
    """部分拆分。至少拆分一个季度；季度下至少拆分一个月。"""
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

    sum_q = sum(request.quarters.values())
    sum_q_gp = sum(request.quarters_gp.values())
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
    if not request.quarters:
        raise HTTPException(status_code=400, detail="至少拆分一个季度")

    created_q = []
    for q_num in sorted(request.quarters.keys()):
        q_amt = request.quarters[q_num]
        q_gp = request.quarters_gp.get(q_num, 0.0)

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

        months_req = request.months_by_quarter.get(q_num, {})
        months_gp_req = request.months_gp_by_quarter.get(q_num, {})

        m_sum = sum(months_req.values())
        m_sum_gp = sum(months_gp_req.values())
        if months_req and (m_sum > q_amt + 0.01 or m_sum_gp > q_gp + 0.01):
            raise HTTPException(
                status_code=400,
                detail=f"Q{q_num} 月度合计超出季度目标",
            )
        if months_req and not months_req:
            pass

        for m_num in sorted(months_req.keys()) if months_req else []:
            m_t = SalesTarget(
                user_id=year_target.user_id,
                target_type="monthly",
                target_year=year_target.target_year,
                target_period=m_num,
                target_amount=months_req[m_num],
                gross_profit_target=months_gp_req.get(m_num, 0.0),
                parent_id=q_t.id,
                created_at=date_cls.today(),
            )
            db.add(m_t)
        created_q.append(q_t)

    await db.commit()
    return {"success": True, "created_quarters": len(created_q)}


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
    year: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按月/季/年聚合实际业绩"""
    principal = build_principal(current_user)
    user_filter = []
    if user_id:
        user_filter.append(ActualPerformance.user_id == user_id)
    if year:
        user_filter.append(ActualPerformance.year == year)
    if principal.role != "admin":
        user_filter.append(ActualPerformance.user_id == principal.user_id)

    if user_filter:
        from sqlalchemy import and_
        query: Any = select(
            ActualPerformance.year,
            ActualPerformance.month,
            ActualPerformance.user_id,
        ).where(and_(*user_filter))
    else:
        query: Any = select(
            ActualPerformance.year,
            ActualPerformance.month,
            ActualPerformance.user_id,
        )

    rows = (await db.execute(query)).all()
    return [
        {"year": r.year, "month": r.month, "user_id": r.user_id}
        for r in rows
    ]


@router.post("/actual/", response_model=ActualPerformanceRead)
async def create_actual(
    data: ActualPerformanceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    uid = data.user_id if hasattr(data, "user_id") and data.user_id else principal.user_id
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
