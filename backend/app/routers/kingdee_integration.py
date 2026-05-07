"""
Kingdee integration router for CRM system.
Provides endpoints for Kingdee accounting system integration.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.database import get_db
from app.models.project import Project

router = APIRouter(prefix="/kingdee", tags=["kingdee"])


async def _generate_kingdee_project_summary(db: AsyncSession, project_id: int):
    """Generate Kingdee-compatible project summary."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from app.models.contract import Contract
    contracts_result = await db.execute(
        select(Contract).where(Contract.project_id == project_id)
    )
    contracts = contracts_result.scalars().all()
    
    total_amount = sum(c.contract_amount or 0 for c in contracts)
    
    return {
        "project_id": project.id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "business_type": project.business_type,
        "project_status": project.project_status,
        "downstream_contract_amount": float(project.downstream_contract_amount or 0),
        "upstream_procurement_amount": float(project.upstream_procurement_amount or 0),
        "gross_margin": float(project.gross_margin or 0) if project.gross_margin else None,
        "contracts_count": len(contracts),
        "total_contract_amount": float(total_amount),
    }


@router.get("/summary/project/{project_id}")
async def get_kingdee_project_summary(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Kingdee-compatible project summary with project number prominently displayed.
    This endpoint is designed to be called by Kingdee integration scripts.
    """
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="kingdee_integration",
        action="read",
        principal=principal,
        db=db,
        obj=None,
        operation="project_summary",
    )
    
    try:
        summary = await _generate_kingdee_project_summary(db, project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Kingdee summary: {str(e)}")


@router.get("/projects/for-integration")
async def get_projects_for_kingdee_integration(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all projects formatted for Kingdee integration.
    Returns a list of projects with Kingdee-ready fields.
    """
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="kingdee_integration",
        action="read",
        principal=principal,
        db=db,
        obj=None,
        operation="projects_for_integration",
    )
    
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    
    kingdee_projects = []
    for project in projects:
        try:
            summary = await _generate_kingdee_project_summary(db, project.id)
            kingdee_projects.append(summary)
        except Exception:
            continue
    
    return {
        "projects": kingdee_projects,
        "total_count": len(kingdee_projects),
        "integration_ready": True
    }


@router.post("/validate-project-codes")
async def validate_project_codes_for_kingdee(
    project_ids: list,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate that project codes are properly formatted for Kingdee integration.
    """
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="kingdee_integration",
        action="read",
        principal=principal,
        db=db,
        obj=None,
        operation="validate_project_codes",
    )
    
    result = await db.execute(select(Project).where(Project.id.in_(project_ids)))
    projects = result.scalars().all()
    
    validation_results = []
    for project in projects:
        is_valid_format = bool(
            project.project_code.startswith('PRJ-') and 
            (len(project.project_code) == 14 or  
             (len(project.project_code) > 14 and '-SVC' in project.project_code))
        )
        
        validation_results.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "is_valid_format": is_valid_format,
            "has_financial_data": project.downstream_contract_amount is not None
        })
    
    return {
        "validation_results": validation_results,
        "all_valid": all(result["is_valid_format"] for result in validation_results),
        "ready_for_kingdee": all(result["has_financial_data"] for result in validation_results)
    }
