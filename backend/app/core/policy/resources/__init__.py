"""
统一策略层资源 Policy 子包

Phase 2: 迁移高频资源
- lead, customer, opportunity, channel
"""

from ..registry import register_policy

from .lead import LeadPolicy
from .customer import CustomerPolicy
from .opportunity import OpportunityPolicy
from .channel import ChannelPolicy

register_policy("lead", LeadPolicy)
register_policy("customer", CustomerPolicy)
register_policy("opportunity", OpportunityPolicy)
register_policy("channel", ChannelPolicy)
