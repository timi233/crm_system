"""
Validation rules for CRM system business logic.
Implements all required validation rules from the specification.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

class ValidationRules:
    """Business logic validation rules."""
    
    @staticmethod
    def validate_opportunity_loss_reason(opportunity_data: Dict[str, Any]) -> bool:
        """
        Validate that loss_reason is provided when opportunity_stage is 'Lost'.
        """
        stage = opportunity_data.get('opportunity_stage', '')
        loss_reason = opportunity_data.get('loss_reason')
        
        if stage == 'Lost' and not loss_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="loss_reason is required when opportunity_stage is 'Lost'"
            )
        return True
    
    @staticmethod
    def validate_follow_up_xor(follow_up_data: Dict[str, Any]) -> bool:
        """
        Validate that exactly one of opportunity_id or project_id is provided.
        """
        opportunity_id = follow_up_data.get('opportunity_id')
        project_id = follow_up_data.get('project_id')
        
        if opportunity_id is None and project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either opportunity_id or project_id must be provided"
            )
        
        if opportunity_id is not None and project_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only one of opportunity_id or project_id can be provided"
            )
        
        return True
    
    @staticmethod
    def validate_project_downstream_amount(project_data: Dict[str, Any]) -> bool:
        """
        Validate that downstream_contract_amount is positive.
        """
        amount = project_data.get('downstream_contract_amount', 0)
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="downstream_contract_amount must be positive"
            )
        return True
    
    @staticmethod
    def validate_contract_linked_project(contract_data: Dict[str, Any], existing_projects: List[int]) -> bool:
        """
        Validate that contract is linked to a valid project.
        """
        project_id = contract_data.get('project_id')
        
        if project_id not in existing_projects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project_id: {project_id}. Project does not exist."
            )
        return True
    
    @staticmethod
    def validate_customer_owner_exists(customer_data: Dict[str, Any], existing_users: List[int]) -> bool:
        """
        Validate that customer owner exists.
        """
        owner_id = customer_data.get('customer_owner_id')
        
        if owner_id not in existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer_owner_id: {owner_id}. User does not exist."
            )
        return True
    
    @staticmethod
    def validate_sales_owner_exists(record_data: Dict[str, Any], existing_users: List[int], field_name: str = 'sales_owner_id') -> bool:
        """
        Validate that sales owner exists for opportunities/projects.
        """
        owner_id = record_data.get(field_name)
        
        if owner_id not in existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: {owner_id}. User does not exist."
            )
        return True
    
    @staticmethod
    def validate_terminal_customer_exists(record_data: Dict[str, Any], existing_customers: List[int]) -> bool:
        """
        Validate that terminal customer exists for opportunities/projects.
        """
        customer_id = record_data.get('terminal_customer_id')
        
        if customer_id not in existing_customers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid terminal_customer_id: {customer_id}. Customer does not exist."
            )
        return True