"""
统一策略层

Phase 1: 建立骨架，不改行为
- 定义核心类型（Action, Resource, PolicyDecision）
- 定义 PrincipalContext
- 定义 BasePolicy 基类
- 定义 PolicyService 统一入口
- 定义 registry 注册机制
- 定义 helpers 通用工具

Phase 2: 迁移高频资源
- lead, customer, opportunity, channel

Phase 3-5: 逐步迁移其他资源，删除旧入口
"""

from .types import Action, Resource, PolicyDecision, PolicyResult, AllActions
from .context import PrincipalContext
from .base import BasePolicy, DefaultPolicy
from .registry import (
    register_policy,
    get_policy_class,
    is_registered,
    list_registered_resources,
)
from .service import PolicyService, policy_service, build_principal
from . import resources
from .helpers import (
    is_admin,
    is_business,
    is_sales,
    is_finance,
    is_technician,
    has_full_access,
    has_read_only_full_access,
    matches_owner,
    owner_filter,
    get_assigned_channel_ids,
    get_technician_work_order_ids,
    get_technician_related_customer_ids,
    get_technician_related_channel_ids,
    get_technician_related_lead_ids,
    get_technician_related_opportunity_ids,
    get_technician_related_project_ids,
)

__all__ = [
    # Types
    "Action",
    "Resource",
    "PolicyDecision",
    "PolicyResult",
    "AllActions",
    # Context
    "PrincipalContext",
    # Base
    "BasePolicy",
    "DefaultPolicy",
    # Registry
    "register_policy",
    "get_policy_class",
    "is_registered",
    "list_registered_resources",
    # Service
    "PolicyService",
    "policy_service",
    "build_principal",
    # Helpers
    "is_admin",
    "is_business",
    "is_sales",
    "is_finance",
    "is_technician",
    "has_full_access",
    "has_read_only_full_access",
    "matches_owner",
    "owner_filter",
    "get_assigned_channel_ids",
    "get_technician_work_order_ids",
    "get_technician_related_customer_ids",
    "get_technician_related_channel_ids",
    "get_technician_related_lead_ids",
    "get_technician_related_opportunity_ids",
    "get_technician_related_project_ids",
]
