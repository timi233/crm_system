from app.database import Base
from app.models.user import User
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
from app.models.nine_a import NineA
from app.models.nine_a_version import NineAVersion
from app.models.dispatch_record import DispatchRecord

from app.models.channel_assignment import ChannelAssignment
from app.models.unified_target import UnifiedTarget
from app.models.execution_plan import ExecutionPlan
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.evaluation import Evaluation
from app.models.knowledge import Knowledge
from app.models.product_installation import ProductInstallation
from app.models.customer_channel_link import CustomerChannelLink

__all__ = [
    "Base",
    "User",
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
    "NineA",
    "NineAVersion",
    "DispatchRecord",
    "ChannelAssignment",
    "UnifiedTarget",
    "ExecutionPlan",
    "WorkOrder",
    "WorkOrderTechnician",
    "Evaluation",
    "Knowledge",
    "ProductInstallation",
    "CustomerChannelLink",
]
