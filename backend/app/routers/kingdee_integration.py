"""
Kingdee integration router for CRM system.
Provides endpoints for Kingdee accounting system integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..middleware.rbac_middleware import RBACMiddleware
from ..services.business_rules_service import BusinessRulesService

router = APIRouter(prefix="/kingdee", tags=["kingdee"])

@router.get("/summary/project/{project_id}")
def get_kingdee_project_summary(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Kingdee-compatible project summary with project number prominently displayed.
    This endpoint is designed to be called by Kingdee integration scripts.
    """
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance", "business"])
    
    business_rules = BusinessRulesService(db)
    try:
        summary = business_rules.generate_kingdee_transaction_summary(project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Kingdee summary: {str(e)}")

@router.get("/projects/for-integration")
def get_projects_for_kingdee_integration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects formatted for Kingdee integration.
    Returns a list of projects with Kingdee-ready fields.
    """
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance"])
    
    from ..models import Project
    projects = db.query(Project).all()
    
    business_rules = BusinessRulesService(db)
    kingdee_projects = []
    
    for project in projects:
        try:
            summary = business_rules.generate_kingdee_transaction_summary(project.id)
            kingdee_projects.append(summary)
        except Exception as e:
            # Skip projects that fail to generate summary
            continue
    
    return {
        "projects": kingdee_projects,
        "total_count": len(kingdee_projects),
        "integration_ready": True
    }

@router.post("/validate-project-codes")
def validate_project_codes_for_kingdee(
    project_ids: list,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate that project codes are properly formatted for Kingdee integration.
    """
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance"])
    
    from ..models import Project
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    
    validation_results = []
    for project in projects:
        # Validate project code format
        is_valid_format = bool(
            project.project_code.startswith('PRJ-') and 
            (len(project.project_code) == 14 or  # PRJ-YYYYMM-XXX
             (len(project.project_code) > 14 and '-SVC' in project.project_code))  # PRJ-YYYYMM-XXX-SVC
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