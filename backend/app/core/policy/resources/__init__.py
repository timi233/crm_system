"""
统一策略层资源 Policy 子包

Phase 2: 迁移高频资源
- lead, customer, opportunity, channel

Phase 3: 迁移工单链路
- work_order, follow_up, project, contract
"""

from ..registry import register_policy

from .lead import LeadPolicy
from .customer import CustomerPolicy
from .opportunity import OpportunityPolicy
from .channel import ChannelPolicy
from .work_order import WorkOrderPolicy
from .follow_up import FollowUpPolicy
from .project import ProjectPolicy
from .contract import ContractPolicy

register_policy("lead", LeadPolicy)
register_policy("customer", CustomerPolicy)
register_policy("opportunity", OpportunityPolicy)
register_policy("channel", ChannelPolicy)
register_policy("work_order", WorkOrderPolicy)
register_policy("follow_up", FollowUpPolicy)
register_policy("project", ProjectPolicy)
register_policy("contract", ContractPolicy)
