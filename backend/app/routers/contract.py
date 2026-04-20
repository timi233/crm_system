from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.channel_assignment import ChannelAssignment
from app.models.contract import Contract, ContractProduct, PaymentPlan
from app.models.project import Project
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services.auto_number_service import generate_code
from app.services.operation_log_service import log_create, log_update, log_delete

router = APIRouter(prefix="/contracts", tags=["contracts"])


def parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


async def _apply_contract_scope(query, current_user: dict, db: AsyncSession):
    role = current_user.get("role")
    user_id = current_user["id"]

    if role in {"admin", "business", "finance"}:
        return query

    if role == "sales":
        assigned_channels = select(ChannelAssignment.channel_id).where(
            ChannelAssignment.user_id == user_id
        )
        owned_projects = select(Project.id).where(Project.sales_owner_id == user_id)
        owned_customers = select(TerminalCustomer.id).where(
            TerminalCustomer.customer_owner_id == user_id
        )
        return query.where(
            or_(
                Contract.project_id.in_(owned_projects),
                Contract.terminal_customer_id.in_(owned_customers),
                Contract.channel_id.in_(assigned_channels),
            )
        )

    if role == "technician":
        assigned_projects = (
            select(WorkOrder.project_id)
            .join(
                WorkOrderTechnician,
                WorkOrderTechnician.work_order_id == WorkOrder.id,
            )
            .where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.project_id.isnot(None),
            )
        )
        return query.where(Contract.project_id.in_(assigned_projects))

    raise HTTPException(status_code=403, detail="无权限访问合同数据")


async def _ensure_can_write_contract(
    db: AsyncSession,
    current_user: dict,
    project_id: int,
    terminal_customer_id: Optional[int],
    channel_id: Optional[int],
):
    role = current_user.get("role")
    user_id = current_user["id"]

    if role in {"admin", "business", "finance"}:
        return

    if role != "sales":
        raise HTTPException(status_code=403, detail="无权限修改合同数据")

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.sales_owner_id == user_id:
        return

    assigned_channel = None
    target_channel_id = channel_id or project.channel_id
    if target_channel_id is not None:
        assigned_channel = await db.execute(
            select(ChannelAssignment.id).where(
                ChannelAssignment.user_id == user_id,
                ChannelAssignment.channel_id == target_channel_id,
            )
        )
        if assigned_channel.scalar_one_or_none() is not None:
            return

    target_customer_id = terminal_customer_id or project.terminal_customer_id
    if target_customer_id is not None:
        owned_customer = await db.execute(
            select(TerminalCustomer.id).where(
                TerminalCustomer.id == target_customer_id,
                TerminalCustomer.customer_owner_id == user_id,
            )
        )
        if owned_customer.scalar_one_or_none() is not None:
            return

    raise HTTPException(status_code=403, detail="只能修改自己负责或分配的合同")


@router.get("/", response_model=List[ContractRead])
async def list_contracts(
    project_id: Optional[int] = None,
    contract_direction: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            Contract,
            Project.project_name,
            TerminalCustomer.customer_name,
            Channel.company_name,
        )
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
        .outerjoin(Project, Contract.project_id == Project.id)
        .outerjoin(
            TerminalCustomer, Contract.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(Channel, Contract.channel_id == Channel.id)
    )
    query = await _apply_contract_scope(query, current_user, db)
    if project_id:
        query = query.where(Contract.project_id == project_id)
    if contract_direction:
        query = query.where(Contract.contract_direction == contract_direction)
    result = await db.execute(query)
    rows = result.all()
    contracts = []
    for row in rows:
        contract = row[0]
        project_name = row[1] if len(row) > 1 else None
        customer_name = row[2] if len(row) > 2 else None
        channel_name = row[3] if len(row) > 3 else None
        contract_dict = {
            "id": contract.id,
            "contract_code": contract.contract_code,
            "contract_name": contract.contract_name,
            "project_id": contract.project_id,
            "contract_direction": contract.contract_direction,
            "contract_status": contract.contract_status,
            "terminal_customer_id": contract.terminal_customer_id,
            "channel_id": contract.channel_id,
            "contract_amount": contract.contract_amount,
            "signing_date": contract.signing_date,
            "effective_date": contract.effective_date,
            "expiry_date": contract.expiry_date,
            "contract_file_url": contract.contract_file_url,
            "notes": contract.notes,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "products": contract.products,
            "payment_plans": contract.payment_plans,
            "project_name": project_name,
            "terminal_customer_name": customer_name,
            "channel_name": channel_name,
        }
        contracts.append(ContractRead(**contract_dict))
    return contracts


@router.get("/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    access_check = await db.execute(
        await _apply_contract_scope(
            select(Contract.id).where(Contract.id == contract_id), current_user, db
        )
    )
    if access_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="无权限访问此合同")
    return contract


@router.post("/", response_model=ContractRead)
async def create_contract(
    contract: ContractCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if (
        contract.contract_direction == "Downstream"
        and not contract.terminal_customer_id
    ):
        raise HTTPException(status_code=400, detail="下游合同必须关联终端客户")
    if contract.contract_direction == "Upstream" and not contract.channel_id:
        raise HTTPException(status_code=400, detail="上游合同必须关联渠道/供应商")

    await _ensure_can_write_contract(
        db=db,
        current_user=current_user,
        project_id=contract.project_id,
        terminal_customer_id=contract.terminal_customer_id,
        channel_id=contract.channel_id,
    )

    contract_code = await generate_code(db, "contract")

    new_contract = Contract(
        contract_code=contract_code,
        contract_name=contract.contract_name,
        project_id=contract.project_id,
        contract_direction=contract.contract_direction,
        contract_status=contract.contract_status,
        terminal_customer_id=contract.terminal_customer_id,
        channel_id=contract.channel_id,
        contract_amount=contract.contract_amount,
        signing_date=parse_date(contract.signing_date),
        effective_date=parse_date(contract.effective_date),
        expiry_date=parse_date(contract.expiry_date),
        contract_file_url=contract.contract_file_url,
        notes=contract.notes,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_contract)
    await db.flush()

    for product in contract.products:
        new_product = ContractProduct(
            contract_id=new_contract.id,
            product_id=product.product_id,
            product_name=product.product_name,
            quantity=product.quantity,
            unit_price=product.unit_price,
            discount=product.discount,
            amount=product.amount,
            notes=product.notes,
        )
        db.add(new_product)

    for plan in contract.payment_plans:
        new_plan = PaymentPlan(
            contract_id=new_contract.id,
            plan_stage=plan.plan_stage,
            plan_amount=plan.plan_amount,
            plan_date=parse_date(plan.plan_date),
            actual_amount=plan.actual_amount or 0,
            actual_date=parse_date(plan.actual_date),
            payment_status=plan.payment_status,
            notes=plan.notes,
        )
        db.add(new_plan)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=new_contract.id,
        entity_code=new_contract.contract_code,
        entity_name=new_contract.contract_name,
        description=f"创建合同: {new_contract.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    result = await db.execute(
        select(Contract)
        .where(Contract.id == new_contract.id)
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
    )
    return result.scalar_one()


@router.put("/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: int,
    contract: ContractUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = contract.model_dump(exclude_unset=True)
    target_project_id = update_data.get("project_id", existing.project_id)
    target_customer_id = update_data.get(
        "terminal_customer_id", existing.terminal_customer_id
    )
    target_channel_id = update_data.get("channel_id", existing.channel_id)

    await _ensure_can_write_contract(
        db=db,
        current_user=current_user,
        project_id=target_project_id,
        terminal_customer_id=target_customer_id,
        channel_id=target_channel_id,
    )

    products_data = update_data.pop("products", None)
    payment_plans_data = update_data.pop("payment_plans", None)

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()

    # 重建 products 和 payment_plans
    if products_data is not None:
        result = await db.execute(
            select(ContractProduct).where(ContractProduct.contract_id == existing.id)
        )
        for p in result.scalars().all():
            await db.delete(p)

        for product in products_data:
            new_product = ContractProduct(
                contract_id=existing.id,
                product_id=product.product_id,
                product_name=product.product_name,
                quantity=product.quantity,
                unit_price=product.unit_price,
                discount=product.discount,
                amount=product.amount,
                notes=product.notes,
            )
            db.add(new_product)

    if payment_plans_data is not None:
        result = await db.execute(
            select(PaymentPlan).where(PaymentPlan.contract_id == existing.id)
        )
        for p in result.scalars().all():
            await db.delete(p)

        for plan in payment_plans_data:
            new_plan = PaymentPlan(
                contract_id=existing.id,
                plan_stage=plan.plan_stage,
                plan_amount=plan.plan_amount,
                plan_date=plan.plan_date,
                actual_amount=plan.actual_amount or 0,
                actual_date=plan.actual_date,
                payment_status=plan.payment_status,
                notes=plan.notes,
            )
            db.add(new_plan)

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=existing.id,
        entity_code=existing.contract_code,
        entity_name=existing.contract_name,
        description=f"更新合同: {existing.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)

    # 签约合同刷新渠道业绩
    if existing.contract_status == "signed" and existing.channel_id:
        from app.services.channel_performance_service import refresh_channel_performance

        await refresh_channel_performance(db, existing.channel_id)

    return existing


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    await _ensure_can_write_contract(
        db=db,
        current_user=current_user,
        project_id=contract.project_id,
        terminal_customer_id=contract.terminal_customer_id,
        channel_id=contract.channel_id,
    )

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=contract.id,
        entity_code=contract.contract_code,
        entity_name=contract.contract_name,
        description=f"删除合同: {contract.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(contract)
    await db.commit()
    return {"message": "Contract deleted successfully"}
