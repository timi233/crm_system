from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.policy import policy_service, build_principal
from app.models.opportunity import Opportunity
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
)
from app.services.auto_number_service import generate_code
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_stage_change,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

# 商机阶段流转规则
OPPORTUNITY_STAGE_TRANSITIONS = {
    "需求方案": ["需求确认", "已流失"],
    "需求确认": ["报价投标", "需求方案", "已流失"],
    "报价投标": ["合同签订", "需求确认", "已流失"],
    "合同签订": ["已成交"],
    "已成交": [],
    "已流失": [],
}


@router.get("/", response_model=List[OpportunityRead])
async def list_opportunities(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    query = select(Opportunity).options(
        selectinload(Opportunity.terminal_customer),
        selectinload(Opportunity.sales_owner),
        selectinload(Opportunity.channel),
    )
    query = await policy_service.scope_query(
        resource="opportunity",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=Opportunity,
    )

    result = await db.execute(query)
    opportunities = result.scalars().all()

    # 手动填充名称字段
    opp_reads = []
    for opp in opportunities:
        opp_dict = {
            "id": opp.id,
            "opportunity_code": opp.opportunity_code,
            "opportunity_name": opp.opportunity_name,
            "terminal_customer_id": opp.terminal_customer_id,
            "terminal_customer_name": opp.terminal_customer.customer_name
            if opp.terminal_customer
            else None,
            "opportunity_source": opp.opportunity_source,
            "opportunity_stage": opp.opportunity_stage,
            "products": opp.products,
            "expected_contract_amount": opp.expected_contract_amount,
            "expected_close_date": opp.expected_close_date,
            "sales_owner_id": opp.sales_owner_id,
            "sales_owner_name": opp.sales_owner.name if opp.sales_owner else None,
            "channel_id": opp.channel_id,
            "channel_name": opp.channel.company_name if opp.channel else None,
            "project_id": opp.project_id,
            "loss_reason": opp.loss_reason,
            "created_at": opp.created_at,
        }
        opp_reads.append(opp_dict)
    return opp_reads


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.terminal_customer),
            selectinload(Opportunity.sales_owner),
            selectinload(Opportunity.channel),
        )
    )
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

    return {
        **opportunity.__dict__,
        "terminal_customer_name": opportunity.terminal_customer.customer_name
        if opportunity.terminal_customer
        else None,
        "sales_owner_name": opportunity.sales_owner.name
        if opportunity.sales_owner
        else None,
        "channel_name": opportunity.channel.company_name
        if opportunity.channel
        else None,
    }


@router.post("/", response_model=OpportunityRead)
async def create_opportunity(
    opportunity: OpportunityCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    await policy_service.authorize_create(
        resource="opportunity",
        principal=principal,
        db=db,
        payload=opportunity,
    )

    opportunity_code = await generate_code(db, "opportunity")

    new_opportunity = Opportunity(
        opportunity_code=opportunity_code,
        opportunity_name=opportunity.opportunity_name,
        terminal_customer_id=opportunity.terminal_customer_id,
        opportunity_source=opportunity.opportunity_source,
        opportunity_stage=opportunity.opportunity_stage,
        expected_contract_amount=opportunity.expected_contract_amount,
        expected_close_date=opportunity.expected_close_date,
        sales_owner_id=opportunity.sales_owner_id,
        channel_id=opportunity.channel_id,
        vendor_registration_status=opportunity.vendor_registration_status,
        vendor_discount=opportunity.vendor_discount,
        loss_reason=opportunity.loss_reason,
        product_ids=opportunity.product_ids,
        created_at=datetime.now().date(),
    )
    db.add(new_opportunity)
    await db.flush()
    await db.refresh(new_opportunity)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="opportunity",
        entity_id=new_opportunity.id,
        entity_code=new_opportunity.opportunity_code,
        entity_name=new_opportunity.opportunity_name,
        description=f"创建商机: {new_opportunity.opportunity_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return new_opportunity


@router.put("/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: int,
    opportunity: OpportunityUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await policy_service.authorize(
        resource="opportunity",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    if existing.opportunity_stage in ["已成交", "已流失"]:
        raise HTTPException(status_code=400, detail="已成交或已流失的商机不能修改")

    old_stage = existing.opportunity_stage
    update_data = opportunity.model_dump(exclude_unset=True)

    if (
        "opportunity_stage" in update_data
        and update_data["opportunity_stage"] != existing.opportunity_stage
    ):
        valid_transitions = OPPORTUNITY_STAGE_TRANSITIONS.get(
            existing.opportunity_stage, []
        )
        if update_data["opportunity_stage"] not in valid_transitions:
            raise HTTPException(
                status_code=400,
                detail=f"商机阶段不能从 '{existing.opportunity_stage}' 直接流转到 '{update_data['opportunity_stage']}'",
            )

        if (
            update_data["opportunity_stage"] == "已流失"
            and not update_data.get("loss_reason")
            and not existing.loss_reason
        ):
            raise HTTPException(status_code=400, detail="转入流失阶段必须填写流失原因")

    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.flush()

    if (
        "opportunity_stage" in update_data
        and update_data["opportunity_stage"] != old_stage
    ):
        await log_stage_change(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="opportunity",
            entity_id=existing.id,
            entity_code=existing.opportunity_code,
            entity_name=existing.opportunity_name,
            old_stage=old_stage,
            new_stage=update_data["opportunity_stage"],
            ip_address=request.client.host if request.client else None,
        )
    else:
        await log_update(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="opportunity",
            entity_id=existing.id,
            entity_code=existing.opportunity_code,
            entity_name=existing.opportunity_name,
            description=f"更新商机: {existing.opportunity_name}",
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await policy_service.authorize(
        resource="opportunity",
        action="delete",
        principal=principal,
        db=db,
        obj=existing,
    )

    await db.delete(existing)
    await db.commit()
    return {"message": "Opportunity deleted successfully"}
