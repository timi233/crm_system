"""
Projects router with enhanced business logic for CRM system.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Project, TerminalCustomer, Channel, Opportunity, Contract
from ..schemas import ProjectCreate, ProjectRead, ProjectUpdate
from ..services.auto_number_service import AutoNumberService
from ..middleware.rbac_middleware import RBACMiddleware  
from ..validation.rules import ValidationRules

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectRead)
def create_project(
    project: ProjectCreate,
    renewal: Optional[bool] = Query(False, description="Whether this is a renewal project"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project with auto-numbering and business logic validation.
    """
    # Check RBAC permissions
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "sales", "business"])
    
    # Validate terminal customer exists
    if not db.query(TerminalCustomer).filter(TerminalCustomer.id == project.terminal_customer_id).first():
        raise HTTPException(status_code=400, detail="Invalid terminal customer ID")
    
    # Validate sales owner exists  
    if not db.query(User).filter(User.id == project.sales_owner_id).first():
        raise HTTPException(status_code=400, detail="Invalid sales owner ID")
    
    # Validate channel if provided
    if project.channel_id and not db.query(Channel).filter(Channel.id == project.channel_id).first():
        raise HTTPException(status_code=400, detail="Invalid channel ID")
    
    # Validate source opportunity if provided
    if project.source_opportunity_id and not db.query(Opportunity).filter(Opportunity.id == project.source_opportunity_id).first():
        raise HTTPException(status_code=400, detail="Invalid source opportunity ID")
    
    # Validate downstream contract amount
    ValidationRules.validate_project_downstream_amount(project.dict())
    
    # Generate project code with renewal suffix if needed
    auto_number = AutoNumberService(db)
    if renewal:
        project_code = auto_number.generate_project_code(is_renewal=True)
    else:
        # Auto-detect renewal based on business type or opportunity name
        is_renewal = auto_number.detect_renewal(
            project.project_name, 
            project.business_type
        )
        project_code = auto_number.generate_project_code(is_renewal=is_renewal)
    
    # Calculate gross margin
    gross_margin = project.downstream_contract_amount - (project.upstream_procurement_amount or 0)
    
    # Create project
    db_project = Project(
        project_code=project_code,
        gross_margin=gross_margin,
        **project.dict()
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project

@router.get("/export/kingdee")
def export_projects_for_kingdee(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export projects for Kingdee integration with project_code prominently displayed.
    """
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance", "business"])
    
    from ..services.financial_export_service import FinancialExportService
    exporter = FinancialExportService(db)
    return exporter.export_projects_for_kingdee()

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List projects with RBAC field filtering."""
    rbac = RBACMiddleware(db)
    
    if current_user["role"] == "sales":
        # Sales can only see projects they own
        projects = db.query(Project).filter(Project.sales_owner_id == current_user["id"]).all()
    else:
        projects = db.query(Project).all()
    
    # Apply field-level filtering
    filtered_projects = []
    for project in projects:
        project_dict = project.__dict__
        filtered_project = rbac.filter_response_fields(
            current_user["role"], 
            "projects", 
            project_dict
        )
        filtered_projects.append(filtered_project)
    
    return filtered_projects