"""
Role-based access control middleware for CRM system.
Implements field-level permissions and route-level role validation.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

class RBACMiddleware:
    """Middleware for role-based access control."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_route_access(self, user_role: str, endpoint: str) -> bool:
        """Check if user role has access to specific endpoint."""
        
        # Define route permissions
        route_permissions = {
            # User management (admin only)
            'users': ['admin'],
            
            # Customer management (sales, business, admin)
            'customers': ['admin', 'sales', 'business'],
            
            # Channel management (business, admin)
            'channels': ['admin', 'business'],
            
            # Opportunity management (sales, business, admin)
            'opportunities': ['admin', 'sales', 'business'],
            
            # Project management (sales, business, admin)
            'projects': ['admin', 'sales', 'business'],
            
            # Contract management (business, admin)
            'contracts': ['admin', 'business'],
            
            # Follow-up management (sales, business, admin)
            'follow-ups': ['admin', 'sales', 'business'],
            
            # Product management (business, admin)
            'products': ['admin', 'business'],
            
            # Financial export (finance, admin)
            'financials/export': ['admin', 'finance']
        }
        
        # Extract base endpoint name from full path
        base_endpoint = endpoint.split('/')[0] if '/' in endpoint else endpoint
        
        allowed_roles = route_permissions.get(base_endpoint, ['admin'])
        return user_role in allowed_roles
    
    def filter_response_fields(self, user_role: str, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter response fields based on user role and resource type.
        Removes sensitive fields that the user shouldn't see.
        """
        
        # Make a copy to avoid modifying original data
        filtered_data = data.copy()
        
        if user_role == 'sales':
            # Sales should not see financial details
            if resource_type == 'projects':
                # Remove procurement costs and margins
                sensitive_fields = [
                    'upstream_procurement_amount',
                    'direct_project_investment', 
                    'additional_investment',
                    'gross_margin'
                ]
                for field in sensitive_fields:
                    filtered_data.pop(field, None)
            
            elif resource_type == 'contracts':
                # Sales can see contract amounts but not procurement details
                pass  # Keep all contract fields visible to sales
        
        elif user_role == 'finance':
            # Finance has read-only access to most fields
            # For now, finance can see all fields but cannot modify
            pass
        
        # Business and admin see all fields
        return filtered_data
    
    def validate_field_access(self, user_role: str, resource_type: str, field_name: str, action: str = 'read') -> bool:
        """
        Validate if user can access specific field for given action.
        Action can be 'read' or 'write'.
        """
        
        # Define field-level permissions
        field_permissions = {
            'projects': {
                'upstream_procurement_amount': ['admin', 'business', 'finance'],
                'direct_project_investment': ['admin', 'business', 'finance'], 
                'additional_investment': ['admin', 'business', 'finance'],
                'gross_margin': ['admin', 'business', 'finance']
            },
            'contracts': {
                'counterparty_id': ['admin', 'business'],
                'contract_file_url': ['admin', 'business']
            }
        }
        
        # If field is not in permissions, allow access
        if resource_type not in field_permissions:
            return True
            
        if field_name not in field_permissions[resource_type]:
            return True
        
        # Check if user role has access to this field
        allowed_roles = field_permissions[resource_type][field_name]
        return user_role in allowed_roles
    
    def require_role(self, user_role: str, required_roles: List[str], resource: str = ""):
        """Raise exception if user doesn't have required role."""
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}, your role: {user_role}"
            )