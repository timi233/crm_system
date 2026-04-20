from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.opportunity import Opportunity
from app.models.nine_a import NineA
from app.models.nine_a_version import NineAVersion
from app.models.user import User
from app.schemas.nine_a import NineACreate, NineAUpdate, NineARead, NineAVersionRead

router = APIRouter(tags=["nine_a"])


@router.get(
    "/opportunities/{opportunity_id}/nine-a", response_model=Optional[NineARead]
)
async def get_nine_a(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    user_role = current_user.get("role")
    user_id = current_user["id"]
    if user_role not in ["admin", "business"]:
        if user_role == "sales" and opportunity.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此商机")

    result = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    nine_a = result.scalar_one_or_none()
    return nine_a


@router.get(
    "/opportunities/{opportunity_id}/nine-a/versions",
    response_model=List[NineAVersionRead],
)
async def get_nine_a_versions(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    user_role = current_user.get("role")
    user_id = current_user["id"]
    if user_role not in ["admin", "business"]:
        if user_role == "sales" and opportunity.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此商机")

    result = await db.execute(
        select(NineAVersion)
        .where(NineAVersion.opportunity_id == opportunity_id)
        .options(selectinload(NineAVersion.created_by))
        .order_by(NineAVersion.version_number.desc())
    )
    versions = result.scalars().all()

    version_reads = []
    for v in versions:
        version_reads.append(
            {
                "id": v.id,
                "opportunity_id": v.opportunity_id,
                "version_number": v.version_number,
                "key_events": v.key_events,
                "budget": float(v.budget) if v.budget else None,
                "decision_chain_influence": v.decision_chain_influence,
                "customer_challenges": v.customer_challenges,
                "customer_needs": v.customer_needs,
                "solution_differentiation": v.solution_differentiation,
                "competitors": v.competitors,
                "buying_method": v.buying_method,
                "close_date": v.close_date,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by_name": v.created_by.name if v.created_by else None,
            }
        )
    return version_reads


@router.post("/opportunities/{opportunity_id}/nine-a", response_model=NineARead)
async def create_nine_a(
    opportunity_id: int,
    data: NineACreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    user_role = current_user.get("role")
    user_id = current_user["id"]
    if user_role not in ["admin", "business"]:
        if user_role == "sales" and opportunity.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此商机")

    result = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="此商机已有九A分析")

    new_nine_a = NineA(
        opportunity_id=opportunity_id,
        key_events=data.key_events,
        budget=data.budget,
        decision_chain_influence=data.decision_chain_influence,
        customer_challenges=data.customer_challenges,
        customer_needs=data.customer_needs,
        solution_differentiation=data.solution_differentiation,
        competitors=data.competitors,
        buying_method=data.buying_method,
        close_date=data.close_date,
    )
    db.add(new_nine_a)

    version_result = await db.execute(
        select(NineAVersion)
        .where(NineAVersion.opportunity_id == opportunity_id)
        .order_by(NineAVersion.version_number.desc())
    )
    latest_version = version_result.scalar_one_or_none()
    next_version = (latest_version.version_number + 1) if latest_version else 1

    new_version = NineAVersion(
        opportunity_id=opportunity_id,
        version_number=next_version,
        key_events=data.key_events,
        budget=data.budget,
        decision_chain_influence=data.decision_chain_influence,
        customer_challenges=data.customer_challenges,
        customer_needs=data.customer_needs,
        solution_differentiation=data.solution_differentiation,
        competitors=data.competitors,
        buying_method=data.buying_method,
        close_date=data.close_date,
        created_by_id=user_id,
    )
    db.add(new_version)

    await db.commit()
    await db.refresh(new_nine_a)
    return new_nine_a


@router.put("/opportunities/{opportunity_id}/nine-a", response_model=NineARead)
async def update_nine_a(
    opportunity_id: int,
    data: NineAUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    user_role = current_user.get("role")
    user_id = current_user["id"]
    if user_role not in ["admin", "business"]:
        if user_role == "sales" and opportunity.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此商机")

    result = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    nine_a = result.scalar_one_or_none()
    if not nine_a:
        new_nine_a = NineA(
            opportunity_id=opportunity_id,
            key_events=data.key_events,
            budget=data.budget,
            decision_chain_influence=data.decision_chain_influence,
            customer_challenges=data.customer_challenges,
            customer_needs=data.customer_needs,
            solution_differentiation=data.solution_differentiation,
            competitors=data.competitors,
            buying_method=data.buying_method,
            close_date=data.close_date,
        )
        db.add(new_nine_a)
    else:
        nine_a.key_events = data.key_events
        nine_a.budget = data.budget
        nine_a.decision_chain_influence = data.decision_chain_influence
        nine_a.customer_challenges = data.customer_challenges
        nine_a.customer_needs = data.customer_needs
        nine_a.solution_differentiation = data.solution_differentiation
        nine_a.competitors = data.competitors
        nine_a.buying_method = data.buying_method
        nine_a.close_date = data.close_date

    version_result = await db.execute(
        select(NineAVersion)
        .where(NineAVersion.opportunity_id == opportunity_id)
        .order_by(NineAVersion.version_number.desc())
    )
    latest_version = version_result.scalar_one_or_none()
    next_version = (latest_version.version_number + 1) if latest_version else 1

    new_version = NineAVersion(
        opportunity_id=opportunity_id,
        version_number=next_version,
        key_events=data.key_events,
        budget=data.budget,
        decision_chain_influence=data.decision_chain_influence,
        customer_challenges=data.customer_challenges,
        customer_needs=data.customer_needs,
        solution_differentiation=data.solution_differentiation,
        competitors=data.competitors,
        buying_method=data.buying_method,
        close_date=data.close_date,
        created_by_id=user_id,
    )
    db.add(new_version)

    await db.commit()
    if nine_a:
        await db.refresh(nine_a)
        return nine_a
    else:
        await db.refresh(new_nine_a)
        return new_nine_a
