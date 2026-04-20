from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user, apply_data_scope_filter
from app.models.project import Project
from app.schemas.project import ProjectRead, ProjectCreate
from app.services.auto_number_service import generate_code

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Project).options(
        selectinload(Project.terminal_customer),
        selectinload(Project.sales_owner),
        selectinload(Project.channel),
    )
    query = apply_data_scope_filter(query, Project, current_user, db)

    result = await db.execute(query)
    projects = result.scalars().all()

    project_reads = []
    for proj in projects:
        proj_dict = {
            "id": proj.id,
            "project_code": proj.project_code,
            "project_name": proj.project_name,
            "terminal_customer_id": proj.terminal_customer_id,
            "terminal_customer_name": proj.terminal_customer.customer_name
            if proj.terminal_customer
            else None,
            "channel_id": proj.channel_id,
            "channel_name": proj.channel.company_name if proj.channel else None,
            "source_opportunity_id": proj.source_opportunity_id,
            "product_ids": proj.product_ids,
            "products": proj.products,
            "business_type": proj.business_type,
            "project_status": proj.project_status,
            "sales_owner_id": proj.sales_owner_id,
            "sales_owner_name": proj.sales_owner.name if proj.sales_owner else None,
            "downstream_contract_amount": proj.downstream_contract_amount,
            "upstream_procurement_amount": proj.upstream_procurement_amount,
            "direct_project_investment": proj.direct_project_investment,
            "additional_investment": proj.additional_investment,
            "winning_date": proj.winning_date,
            "acceptance_date": proj.acceptance_date,
            "first_payment_date": proj.first_payment_date,
            "actual_payment_amount": proj.actual_payment_amount,
            "notes": proj.notes,
            "gross_margin": proj.gross_margin,
        }
        project_reads.append(proj_dict)
    return project_reads


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user["id"]

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

    if user_role == "admin" or user_role == "business":
        pass
    elif user_role == "sales":
        if project.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此项目")
    elif user_role == "finance":
        pass
    else:
        raise HTTPException(status_code=403, detail="无权限访问项目数据")

    return {
        **project.__dict__,
        "terminal_customer_name": project.terminal_customer.customer_name
        if project.terminal_customer
        else None,
        "sales_owner_name": project.sales_owner.name if project.sales_owner else None,
        "channel_name": project.channel.company_name if project.channel else None,
    }


@router.post("/", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    if user_role not in ["admin", "business", "sales"]:
        raise HTTPException(status_code=403, detail="无权限创建项目")

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
