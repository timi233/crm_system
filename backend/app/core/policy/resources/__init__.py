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
from .evaluation import EvaluationPolicy
from .execution_plan import ExecutionPlanPolicy
from .unified_target import UnifiedTargetPolicy
from .channel_assignment import ChannelAssignmentPolicy
from .knowledge import KnowledgePolicy
from .dashboard import DashboardPolicy
from .report import ReportPolicy
from .dispatch_record import DispatchRecordPolicy
from .opportunity_conversion import OpportunityConversionPolicy
from .dict_item import DictItemPolicy
from .financial_export import FinancialExportPolicy
from .customer_finance_view import CustomerFinanceViewPolicy
from .kingdee_integration import KingdeeIntegrationPolicy

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
register_policy("evaluation", EvaluationPolicy)
register_policy("execution_plan", ExecutionPlanPolicy)
register_policy("unified_target", UnifiedTargetPolicy)
register_policy("channel_assignment", ChannelAssignmentPolicy)
register_policy("knowledge", KnowledgePolicy)
register_policy("dashboard", DashboardPolicy)
register_policy("report", ReportPolicy)
register_policy("dispatch_record", DispatchRecordPolicy)
register_policy("opportunity_conversion", OpportunityConversionPolicy)
register_policy("dict_item", DictItemPolicy)
register_policy("financial_export", FinancialExportPolicy)
register_policy("customer_finance_view", CustomerFinanceViewPolicy)
register_policy("kingdee_integration", KingdeeIntegrationPolicy)
