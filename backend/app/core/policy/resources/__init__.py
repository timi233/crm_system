from ..registry import register_policy

from .lead import LeadPolicy
from .customer import CustomerPolicy
from .opportunity import OpportunityPolicy
from .channel import ChannelPolicy
from .work_order import WorkOrderPolicy
from .follow_up import FollowUpPolicy
from .project import ProjectPolicy
from .contract import ContractPolicy
from .user import UserPolicy
from .product import ProductPolicy
from .operation_log import OperationLogPolicy
from .alert import AlertPolicy
from .alert_rule import AlertRulePolicy
from .sales_target import SalesTargetPolicy

register_policy("lead", LeadPolicy)
register_policy("customer", CustomerPolicy)
register_policy("opportunity", OpportunityPolicy)
register_policy("channel", ChannelPolicy)
register_policy("work_order", WorkOrderPolicy)
register_policy("follow_up", FollowUpPolicy)
register_policy("project", ProjectPolicy)
register_policy("contract", ContractPolicy)
register_policy("user", UserPolicy)
register_policy("product", ProductPolicy)
register_policy("operation_log", OperationLogPolicy)
register_policy("alert", AlertPolicy)
register_policy("alert_rule", AlertRulePolicy)
register_policy("sales_target", SalesTargetPolicy)
