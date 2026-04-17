from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.schemas.lead import LeadCreate, LeadRead, LeadUpdate, LeadConvertRequest
from app.schemas.opportunity import OpportunityRead
from app.services.auto_number_service import generate_code
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
    log_stage_change,
    log_convert,
)

router = APIRouter(prefix="/leads", tags=["leads"])

# 线索阶段流转规则
LEAD_STAGE_TRANSITIONS = {
    "初步接触": ["意向沟通"],
    "意向沟通": ["需求挖掘中", "初步接触"],
    "需求挖掘中": ["意向沟通"],
}


@router.get("/", response_model=List[LeadRead])
async def list_leads(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.dependencies import apply_data_scope_filter

    query = select(Lead).options(
        selectinload(Lead.terminal_customer),
        selectinload(Lead.sales_owner),
        selectinload(Lead.channel),
        selectinload(Lead.source_channel),
    )
    query = apply_data_scope_filter(query, Lead, current_user, db)

    result = await db.execute(query)
    leads = result.scalars().all()

    # 手动填充名称字段
    lead_reads = []
    for lead in leads:
        lead_dict = {
            "id": lead.id,
            "lead_code": lead.lead_code,
            "lead_name": lead.lead_name,
            "terminal_customer_id": lead.terminal_customer_id,
            "terminal_customer_name": lead.terminal_customer.customer_name
            if lead.terminal_customer
            else None,
            "channel_id": lead.channel_id,
            "channel_name": lead.channel.company_name if lead.channel else None,
            "source_channel_id": lead.source_channel_id,
            "source_channel_name": lead.source_channel.company_name
            if lead.source_channel
            else None,
            "lead_stage": lead.lead_stage,
            "lead_source": lead.lead_source,
            "contact_person": lead.contact_person,
            "contact_phone": lead.contact_phone,
            "products": lead.products,
            "estimated_budget": lead.estimated_budget,
            "has_confirmed_requirement": lead.has_confirmed_requirement,
            "has_confirmed_budget": lead.has_confirmed_budget,
            "converted_to_opportunity": lead.converted_to_opportunity,
            "opportunity_id": lead.opportunity_id,
            "sales_owner_id": lead.sales_owner_id,
            "sales_owner_name": lead.sales_owner.name if lead.sales_owner else None,
            "notes": lead.notes,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
        lead_reads.append(lead_dict)
    return lead_reads


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import check_technician_access

    user_role = current_user.get("role")
    user_id = current_user["id"]

    result = await db.execute(
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.terminal_customer),
            selectinload(Lead.sales_owner),
            selectinload(Lead.channel),
            selectinload(Lead.source_channel),
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if user_role == "admin":
        return lead

    if user_role == "sales":
        if lead.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此线索")
        return lead

    if user_role == "technician":
        await check_technician_access(db, user_id, user_role, "lead", lead_id)
        return lead

    raise HTTPException(status_code=403, detail="无权限访问线索数据")


@router.post("/", response_model=LeadRead)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_code = await generate_code(db, "lead")

    new_lead = Lead(
        lead_code=lead_code,
        lead_name=lead.lead_name,
        terminal_customer_id=lead.terminal_customer_id,
        channel_id=lead.channel_id,
        source_channel_id=lead.source_channel_id,
        lead_stage=lead.lead_stage,
        lead_source=lead.lead_source,
        contact_person=lead.contact_person,
        contact_phone=lead.contact_phone,
        products=lead.products,
        estimated_budget=lead.estimated_budget,
        has_confirmed_requirement=lead.has_confirmed_requirement,
        has_confirmed_budget=lead.has_confirmed_budget,
        sales_owner_id=lead.sales_owner_id,
        notes=lead.notes,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_lead)
    await db.flush()
    await db.refresh(new_lead)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="lead",
        entity_id=new_lead.id,
        entity_code=new_lead.lead_code,
        entity_name=new_lead.lead_name,
        description=f"创建线索: {new_lead.lead_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return new_lead


@router.put("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    lead: LeadUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

    if existing.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="已转商机的线索不能修改")

    old_stage = existing.lead_stage
    update_data = lead.model_dump(exclude_unset=True)
    update_data.pop("source_channel_id", None)

    if "lead_stage" in update_data and update_data["lead_stage"] != existing.lead_stage:
        valid_transitions = LEAD_STAGE_TRANSITIONS.get(existing.lead_stage, [])
        if update_data["lead_stage"] not in valid_transitions:
            raise HTTPException(
                status_code=400,
                detail=f"线索阶段不能从 '{existing.lead_stage}' 直接流转到 '{update_data['lead_stage']}'",
            )

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()
    await db.flush()

    if "lead_stage" in update_data and update_data["lead_stage"] != old_stage:
        await log_stage_change(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="lead",
            entity_id=existing.id,
            entity_code=existing.lead_code,
            entity_name=existing.lead_name,
            old_stage=old_stage,
            new_stage=update_data["lead_stage"],
            ip_address=request.client.host if request.client else None,
        )
    else:
        await log_update(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="lead",
            entity_id=existing.id,
            entity_code=existing.lead_code,
            entity_name=existing.lead_name,
            description=f"更新线索: {existing.lead_name}",
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await assert_can_mutate_entity_v2(lead, current_user, db)

    if lead.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="已转商机的线索不能删除")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="lead",
        entity_id=lead.id,
        entity_code=lead.lead_code,
        entity_name=lead.lead_name,
        description=f"删除线索: {lead.lead_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(lead)
    await db.commit()
    return {"message": "Lead deleted successfully"}


@router.post("/{lead_id}/convert", response_model=OpportunityRead)
async def convert_lead_to_opportunity(
    lead_id: int,
    convert_request: LeadConvertRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="该线索已转换为商机")

    if not lead.has_confirmed_requirement or not lead.has_confirmed_budget:
        raise HTTPException(status_code=400, detail="线索需确认需求和预算后才能转商机")

    opportunity_code = await generate_code(db, "opportunity")

    new_opportunity = Opportunity(
        opportunity_code=opportunity_code,
        opportunity_name=convert_request.opportunity_name,
        terminal_customer_id=lead.terminal_customer_id,
        channel_id=lead.channel_id,  # 继承线索的 channel_id
        opportunity_source=convert_request.opportunity_source
        or lead.lead_source
        or "线索转化",
        opportunity_stage="需求方案",
        expected_contract_amount=convert_request.expected_contract_amount,
        sales_owner_id=lead.sales_owner_id,
        created_at=date.today(),
    )
    db.add(new_opportunity)
    await db.flush()
    await db.refresh(new_opportunity)

    lead.converted_to_opportunity = True
    lead.opportunity_id = new_opportunity.id
    lead.updated_at = date.today()

    await log_convert(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        source_type="lead",
        source_id=lead.id,
        source_code=lead.lead_code,
        source_name=lead.lead_name,
        target_type="opportunity",
        target_id=new_opportunity.id,
        target_code=new_opportunity.opportunity_code,
        description=f"线索转商机: {lead.lead_name} → {new_opportunity.opportunity_name}"
        + (
            f" (线索等级: {convert_request.lead_grade})"
            if convert_request.lead_grade
            else ""
        ),
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_opportunity)
    return new_opportunity
