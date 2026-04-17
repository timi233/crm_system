from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.customer_channel_link import CustomerChannelLink
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.auto_number_service import generate_code
from app.services.operation_log_service import log_create, log_update, log_delete

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerRead])
async def list_customers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user["id"]

    stmt = select(TerminalCustomer).options(
        selectinload(TerminalCustomer.owner), selectinload(TerminalCustomer.channel)
    )

    if user_role == "admin" or user_role in ["business", "finance"]:
        pass
    elif user_role == "sales":
        stmt = stmt.where(TerminalCustomer.customer_owner_id == user_id)
    elif user_role == "technician":
        customer_ids_from_work_orders = select(WorkOrder.lead_id).where(
            WorkOrder.lead_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_leads = select(Lead.terminal_customer_id).where(
            Lead.id.in_(customer_ids_from_work_orders)
        )

        opp_customer_ids = select(WorkOrder.opportunity_id).where(
            WorkOrder.opportunity_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_opps = select(Opportunity.terminal_customer_id).where(
            Opportunity.id.in_(opp_customer_ids)
        )

        proj_customer_ids = select(WorkOrder.project_id).where(
            WorkOrder.project_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_projs = select(Project.terminal_customer_id).where(
            Project.id.in_(proj_customer_ids)
        )

        stmt = stmt.where(
            or_(
                TerminalCustomer.id.in_(customer_ids_from_leads),
                TerminalCustomer.id.in_(customer_ids_from_opps),
                TerminalCustomer.id.in_(customer_ids_from_projs),
            )
        )
    else:
        stmt = stmt.where(False)

    result = await db.execute(stmt)
    customers = result.scalars().all()
    return [
        {
            **c.__dict__,
            "customer_owner_name": c.owner.name if c.owner else None,
            "channel_name": c.channel.company_name if c.channel else None,
        }
        for c in customers
    ]


@router.get("/check-credit-code")
async def check_credit_code(
    credit_code: str,
    exclude_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TerminalCustomer).where(TerminalCustomer.credit_code == credit_code)
    if exclude_id:
        query = query.where(TerminalCustomer.id != exclude_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    return {"exists": existing is not None}


@router.post("/", response_model=CustomerRead)
async def create_customer(
    customer: CustomerCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        existing = await db.execute(
            select(TerminalCustomer).where(
                TerminalCustomer.credit_code == customer.credit_code
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

        customer_code = await generate_code(db, "customer")

        new_customer = TerminalCustomer(
            customer_code=customer_code,
            customer_name=customer.customer_name,
            credit_code=customer.credit_code,
            customer_industry=customer.customer_industry,
            customer_region=customer.customer_region,
            customer_owner_id=customer.customer_owner_id,
            channel_id=customer.channel_id,
            main_contact=customer.main_contact,
            phone=customer.phone,
            customer_status=customer.customer_status,
            maintenance_expiry=customer.maintenance_expiry,
            notes=customer.notes,
        )
        db.add(new_customer)
        await db.flush()

        if customer.channel_id is not None:
            main_channel_link = CustomerChannelLink(
                customer_id=new_customer.id,
                channel_id=customer.channel_id,
                role="主渠道",
                created_by=current_user["id"],
            )
            db.add(main_channel_link)
            await db.flush()

        await db.refresh(new_customer)

        await log_create(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="customer",
            entity_id=new_customer.id,
            entity_code=new_customer.customer_code,
            entity_name=new_customer.customer_name,
            description=f"创建客户: {new_customer.customer_name}",
            ip_address=request.client.host if request.client else None,
        )

        await db.commit()
        await db.refresh(new_customer)
        await db.refresh(new_customer, ["owner", "channel"])
        return {
            "id": new_customer.id,
            "customer_code": new_customer.customer_code,
            "customer_name": new_customer.customer_name,
            "credit_code": new_customer.credit_code,
            "customer_industry": new_customer.customer_industry,
            "customer_region": new_customer.customer_region,
            "customer_owner_id": new_customer.customer_owner_id,
            "channel_id": new_customer.channel_id,
            "main_contact": new_customer.main_contact,
            "phone": new_customer.phone,
            "customer_status": new_customer.customer_status,
            "maintenance_expiry": new_customer.maintenance_expiry,
            "notes": new_customer.notes,
            "customer_owner_name": new_customer.owner.name
            if new_customer.owner
            else None,
            "channel_name": new_customer.channel.company_name
            if new_customer.channel
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging

        logger = logging.getLogger("uvicorn.error")
        logger.error(f"Error creating customer: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建客户失败: {str(e)}")


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    customer: CustomerCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

    old_data = {
        "customer_name": existing.customer_name,
        "credit_code": existing.credit_code,
        "customer_industry": existing.customer_industry,
        "customer_region": existing.customer_region,
        "customer_status": existing.customer_status,
    }

    if customer.credit_code != existing.credit_code:
        duplicate = await db.execute(
            select(TerminalCustomer).where(
                TerminalCustomer.credit_code == customer.credit_code
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

    existing.customer_name = customer.customer_name
    existing.credit_code = customer.credit_code
    existing.customer_industry = customer.customer_industry
    existing.customer_region = customer.customer_region
    existing.customer_owner_id = customer.customer_owner_id
    existing.main_contact = customer.main_contact
    existing.phone = customer.phone
    existing.customer_status = customer.customer_status
    existing.maintenance_expiry = customer.maintenance_expiry
    existing.notes = customer.notes

    channel_changed = existing.channel_id != customer.channel_id
    existing.channel_id = customer.channel_id

    if channel_changed:
        if existing.channel_id is not None:
            existing_links = await db.execute(
                select(CustomerChannelLink).where(
                    CustomerChannelLink.customer_id == customer_id,
                    CustomerChannelLink.role == "主渠道",
                    CustomerChannelLink.end_date.is_(None),
                )
            )
            for link in existing_links.scalars():
                link.end_date = date.today()
                await db.flush()

        if customer.channel_id is not None:
            new_main_link = CustomerChannelLink(
                customer_id=customer_id,
                channel_id=customer.channel_id,
                role="主渠道",
                created_by=current_user["id"],
            )
            db.add(new_main_link)
            await db.flush()

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="customer",
        entity_id=existing.id,
        entity_code=existing.customer_code,
        entity_name=existing.customer_name,
        old_value=old_data,
        new_value={
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
            "customer_industry": customer.customer_industry,
            "customer_region": customer.customer_region,
            "customer_status": customer.customer_status,
        },
        description=f"更新客户: {existing.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)
    await db.refresh(existing, ["owner", "channel"])
    return {
        **existing.__dict__,
        "customer_owner_name": existing.owner.name if existing.owner else None,
        "channel_name": existing.channel.company_name if existing.channel else None,
    }


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await assert_can_mutate_entity_v2(customer, current_user, db)

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="customer",
        entity_id=customer.id,
        entity_code=customer.customer_code,
        entity_name=customer.customer_name,
        old_value={
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
        },
        description=f"删除客户: {customer.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(customer)
    await db.commit()
    return {"message": "Customer deleted successfully"}
