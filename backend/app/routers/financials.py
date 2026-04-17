"""
Financial export router with async database operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.contract import Contract
from app.models.customer import TerminalCustomer

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/export/projects")
async def export_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] not in ["admin", "finance", "business"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Project, TerminalCustomer)
        .join(TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id)
        .order_by(Project.id.desc())
    )
    rows = result.all()

    return [
        {
            "project_id": p.id,
            "project_code": p.project_code,
            "customer_name": c.customer_name,
            "amount": p.downstream_contract_amount,
            "business_type": p.business_type,
            "project_status": p.project_status,
        }
        for p, c in rows
    ]


@router.get("/export/contracts")
async def export_contracts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] not in ["admin", "finance", "business"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Contract, Project, TerminalCustomer)
        .join(Project, Contract.project_id == Project.id)
        .join(TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id)
        .order_by(Contract.id.desc())
    )
    rows = result.all()

    return [
        {
            "contract_id": c.id,
            "contract_code": c.contract_code,
            "project_code": p.project_code,
            "customer_name": tc.customer_name,
            "amount": c.contract_amount,
            "contract_direction": c.contract_direction,
            "contract_status": c.contract_status,
        }
        for c, p, tc in rows
    ]


@router.get("/export/summary")
async def export_financial_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] not in ["admin", "finance"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Project, TerminalCustomer)
        .join(TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id)
        .where(Project.downstream_contract_amount.isnot(None))
        .order_by(Project.id.desc())
    )
    rows = result.all()

    return [
        {
            "project_code": p.project_code,
            "customer_name": c.customer_name,
            "business_type": p.business_type,
            "downstream_contract_amount": p.downstream_contract_amount or 0,
            "upstream_procurement_amount": p.upstream_procurement_amount or 0,
            "gross_margin": p.gross_margin or 0,
            "project_status": p.project_status,
        }
        for p, c in rows
    ]
