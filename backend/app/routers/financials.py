"""
Financial export router for CRM system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..middleware.rbac_middleware import RBACMiddleware
from ..services.financial_export_service import FinancialExportService

router = APIRouter(prefix="/financials", tags=["financials"])

@router.get("/export/projects")
def export_projects(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export projects for financial reporting."""
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance", "business"])
    
    exporter = FinancialExportService(db)
    return exporter.export_projects_for_kingdee()

@router.get("/export/contracts")  
def export_contracts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export contracts for financial reporting."""
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance", "business"])
    
    exporter = FinancialExportService(db)
    return exporter.export_contracts_for_kingdee()

@router.get("/export/summary")
def export_financial_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export comprehensive financial summary."""
    rbac = RBACMiddleware(db)
    rbac.require_role(current_user["role"], ["admin", "finance"])
    
    exporter = FinancialExportService(db)
    return exporter.export_financial_summary()