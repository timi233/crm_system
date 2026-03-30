"""
Auto-numbering service for CRM system.
Handles automatic generation of formatted codes for all 7 table types.
"""

import re
from datetime import datetime
from typing import Optional
from threading import Lock
from sqlalchemy import text
from sqlalchemy.orm import Session

class AutoNumberService:
    """Service for generating auto-numbered codes with proper formatting."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.locks = {
            'CUS': Lock(),
            'CH': Lock(), 
            'OPP': Lock(),
            'PRJ': Lock(),
            'PRD': Lock()
        }
    
    def generate_customer_code(self) -> str:
        """Generate customer code: CUS-YYYYMM-001"""
        return self._generate_code('CUS', 'customer_code_seq')
    
    def generate_channel_code(self) -> str:
        """Generate channel code: CH-YYYYMM-001"""
        return self._generate_code('CH', 'channel_code_seq')
    
    def generate_opportunity_code(self) -> str:
        """Generate opportunity code: OPP-YYYYMM-001"""
        return self._generate_code('OPP', 'opportunity_code_seq')
    
    def generate_project_code(self, is_renewal: bool = False) -> str:
        """Generate project code: PRJ-YYYYMM-001 or PRJ-YYYYMM-001-SVC"""
        base_code = self._generate_code('PRJ', 'project_code_seq')
        if is_renewal:
            return f"{base_code}-SVC"
        return base_code
    
    def generate_product_code(self) -> str:
        """Generate product code: PRD-001"""
        # Product codes don't include date, just sequence
        result = self.db.execute(text("SELECT nextval('product_code_seq')"))
        seq_num = result.scalar()
        return f"PRD-{seq_num:03d}"
    
    def _generate_code(self, prefix: str, sequence_name: str) -> str:
        """Generate formatted code with year-month and sequence number."""
        with self.locks[prefix]:
            # Get current year-month
            year_month = datetime.now().strftime("%Y%m")
            
            # Get next sequence number
            result = self.db.execute(text(f"SELECT nextval('{sequence_name}')"))
            seq_num = result.scalar()
            
            return f"{prefix}-{year_month}-{seq_num:03d}"
    
    def detect_renewal(self, opportunity_name: str, business_type: str) -> bool:
        """Detect if this should be a renewal project based on name or business type."""
        renewal_keywords = ['续保', '续报', 'renewal', 'Renewal', 'SVC']
        
        # Check opportunity name
        if any(keyword.lower() in opportunity_name.lower() for keyword in renewal_keywords):
            return True
        
        # Check business type  
        if business_type in ['Renewal/Maintenance', '续保/维保']:
            return True
            
        return False