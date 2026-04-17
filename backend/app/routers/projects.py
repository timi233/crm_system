"""
Projects router with async database operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.opportunity import Opportunity
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.auto_number_service import generate_code

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    renewal: Optional[bool] = Query(
        False, description="Whether this is a renewal project"
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project with auto-numbering and business logic validation.
    """
    if current_user["role"] not in ["admin", "sales", "business"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate terminal customer exists
    result = await db.execute(
        select(TerminalCustomer).where(
            TerminalCustomer.id == project.terminal_customer_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid terminal customer ID")

    # Validate sales owner exists
    result = await db.execute(select(User).where(User.id == project.sales_owner_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid sales owner ID")

    # Validate channel if provided
    if project.channel_id:
        result = await db.execute(
            select(Channel).where(Channel.id == project.channel_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid channel ID")

    # Validate source opportunity if provided
    if project.source_opportunity_id:
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == project.source_opportunity_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid source opportunity ID")

    # Validate downstream contract amount
    if project.downstream_contract_amount <= 0:
        raise HTTPException(
            status_code=400, detail="downstream_contract_amount must be positive"
        )

    # Generate project code
    project_code = await generate_code(db, "project")

    # Calculate gross margin
    gross_margin = project.downstream_contract_amount - (
        project.upstream_procurement_amount or 0
    )

    # Create project
    db_project = Project(
        project_code=project_code,
        project_name=project.project_name,
        terminal_customer_id=project.terminal_customer_id,
        sales_owner_id=project.sales_owner_id,
        business_type=project.business_type,
        project_status=project.project_status,
        downstream_contract_amount=project.downstream_contract_amount,
        upstream_procurement_amount=project.upstream_procurement_amount,
        direct_project_investment=project.direct_project_investment,
        additional_investment=project.additional_investment,
        winning_date=project.winning_date,
        acceptance_date=project.acceptance_date,
        first_payment_date=project.first_payment_date,
        actual_payment_amount=project.actual_payment_amount,
        notes=project.notes,
        product_ids=project.product_ids,
        channel_id=project.channel_id,
        source_opportunity_id=project.source_opportunity_id,
        gross_margin=gross_margin,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return db_project


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List projects with role-based filtering."""
    query = select(Project).options(
        selectinload(Project.terminal_customer),
        selectinload(Project.sales_owner),
    )

    if current_user["role"] == "sales":
        query = query.where(Project.sales_owner_id == current_user["id"])

    result = await db.execute(query)
    projects = result.scalars().all()

    # Build response with name fields
    response = []
    for p in projects:
        response.append(
            {
                "id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "terminal_customer_id": p.terminal_customer_id,
                "terminal_customer_name": p.terminal_customer.customer_name
                if p.terminal_customer
                else None,
                "sales_owner_id": p.sales_owner_id,
                "sales_owner_name": p.sales_owner.name if p.sales_owner else None,
                "business_type": p.business_type,
                "project_status": p.project_status,
                "downstream_contract_amount": p.downstream_contract_amount,
                "upstream_procurement_amount": p.upstream_procurement_amount,
                "direct_project_investment": p.direct_project_investment,
                "additional_investment": p.additional_investment,
                "gross_margin": p.gross_margin,
                "winning_date": p.winning_date,
                "acceptance_date": p.acceptance_date,
                "first_payment_date": p.first_payment_date,
                "actual_payment_amount": p.actual_payment_amount,
                "notes": p.notes,
                "product_ids": p.product_ids,
                "products": p.products,
                "channel_id": p.channel_id,
                "source_opportunity_id": p.source_opportunity_id,
            }
        )

    return response
