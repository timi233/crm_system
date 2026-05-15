from datetime import date, timedelta
from typing import Any, List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.followup import FollowUp
from app.models.contract import Contract
from app.models.work_order import WorkOrder, WorkOrderTechnician, WorkOrderStatus, WorkOrderPriority
from app.models.work_report import WorkReport
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.models.user import User
from app.schemas.todo import TodoRead, TodoFilterParams


class TodoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_todos(
        self,
        user_id: int,
        role: str,
        filters: TodoFilterParams,
    ) -> List[TodoRead]:
        todos: List[TodoRead] = []

        if role in ("sales", "technician", "channel_ops"):
            todos.extend(await self._get_follow_up_todos(user_id, role))
            todos.extend(await self._get_work_report_todos(user_id, role))

        if role == "technician":
            todos.extend(await self._get_work_order_todos_technician(user_id))

        if role in ("admin", "business"):
            todos.extend(await self._get_work_order_todos_admin(role))
            todos.extend(await self._get_handover_todos_admin())

        if role == "admin":
            todos.extend(await self._get_contract_expiry_todos())

        todos = self._apply_filters(todos, filters)
        return todos

    async def _get_follow_up_todos(self, user_id: int, role: str) -> List[TodoRead]:
        today = date.today()
        future_7_days = today + timedelta(days=7)

        result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.follower_id == user_id,
                FollowUp.next_follow_up_date != None,
                FollowUp.next_follow_up_date <= future_7_days,
                FollowUp.follow_up_type == ("business" if role == "sales" else "channel"),
            ).order_by(FollowUp.next_follow_up_date)
        )
        followups = result.scalars().all()

        todos = []
        for f in followups:
            entity_type, entity_id, link = self._resolve_followup_link(f)
            priority = "high" if f.next_follow_up_date and f.next_follow_up_date <= today else "normal"

            todos.append(TodoRead(
                key=f"follow_up:{f.id}",
                type="follow_up",
                title=f.next_action[:60] if f.next_action else "跟进提醒",
                description=f.follow_up_content[:100] if f.follow_up_content else None,
                priority=priority,
                due_date=str(f.next_follow_up_date) if f.next_follow_up_date else None,
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                source="follow_up",
                status="open",
            ))
        return todos

    def _resolve_followup_link(self, f: FollowUp) -> tuple[Optional[str], Optional[int], str]:
        if f.lead_id:
            return "lead", f.lead_id, f"/leads/{f.lead_id}/full"
        if f.opportunity_id:
            return "opportunity", f.opportunity_id, f"/opportunities/{f.opportunity_id}/full"
        if f.project_id:
            return "project", f.project_id, f"/projects/{f.project_id}/full"
        if f.terminal_customer_id:
            return "customer", f.terminal_customer_id, f"/customers/{f.terminal_customer_id}/full"
        if f.channel_id:
            return "channel", f.channel_id, f"/channels/{f.channel_id}/full"
        return None, None, "/business-follow-ups" if f.follow_up_type == "business" else "/channel-follow-ups"

    async def _get_contract_expiry_todos(self) -> List[TodoRead]:
        today = date.today()
        future_30_days = today + timedelta(days=30)

        result = await self.db.execute(
            select(Contract).where(
                Contract.expiry_date != None,
                Contract.expiry_date <= future_30_days,
                Contract.contract_status == "signed",
            ).order_by(Contract.expiry_date)
        )
        contracts = result.scalars().all()

        todos = []
        for c in contracts:
            priority = "high" if c.expiry_date and c.expiry_date <= today else "medium"

            todos.append(TodoRead(
                key=f"contract_expiry:{c.id}",
                type="contract_expiry",
                title=f"合同即将到期：{c.contract_name}",
                description=f"合同编号 {c.contract_code}，到期日期 {c.expiry_date}",
                priority=priority,
                due_date=str(c.expiry_date) if c.expiry_date else None,
                entity_type="contract",
                entity_id=c.id,
                link=f"/contracts/{c.id}/full",
                source="contract",
                status="open",
            ))
        return todos

    async def _get_work_order_todos_technician(self, user_id: int) -> List[TodoRead]:
        pending_result = await self.db.execute(
            select(WorkOrder).join(WorkOrderTechnician).where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrderTechnician.status == "PENDING",
            ).order_by(WorkOrder.priority, WorkOrder.created_at)
        )
        pending_orders = pending_result.scalars().all()

        in_progress_result = await self.db.execute(
            select(WorkOrder).join(WorkOrderTechnician).where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.status == WorkOrderStatus.IN_SERVICE,
            ).order_by(WorkOrder.priority, WorkOrder.created_at)
        )
        in_progress_orders = in_progress_result.scalars().all()

        todos = []
        for wo in pending_orders:
            priority = self._map_work_order_priority(wo.priority)
            todos.append(TodoRead(
                key=f"work_order:{wo.id}:pending",
                type="work_order",
                title=f"待接单：{wo.work_order_no}",
                description=wo.description[:100] if wo.description else wo.customer_name,
                priority=priority,
                due_date=str(wo.estimated_start_date) if wo.estimated_start_date else None,
                entity_type="work_order",
                entity_id=wo.id,
                link=f"/work-orders/{wo.id}",
                source="work_order",
                status="open",
            ))

        for wo in in_progress_orders:
            priority = "normal"
            todos.append(TodoRead(
                key=f"work_order:{wo.id}:in_progress",
                type="work_order",
                title=f"进行中：{wo.work_order_no}",
                description=wo.description[:100] if wo.description else wo.customer_name,
                priority=priority,
                due_date=str(wo.estimated_end_date) if wo.estimated_end_date else None,
                entity_type="work_order",
                entity_id=wo.id,
                link=f"/work-orders/{wo.id}",
                source="work_order",
                status="open",
            ))
        return todos

    async def _get_work_order_todos_admin(self, role: str) -> List[TodoRead]:
        pending_result = await self.db.execute(
            select(WorkOrder).where(
                WorkOrder.status == WorkOrderStatus.PENDING,
            ).order_by(WorkOrder.priority, WorkOrder.created_at)
        )
        pending_orders = pending_result.scalars().all()

        in_service_result = await self.db.execute(
            select(WorkOrder).where(
                WorkOrder.status == WorkOrderStatus.IN_SERVICE,
            ).order_by(WorkOrder.priority, WorkOrder.created_at).limit(20)
        )
        in_service_orders = in_service_result.scalars().all()

        todos = []
        for wo in pending_orders:
            priority = self._map_work_order_priority(wo.priority)
            todos.append(TodoRead(
                key=f"work_order:{wo.id}:pending",
                type="work_order",
                title=f"待接单：{wo.work_order_no}",
                description=wo.description[:100] if wo.description else wo.customer_name,
                priority=priority,
                due_date=str(wo.estimated_start_date) if wo.estimated_start_date else None,
                entity_type="work_order",
                entity_id=wo.id,
                link=f"/work-orders/{wo.id}",
                source="work_order",
                status="open",
            ))

        for wo in in_service_orders:
            priority = "normal"
            todos.append(TodoRead(
                key=f"work_order:{wo.id}:in_service",
                type="work_order",
                title=f"进行中：{wo.work_order_no}",
                description=wo.description[:100] if wo.description else wo.customer_name,
                priority=priority,
                due_date=str(wo.estimated_end_date) if wo.estimated_end_date else None,
                entity_type="work_order",
                entity_id=wo.id,
                link=f"/work-orders/{wo.id}",
                source="work_order",
                status="open",
            ))
        return todos

    def _map_work_order_priority(self, priority: Any) -> str:
        if priority is None:
            return "normal"
        p = priority.value if hasattr(priority, 'value') else str(priority)
        if p in ("VERY_URGENT", "URGENT"):
            return "high"
        return "normal"

    async def _get_work_report_todos(self, user_id: int, role: str) -> List[TodoRead]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        today_weekday = today.weekday()

        todos = []

        daily_result = await self.db.execute(
            select(WorkReport).where(
                WorkReport.owner_id == user_id,
                WorkReport.report_type == "daily",
                WorkReport.report_date == today,
            )
        )
        daily_report = daily_result.scalar_one_or_none()

        if not daily_report or daily_report.status in ("draft", "withdrawn"):
            todos.append(TodoRead(
                key="work_report:daily:missing",
                type="work_report",
                title="今日日报未提交",
                description="生成并提交今天的工作报告",
                priority="high",
                due_date=str(today),
                entity_type="work_report",
                entity_id=None,
                link="/work-reports",
                source="work_report",
                status="open",
            ))

        if today_weekday >= 4:
            weekly_result = await self.db.execute(
                select(WorkReport).where(
                    WorkReport.owner_id == user_id,
                    WorkReport.report_type == "weekly",
                    WorkReport.report_date == week_start,
                )
            )
            weekly_report = weekly_result.scalar_one_or_none()

            if not weekly_report or weekly_report.status in ("draft", "withdrawn"):
                todos.append(TodoRead(
                    key="work_report:weekly:missing",
                    type="work_report",
                    title="本周周报未提交",
                    description="生成并提交本周工作报告",
                    priority="medium",
                    due_date=str(week_start + timedelta(days=6)),
                    entity_type="work_report",
                    entity_id=None,
                    link="/work-reports",
                    source="work_report",
                    status="open",
                ))
        return todos

    async def _get_handover_todos_admin(self) -> List[TodoRead]:
        pending_assignment_result = await self.db.execute(
            select(EmployeeHandoverRequest).where(
                EmployeeHandoverRequest.status == HandoverRequestStatus.PENDING_ASSIGNMENT,
            ).order_by(EmployeeHandoverRequest.created_at)
        )
        pending_assignment = pending_assignment_result.scalars().all()

        pending_execution_result = await self.db.execute(
            select(EmployeeHandoverRequest).where(
                EmployeeHandoverRequest.status == HandoverRequestStatus.PENDING_EXECUTION,
            ).order_by(EmployeeHandoverRequest.decided_at)
        )
        pending_execution = pending_execution_result.scalars().all()

        todos = []
        for h in pending_assignment:
            todos.append(TodoRead(
                key=f"handover:{h.id}:pending_assignment",
                type="handover",
                title="离职交接待分配",
                description=f"员工 {h.from_user_id} 离职交接待分配接手人",
                priority="high",
                due_date=None,
                entity_type="handover_request",
                entity_id=h.id,
                link=f"/handovers/{h.id}",
                source="handover",
                status="open",
            ))

        for h in pending_execution:
            todos.append(TodoRead(
                key=f"handover:{h.id}:pending_execution",
                type="handover",
                title="离职交接待执行",
                description=f"员工 {h.from_user_id} 离职交接待执行",
                priority="high",
                due_date=None,
                entity_type="handover_request",
                entity_id=h.id,
                link=f"/handovers/{h.id}",
                source="handover",
                status="open",
            ))
        return todos

    def _apply_filters(self, todos: List[TodoRead], filters: TodoFilterParams) -> List[TodoRead]:
        if filters.type:
            todos = [t for t in todos if t.type == filters.type]
        if filters.priority:
            todos = [t for t in todos if t.priority == filters.priority]
        if filters.status:
            todos = [t for t in todos if t.status == filters.status]
        if filters.date_from:
            todos = [t for t in todos if t.due_date and date.fromisoformat(t.due_date) >= filters.date_from]
        if filters.date_to:
            todos = [t for t in todos if t.due_date and date.fromisoformat(t.due_date) <= filters.date_to]
        return todos