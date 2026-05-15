from app.database import Base
from app.models.user import User, FeishuEmploymentStatus
from app.models.product import Product
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.contract import Contract
from app.models.followup import FollowUp
from app.models.dict_item import DictItem
from app.models.auto_number import AutoNumber
from app.models.lead import Lead
from app.models.operation_log import OperationLog
from app.models.sales_target import SalesTarget
from app.models.actual_performance import ActualPerformance
from app.models.nine_a import NineA
from app.models.nine_a_version import NineAVersion
from app.models.dispatch_record import DispatchRecord
from app.models.channel_contact import ChannelContact

from app.models.channel_assignment import ChannelAssignment
from app.models.unified_target import UnifiedTarget
from app.models.execution_plan import ExecutionPlan
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.evaluation import Evaluation
from app.models.knowledge import Knowledge
from app.models.product_installation import ProductInstallation
from app.models.customer_channel_link import CustomerChannelLink
from app.models.work_report import WorkReport
from app.models.work_report_comment import WorkReportComment
from app.models.notification import Notification
from app.models.feishu_org_sync_run import FeishuOrgSyncRun
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.models.employee_handover_log import EmployeeHandoverLog, HandoverLogOperation

__all__ = [
    "Base",
    "User",
    "FeishuEmploymentStatus",
    "Product",
    "TerminalCustomer",
    "Channel",
    "Opportunity",
    "Project",
    "Contract",
    "FollowUp",
    "DictItem",
    "AutoNumber",
    "Lead",
    "OperationLog",
    "SalesTarget",
    "ActualPerformance",
    "NineA",
    "NineAVersion",
    "DispatchRecord",
    "ChannelContact",
    "ChannelAssignment",
    "UnifiedTarget",
    "ExecutionPlan",
    "WorkOrder",
    "WorkOrderTechnician",
    "Evaluation",
    "Knowledge",
    "ProductInstallation",
    "CustomerChannelLink",
    "WorkReport",
    "WorkReportComment",
    "Notification",
    "FeishuOrgSyncRun",
    "EmployeeHandoverRequest",
    "HandoverRequestStatus",
    "EmployeeHandoverLog",
    "HandoverLogOperation",
]
