"""
Financial export service for CRM system.
Provides export functionality for Kingdee integration and financial reporting.
"""

import csv
import io
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

class FinancialExportService:
    """Service for exporting financial data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_projects_for_kingdee(self) -> StreamingResponse:
        """
        Export projects with project_code for Kingdee integration.
        Returns CSV with project_id, project_code, customer_name, amount.
        """
        # Query projects with customer information
        query = """
        SELECT 
            p.id as project_id,
            p.project_code,
            c.customer_name,
            p.downstream_contract_amount as amount,
            p.business_type,
            p.project_status
        FROM projects p
        JOIN terminal_customers c ON p.terminal_customer_id = c.id
        ORDER BY p.created_at DESC
        """
        
        result = self.db.execute(query)
        rows = result.fetchall()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'project_id',
            'project_code', 
            'customer_name',
            'amount',
            'business_type',
            'project_status'
        ])
        
        # Data rows
        for row in rows:
            writer.writerow([
                row.project_id,
                row.project_code,
                row.customer_name,
                row.amount,
                row.business_type,
                row.project_status
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=projects_kingdee_export.csv"}
        )
    
    def export_contracts_for_kingdee(self) -> StreamingResponse:
        """
        Export contracts with project_code for Kingdee integration.
        """
        query = """
        SELECT 
            co.id as contract_id,
            co.contract_code,
            p.project_code,
            c.customer_name,
            co.contract_amount as amount,
            co.contract_direction,
            co.contract_status
        FROM contracts co
        JOIN projects p ON co.project_id = p.id
        JOIN terminal_customers c ON p.terminal_customer_id = c.id
        ORDER BY co.created_at DESC
        """
        
        result = self.db.execute(query)
        rows = result.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'contract_id',
            'contract_code',
            'project_code',
            'customer_name', 
            'amount',
            'contract_direction',
            'contract_status'
        ])
        
        for row in rows:
            writer.writerow([
                row.contract_id,
                row.contract_code,
                row.project_code,
                row.customer_name,
                row.amount,
                row.contract_direction,
                row.contract_status
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv", 
            headers={"Content-Disposition": "attachment; filename=contracts_kingdee_export.csv"}
        )
    
    def export_financial_summary(self) -> StreamingResponse:
        """
        Export comprehensive financial summary including profit calculations.
        """
        query = """
        SELECT 
            p.project_code,
            c.customer_name,
            p.business_type,
            p.downstream_contract_amount,
            p.upstream_procurement_amount,
            p.gross_margin,
            p.project_status,
            COUNT(co.id) as contract_count
        FROM projects p
        JOIN terminal_customers c ON p.terminal_customer_id = c.id
        LEFT JOIN contracts co ON p.id = co.project_id
        WHERE p.downstream_contract_amount IS NOT NULL
        GROUP BY p.id, p.project_code, c.customer_name, p.business_type, 
                 p.downstream_contract_amount, p.upstream_procurement_amount, 
                 p.gross_margin, p.project_status
        ORDER BY p.created_at DESC
        """
        
        result = self.db.execute(query)
        rows = result.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'project_code',
            'customer_name',
            'business_type', 
            'downstream_contract_amount',
            'upstream_procurement_amount',
            'gross_margin',
            'project_status',
            'contract_count'
        ])
        
        for row in rows:
            writer.writerow([
                row.project_code,
                row.customer_name,
                row.business_type,
                row.downstream_contract_amount or 0,
                row.upstream_procurement_amount or 0,
                row.gross_margin or 0,
                row.project_status,
                row.contract_count
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=financial_summary.csv"}
        )