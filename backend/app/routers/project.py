from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.core.policy import policy_service, build_principal
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.auto_number_service import generate_code

router = APIRouter(prefix="/projects", tags=["projects"])

FINANCIAL_FIELDS = [
    "upstream_procurement_amount",
    "direct_project_investment",
    "additional_investment",
    "gross_margin",
]


def _filter_financial_fields(project_dict: dict, role: str) -> dict:
    if role in ("admin", "business", "finance"):
        return project_dict
    for field in FINANCIAL_FIELDS:
        project_dict.pop(field, None)
    return project_dict


@router.get("/", response_model=List[ProjectRead], response_model_exclude_none=True)
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    query = select(Project).options(
        selectinload(Project.terminal_customer),
        selectinload(Project.sales_owner),
        selectinload(Project.channel),
    )
    query = await policy_service.scope_query(
        resource="project",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=Project,
    )

    result = await db.execute(query)
    projects = result.scalars().all()

    project_reads = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "terminal_customer_id": project.terminal_customer_id,
            "terminal_customer_name": project.terminal_customer.customer_name
            if project.terminal_customer
            else None,
            "channel_id": project.channel_id,
            "channel_name": project.channel.company_name
            if project.channel
            else None,
            "source_opportunity_id": project.source_opportunity_id,
            "product_ids": project.product_ids,
            "products": project.products,
            "business_type": project.business_type,
            "project_status": project.project_status,
            "sales_owner_id": project.sales_owner_id,
            "sales_owner_name": project.sales_owner.name
            if project.sales_owner
            else None,
            "downstream_contract_amount": project.downstream_contract_amount,
            "upstream_procurement_amount": project.upstream_procurement_amount,
            "direct_project_investment": project.direct_project_investment,
            "additional_investment": project.additional_investment,
            "winning_date": project.winning_date,
            "acceptance_date": project.acceptance_date,
            "first_payment_date": project.first_payment_date,
            "actual_payment_amount": project.actual_payment_amount,
            "notes": project.notes,
            "gross_margin": project.gross_margin,
        }
        project_dict = _filter_financial_fields(project_dict, principal.role)
        project_reads.append(project_dict)
    return project_reads


@router.get("/{project_id}", response_model=ProjectRead, response_model_exclude_none=True)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.terminal_customer),
            selectinload(Project.sales_owner),
            selectinload(Project.channel),
        )
    )
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

    project_dict = {
        **project.__dict__,
        "terminal_customer_name": project.terminal_customer.customer_name
        if project.terminal_customer
        else None,
        "sales_owner_name": project.sales_owner.name if project.sales_owner else None,
        "channel_name": project.channel.company_name if project.channel else None,
    }
    project_dict = _filter_financial_fields(project_dict, principal.role)
    return project_dict


@router.post("/", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    await policy_service.authorize_create(
        resource="project",
        principal=principal,
        db=db,
        payload=project,
    )

    project_code = await generate_code(db, "project")

    new_project = Project(
        project_code=project_code,
        project_name=project.project_name,
        terminal_customer_id=project.terminal_customer_id,
        channel_id=project.channel_id,
        source_opportunity_id=project.source_opportunity_id,
        product_ids=project.product_ids or [],
        products=project.products or [],
        business_type=project.business_type,
        project_status=project.project_status,
        sales_owner_id=project.sales_owner_id,
        downstream_contract_amount=project.downstream_contract_amount,
        upstream_procurement_amount=project.upstream_procurement_amount,
        direct_project_investment=project.direct_project_investment,
        additional_investment=project.additional_investment,
        winning_date=project.winning_date,
        acceptance_date=project.acceptance_date,
        first_payment_date=project.first_payment_date,
        actual_payment_amount=project.actual_payment_amount,
        notes=project.notes,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return {
        **new_project.__dict__,
        "terminal_customer_name": None,
        "sales_owner_name": None,
        "channel_name": None,
    }
