"""
Configuration file for CRM data migration.
"""

import os
from pathlib import Path

class MigrationConfig:
    """Configuration class for data migration."""
    
    # Database configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/crm_db"
    )
    
    # Source data paths
    SOURCE_DATA_PATH = Path(os.getenv(
        "SOURCE_DATA_PATH", 
        "D:/项目材料/业财一体"
    ))
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "migration.log")
    
    # Migration settings
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    
    # Product standardization mapping
    PRODUCT_MAPPING = {
        "ipg": "IPGuard",
        "IPG": "IPGuard",
        "IPguard": "IPGuard", 
        "ipguard": "IPGuard",
        "爱数": "Aisino",
        "绿盟": "NSFOCUS",
        "深信服": "Sangfor",
        "火绒": "Huorong"
    }
    
    # Industry mapping
    INDUSTRY_MAPPING = {
        "制造业": "Manufacturing",
        "金融": "Finance",
        "政府/事业单位": "Government", 
        "医疗": "Healthcare",
        "教育": "Education",
        "能源化工": "Energy",
        "其他": "Other"
    }
    
    # Customer status mapping  
    CUSTOMER_STATUS_MAPPING = {
        "潜在客户": "Potential",
        "活跃客户": "Active",
        "存量客户": "Existing", 
        "流失客户": "Lost"
    }
    
    # Opportunity source mapping
    OPPORTUNITY_SOURCE_MAPPING = {
        "销售直拓": "Direct Sales",
        "渠道带入": "Channel",
        "老客户转介绍": "Customer Referral", 
        "老客户续保/扩容": "Renewal/Expansion"
    }
    
    # Opportunity stage mapping
    OPPORTUNITY_STAGE_MAPPING = {
        "初步接触": "Initial Contact",
        "需求确认": "Needs Confirmation", 
        "方案报价": "Proposal",
        "厂家报备中": "Vendor Registration",
        "等待决策": "Decision Pending",
        "赢单→转项目": "Won→Project",
        "丢单": "Lost"
    }

# Create global config instance
config = MigrationConfig()