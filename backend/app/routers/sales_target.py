from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.sales_target import SalesTarget
from app.schemas.sales_target import (
    QuarterDecomposeRequest,
    SalesTargetCreate,
    SalesTargetRead,
    SalesTargetUpdate,
)


router = APIRouter(prefix="/sales-targets", tags=["sales_targets"])


@router.get("/", response_model=List[SalesTargetRead])
async def get_sales_targets(
    year: Optional[int] = None,
    target_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SalesTarget)
    if year:
        query = query.where(SalesTarget.target_year == year)
    if target_type:
        query = query.where(SalesTarget.target_type == target_type)
    if user_id:
        query = query.where(SalesTarget.user_id == user_id)
    if current_user["role"] != "admin":
        query = query.where(SalesTarget.user_id == current_user["id"])
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/year", response_model=SalesTargetRead)
async def create_year_target(
    target: SalesTargetCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(
        select(SalesTarget).where(
            SalesTarget.user_id == target.user_id,
            SalesTarget.target_type == "yearly",
            SalesTarget.target_year == target.target_year,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="该用户此年度目标已存在")

    new_target = SalesTarget(
        user_id=target.user_id,
        target_type="yearly",
        target_year=target.target_year,
        target_period=1,
        target_amount=target.target_amount,
        created_at=date.today(),
    )
    db.add(new_target)
    await db.commit()
    await db.refresh(new_target)
    return new_target


@router.post("/{target_id}/decompose-quarterly")
async def decompose_yearly_to_quarterly(
    target_id: int,
    request: QuarterDecomposeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    year_target_result = await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )
    year_target = year_target_result.scalars().first()
    if not year_target or year_target.target_type != "yearly":
        raise HTTPException(status_code=404, detail="年目标不存在")

    total = request.q1 + request.q2 + request.q3 + request.q4
    if abs(total - year_target.target_amount) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"季度目标总和({total})必须等于年目标({year_target.target_amount})",
        )

    existing_quarters = await db.execute(
        select(SalesTarget).where(
            SalesTarget.parent_id == target_id,
            SalesTarget.target_type == "quarterly",
        )
    )
    if existing_quarters.scalars().first():
        raise HTTPException(status_code=400, detail="该年目标已分解过季度目标")

    quarters = [
        (1, request.q1),
        (2, request.q2),
        (3, request.q3),
        (4, request.q4),
    ]

    created_targets = []
    for q_num, q_amount in quarters:
        q_target = SalesTarget(
            user_id=year_target.user_id,
            target_type="quarterly",
            target_year=year_target.target_year,
            target_period=q_num,
            target_amount=q_amount,
            parent_id=year_target.id,
            created_at=date.today(),
        )
        db.add(q_target)
        await db.flush()

        m_amount = round(q_amount / 3, 2)
        start_month = (q_num - 1) * 3 + 1
        for m_offset in range(3):
            m_target = SalesTarget(
                user_id=year_target.user_id,
                target_type="monthly",
                target_year=year_target.target_year,
                target_period=start_month + m_offset,
                target_amount=m_amount,
                parent_id=q_target.id,
                created_at=date.today(),
            )
            db.add(m_target)

        created_targets.append(q_target)

    await db.commit()
    return {
        "success": True,
        "created_quarterly": len(created_targets),
        "created_monthly": len(created_targets) * 3,
    }


@router.get("/{target_id}/children")
async def get_target_children(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    children_result = await db.execute(
        select(SalesTarget)
        .where(SalesTarget.parent_id == target_id)
        .order_by(SalesTarget.target_period)
    )
    children = children_result.scalars().all()

    return {
        "parent": {
            "id": target.id,
            "target_type": target.target_type,
            "target_amount": target.target_amount,
        },
        "children": [
            {
                "id": c.id,
                "target_type": c.target_type,
                "target_period": c.target_period,
                "target_amount": c.target_amount,
                "has_children": c.target_type == "quarterly",
            }
            for c in children
        ],
    }


@router.get("/yearly-with-status")
async def get_yearly_targets_with_status(
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SalesTarget).where(SalesTarget.target_type == "yearly")
    if year:
        query = query.where(SalesTarget.target_year == year)
    if current_user["role"] != "admin":
        query = query.where(SalesTarget.user_id == current_user["id"])
    result = await db.execute(query)
    year_targets = result.scalars().all()

    response = []
    for yt in year_targets:
        children_result = await db.execute(
            select(SalesTarget).where(SalesTarget.parent_id == yt.id)
        )
        children = children_result.scalars().all()
        response.append(
            {
                "id": yt.id,
                "user_id": yt.user_id,
                "target_year": yt.target_year,
                "target_amount": yt.target_amount,
                "decomposed": len(children) > 0,
                "quarterly_count": len(
                    [c for c in children if c.target_type == "quarterly"]
                ),
                "monthly_count": len(
                    [c for c in children if c.target_type == "monthly"]
                ),
                "created_at": str(yt.created_at) if yt.created_at else None,
            }
        )
    return response


@router.put("/{target_id}", response_model=SalesTargetRead)
async def update_sales_target(
    target_id: int,
    target: SalesTargetUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    db_target = existing.scalars().first()
    if not db_target:
        raise HTTPException(status_code=404, detail="目标不存在")

    db_target.target_amount = target.target_amount
    db_target.updated_at = str(date.today())

    await db.commit()
    await db.refresh(db_target)
    return db_target


@router.delete("/{target_id}")
async def delete_sales_target(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    db_target = existing.scalars().first()
    if not db_target:
        raise HTTPException(status_code=404, detail="目标不存在")

    await db.delete(db_target)
    await db.commit()
    return {"success": True}
