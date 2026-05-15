from datetime import date, datetime, timedelta
from typing import Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.contract import Contract
from app.models.followup import FollowUp
from app.models.work_order import WorkOrder, WorkOrderTechnician, WorkOrderStatus
from app.models.channel import Channel
from app.models.execution_plan import ExecutionPlan, ExecutionPlanStatus
from app.models.sales_target import SalesTarget
from app.models.alert_rule import AlertRule
from app.models.operation_log import OperationLog
from app.models.work_report import WorkReport
from app.schemas.dashboard import (
    DashboardWorkbenchResponse,
    DashboardMetricCard,
    DashboardTodoItemNew,
    DashboardRiskItem,
    DashboardQuickAction,
    DashboardReportStatus,
)


class DashboardWorkbenchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_workbench(
        self,
        user_id: int,
        role: str,
        department_manager_id: Optional[int] = None,
    ) -> DashboardWorkbenchResponse:
        generated_at = datetime.now().isoformat()

        if role == "admin":
            return await self._build_admin_workbench(user_id, generated_at)
        elif role == "business":
            return await self._build_business_workbench(user_id, department_manager_id, generated_at)
        elif role == "sales":
            workbench = await self._build_sales_workbench(user_id, generated_at)
            return await self._apply_department_manager_report_status(workbench, user_id)
        elif role == "finance":
            return await self._build_finance_workbench(user_id, generated_at)
        elif role == "technician":
            workbench = await self._build_technician_workbench(user_id, generated_at)
            return await self._apply_department_manager_report_status(workbench, user_id)
        elif role == "channel_ops":
            workbench = await self._build_channel_ops_workbench(user_id, generated_at)
            return await self._apply_department_manager_report_status(workbench, user_id)
        else:
            return DashboardWorkbenchResponse(
                role=role,
                scope="personal",
                metrics=[],
                todos=[],
                risks=[],
                quick_actions=[],
                generated_at=generated_at,
            )

    async def _build_admin_workbench(
        self,
        user_id: int,
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        users_result = await self.db.execute(select(func.count()).select_from(User))
        users_count = users_result.scalar() or 0

        alerts_result = await self.db.execute(select(func.count()).select_from(AlertRule))
        alerts_count = alerts_result.scalar() or 0

        logs_result = await self.db.execute(
            select(func.count()).select_from(OperationLog)
        )
        logs_count = logs_result.scalar() or 0

        leads_result = await self.db.execute(select(func.count()).select_from(Lead))
        leads_count = leads_result.scalar() or 0

        opps_result = await self.db.execute(select(func.count()).select_from(Opportunity))
        opps_count = opps_result.scalar() or 0

        metrics = [
            DashboardMetricCard(key="users", title="用户总数", value=users_count, unit="人", link="/users"),
            DashboardMetricCard(key="alerts", title="告警规则", value=alerts_count, unit="条", link="/alert-rules"),
            DashboardMetricCard(key="logs", title="操作日志", value=logs_count, unit="条", link="/operation-logs"),
            DashboardMetricCard(key="leads", title="线索总数", value=leads_count, unit="条", link="/leads"),
            DashboardMetricCard(key="opportunities", title="商机总数", value=opps_count, unit="条", link="/opportunities"),
        ]

        quick_actions = [
            DashboardQuickAction(key="users", title="用户管理", link="/users", capability="user:read"),
            DashboardQuickAction(key="logs", title="操作日志", link="/operation-logs", capability="operation_log:read"),
            DashboardQuickAction(key="alerts", title="预警中心", link="/alert-rules", capability="alert_rule:manage"),
            DashboardQuickAction(key="dict", title="数据字典", link="/dict-items", capability="dict_item:read"),
        ]

        return DashboardWorkbenchResponse(
            role="admin",
            scope="global",
            metrics=metrics,
            todos=[],
            risks=[],
            quick_actions=quick_actions,
            generated_at=generated_at,
        )

    async def _build_business_workbench(
        self,
        user_id: int,
        department_manager_id: Optional[int],
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        leads_result = await self.db.execute(select(func.count()).select_from(Lead))
        leads_count = leads_result.scalar() or 0

        opps_result = await self.db.execute(select(func.count()).select_from(Opportunity))
        opps_count = opps_result.scalar() or 0

        projects_result = await self.db.execute(select(func.count()).select_from(Project))
        projects_count = projects_result.scalar() or 0

        contracts_result = await self.db.execute(select(func.count()).select_from(Contract))
        contracts_count = contracts_result.scalar() or 0

        targets_result = await self.db.execute(
            select(func.count()).select_from(SalesTarget).where(
                SalesTarget.target_year == date.today().year
            )
        )
        targets_count = targets_result.scalar() or 0

        metrics = [
            DashboardMetricCard(key="leads", title="线索总数", value=leads_count, unit="条", link="/leads"),
            DashboardMetricCard(key="opportunities", title="商机总数", value=opps_count, unit="条", link="/opportunities"),
            DashboardMetricCard(key="projects", title="项目总数", value=projects_count, unit="个", link="/projects"),
            DashboardMetricCard(key="contracts", title="合同总数", value=contracts_count, unit="份", link="/contracts"),
            DashboardMetricCard(key="targets", title="销售目标", value=targets_count, unit="项", link="/sales-targets"),
        ]

        report_status = await self._get_team_report_status(user_id, department_manager_id)

        quick_actions = [
            DashboardQuickAction(key="targets", title="目标管理", link="/sales-targets", capability="sales_target:read"),
            DashboardQuickAction(key="reports", title="日报/周报", link="/work-reports", capability="work_report:team_read"),
            DashboardQuickAction(key="opportunities", title="商机管理", link="/opportunities", capability="opportunity:read"),
            DashboardQuickAction(key="reports-funnel", title="销售漏斗", link="/reports/sales-funnel", capability="report:read"),
        ]

        return DashboardWorkbenchResponse(
            role="business",
            scope="team",
            metrics=metrics,
            todos=[],
            risks=[],
            quick_actions=quick_actions,
            report_status=report_status,
            generated_at=generated_at,
        )

    async def _build_sales_workbench(
        self,
        user_id: int,
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        leads_result = await self.db.execute(
            select(func.count()).select_from(Lead).where(Lead.sales_owner_id == user_id)
        )
        leads_count = leads_result.scalar() or 0

        opps_result = await self.db.execute(
            select(func.count()).select_from(Opportunity).where(Opportunity.sales_owner_id == user_id)
        )
        opps_count = opps_result.scalar() or 0

        targets_result = await self.db.execute(
            select(func.count()).select_from(SalesTarget).where(
                SalesTarget.user_id == user_id,
                SalesTarget.target_year == date.today().year,
            )
        )
        targets_count = targets_result.scalar() or 0

        followups_result = await self.db.execute(
            select(func.count()).select_from(FollowUp).where(
                FollowUp.follower_id == user_id,
                FollowUp.follow_up_type == "business",
            )
        )
        followups_count = followups_result.scalar() or 0

        metrics = [
            DashboardMetricCard(key="leads", title="我的线索", value=leads_count, unit="条", link="/leads"),
            DashboardMetricCard(key="opportunities", title="我的商机", value=opps_count, unit="条", link="/opportunities"),
            DashboardMetricCard(key="targets", title="销售目标", value=targets_count, unit="项", link="/sales-targets"),
            DashboardMetricCard(key="followups", title="跟进记录", value=followups_count, unit="条", link="/business-follow-ups"),
        ]

        pending_followups_result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.follower_id == user_id,
                FollowUp.follow_up_type == "business",
                FollowUp.next_action != None,
            ).limit(5)
        )
        pending_followups = pending_followups_result.scalars().all()

        todos = []
        for f in pending_followups:
            todos.append(
                DashboardTodoItemNew(
                    key=f"followup-{f.id}",
                    title=f.next_action[:50] if f.next_action else "跟进任务",
                    description=f.follow_up_content[:100] if f.follow_up_content else None,
                    priority="high" if f.next_follow_up_date and f.next_follow_up_date <= date.today() else "normal",
                    due_date=str(f.next_follow_up_date) if f.next_follow_up_date else None,
                    link="/business-follow-ups",
                )
            )

        report_status = await self._get_personal_report_status(user_id)

        # Add unsubmitted report todos
        if report_status.daily == "not_created":
            todos.append(
                DashboardTodoItemNew(
                    key="daily_report_missing",
                    title="今日日报未提交",
                    description="生成并提交今天的工作报告",
                    priority="high",
                    link="/work-reports",
                )
            )

        today_weekday = date.today().weekday()
        if report_status.weekly == "not_created" and today_weekday >= 4:
            todos.append(
                DashboardTodoItemNew(
                    key="weekly_report_missing",
                    title="本周周报未提交",
                    description="生成并提交本周工作报告",
                    priority="medium",
                    link="/work-reports",
                )
            )

        quick_actions = [
            DashboardQuickAction(key="customers", title="终端客户", link="/customers", capability="customer:read"),
            DashboardQuickAction(key="leads", title="线索管理", link="/leads", capability="lead:read"),
            DashboardQuickAction(key="opportunities", title="商机管理", link="/opportunities", capability="opportunity:read"),
            DashboardQuickAction(key="followups", title="业务跟进", link="/business-follow-ups", capability="follow_up:read"),
            DashboardQuickAction(key="reports", title="日报/周报", link="/work-reports", capability="work_report:create"),
        ]

        return DashboardWorkbenchResponse(
            role="sales",
            scope="personal",
            metrics=metrics,
            todos=todos,
            risks=[],
            quick_actions=quick_actions,
            report_status=report_status,
            generated_at=generated_at,
        )

    async def _build_finance_workbench(
        self,
        user_id: int,
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        contracts_result = await self.db.execute(select(func.count()).select_from(Contract))
        contracts_count = contracts_result.scalar() or 0

        downstream_result = await self.db.execute(
            select(func.sum(Contract.contract_amount)).select_from(Contract).where(
                Contract.contract_direction == "Downstream"
            )
        )
        total_amount = float(downstream_result.scalar() or 0)

        metrics = [
            DashboardMetricCard(key="contracts", title="合同总数", value=contracts_count, unit="份", link="/contracts"),
            DashboardMetricCard(key="amount", title="合同金额", value=total_amount, unit="元", link="/contracts"),
        ]

        quick_actions = [
            DashboardQuickAction(key="contracts", title="合同管理", link="/contracts", capability="contract:read"),
            DashboardQuickAction(key="payment", title="回款进度", link="/reports/payment-progress", capability="report:read"),
            DashboardQuickAction(key="performance", title="业绩报表", link="/reports/performance", capability="report:read"),
        ]

        return DashboardWorkbenchResponse(
            role="finance",
            scope="global",
            metrics=metrics,
            todos=[],
            risks=[],
            quick_actions=quick_actions,
            generated_at=generated_at,
        )

    async def _build_technician_workbench(
        self,
        user_id: int,
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        assigned_result = await self.db.execute(
            select(func.count()).select_from(WorkOrderTechnician).where(
                WorkOrderTechnician.technician_id == user_id
            )
        )
        assigned_count = assigned_result.scalar() or 0

        pending_result = await self.db.execute(
            select(func.count()).select_from(WorkOrderTechnician).where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrderTechnician.status == "PENDING",
            )
        )
        pending_count = pending_result.scalar() or 0

        in_progress_result = await self.db.execute(
            select(WorkOrder).join(WorkOrderTechnician).where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.status == WorkOrderStatus.IN_SERVICE,
            )
        )
        in_progress_orders = in_progress_result.scalars().all()
        in_progress_count = len(in_progress_orders)

        metrics = [
            DashboardMetricCard(key="assigned", title="分配工单", value=assigned_count, unit="个", link="/work-orders"),
            DashboardMetricCard(key="pending", title="待接单", value=pending_count, unit="个", link="/work-orders"),
            DashboardMetricCard(key="in_progress", title="进行中", value=in_progress_count, unit="个", link="/work-orders"),
        ]

        todos = []
        for wo in in_progress_orders[:3]:
            todos.append(
                DashboardTodoItemNew(
                    key=f"workorder-{wo.id}",
                    title=wo.description[:50] if wo.description else f"工单 #{wo.work_order_no}",
                    description=wo.customer_name,
                    priority="high" if wo.priority.value in ("URGENT", "VERY_URGENT") else "normal",
                    link=f"/work-orders/{wo.id}",
                )
            )

        report_status = await self._get_personal_report_status(user_id)

        # Add unsubmitted report todos
        if report_status.daily == "not_created":
            todos.append(
                DashboardTodoItemNew(
                    key="daily_report_missing",
                    title="今日日报未提交",
                    description="生成并提交今天的工作报告",
                    priority="high",
                    link="/work-reports",
                )
            )

        today_weekday = date.today().weekday()
        if report_status.weekly == "not_created" and today_weekday >= 4:
            todos.append(
                DashboardTodoItemNew(
                    key="weekly_report_missing",
                    title="本周周报未提交",
                    description="生成并提交本周工作报告",
                    priority="medium",
                    link="/work-reports",
                )
            )

        quick_actions = [
            DashboardQuickAction(key="workorders", title="工单管理", link="/work-orders", capability="work_order:read"),
            DashboardQuickAction(key="knowledge", title="知识库", link="/knowledge", capability="knowledge:read"),
            DashboardQuickAction(key="reports", title="日报/周报", link="/work-reports", capability="work_report:create"),
        ]

        return DashboardWorkbenchResponse(
            role="technician",
            scope="personal",
            metrics=metrics,
            todos=todos,
            risks=[],
            quick_actions=quick_actions,
            report_status=report_status,
            generated_at=generated_at,
        )

    async def _build_channel_ops_workbench(
        self,
        user_id: int,
        generated_at: str,
    ) -> DashboardWorkbenchResponse:
        channels_result = await self.db.execute(select(func.count()).select_from(Channel))
        channels_count = channels_result.scalar() or 0

        followups_result = await self.db.execute(
            select(func.count()).select_from(FollowUp).where(
                FollowUp.follow_up_type == "channel",
                FollowUp.follower_id == user_id,
            )
        )
        followups_count = followups_result.scalar() or 0

        plans_result = await self.db.execute(
            select(func.count()).select_from(ExecutionPlan).where(
                ExecutionPlan.user_id == user_id,
                ExecutionPlan.plan_category == "training",
                ExecutionPlan.status == ExecutionPlanStatus.planned,
            )
        )
        plans_count = plans_result.scalar() or 0

        metrics = [
            DashboardMetricCard(key="channels", title="渠道总数", value=channels_count, unit="家", link="/channels"),
            DashboardMetricCard(key="followups", title="渠道跟进", value=followups_count, unit="条", link="/channel-follow-ups"),
            DashboardMetricCard(key="plans", title="待执行计划", value=plans_count, unit="项", link="/channel-training"),
        ]

        report_status = await self._get_personal_report_status(user_id)

        todos = []

        # Add unsubmitted report todos
        if report_status.daily == "not_created":
            todos.append(
                DashboardTodoItemNew(
                    key="daily_report_missing",
                    title="今日日报未提交",
                    description="生成并提交今天的工作报告",
                    priority="high",
                    link="/work-reports",
                )
            )

        today_weekday = date.today().weekday()
        if report_status.weekly == "not_created" and today_weekday >= 4:
            todos.append(
                DashboardTodoItemNew(
                    key="weekly_report_missing",
                    title="本周周报未提交",
                    description="生成并提交本周工作报告",
                    priority="medium",
                    link="/work-reports",
                )
            )

        quick_actions = [
            DashboardQuickAction(key="channels", title="渠道档案", link="/channels", capability="channel:read"),
            DashboardQuickAction(key="followups", title="渠道跟进", link="/channel-follow-ups", capability="channel:read"),
            DashboardQuickAction(key="training", title="渠道培训", link="/channel-training", capability="channel_training:read"),
            DashboardQuickAction(key="performance", title="渠道绩效", link="/channel-performance", capability="channel_performance:read"),
            DashboardQuickAction(key="reports", title="日报/周报", link="/work-reports", capability="work_report:create"),
        ]

        return DashboardWorkbenchResponse(
            role="channel_ops",
            scope="personal",
            metrics=metrics,
            todos=todos,
            risks=[],
            quick_actions=quick_actions,
            report_status=report_status,
            generated_at=generated_at,
        )

    async def _get_personal_report_status(
        self,
        user_id: int,
    ) -> DashboardReportStatus:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        daily_result = await self.db.execute(
            select(WorkReport).where(
                WorkReport.owner_id == user_id,
                WorkReport.report_type == "daily",
                WorkReport.report_date == today,
            )
        )
        daily_report = daily_result.scalar_one_or_none()

        weekly_result = await self.db.execute(
            select(WorkReport).where(
                WorkReport.owner_id == user_id,
                WorkReport.report_type == "weekly",
                WorkReport.report_date == week_start,
            )
        )
        weekly_report = weekly_result.scalar_one_or_none()

        return DashboardReportStatus(
            daily=daily_report.status if daily_report else "not_created",
            weekly=weekly_report.status if weekly_report else "not_created",
            daily_draft_id=daily_report.id if daily_report else None,
            weekly_draft_id=weekly_report.id if weekly_report else None,
        )

    async def _apply_department_manager_report_status(
        self,
        workbench: DashboardWorkbenchResponse,
        user_id: int,
    ) -> DashboardWorkbenchResponse:
        members_result = await self.db.execute(
            select(User.id).where(User.department_manager_id == user_id).limit(1)
        )
        has_direct_members = members_result.scalar_one_or_none() is not None
        if not has_direct_members:
            return workbench

        workbench.scope = "team"
        workbench.report_status = await self._get_department_manager_team_report_status(user_id)
        return workbench

    async def _get_team_report_status(
        self,
        user_id: int,
        department_manager_id: Optional[int],
    ) -> DashboardReportStatus:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Business role: count all sales/technician/channel_ops users
        members_result = await self.db.execute(
            select(User.id).where(User.role.in_(("sales", "technician", "channel_ops")))
        )
        member_ids = [row[0] for row in members_result.fetchall()]
        total_count = len(member_ids)

        if total_count == 0:
            return DashboardReportStatus(
                daily="0/0 已提交",
                weekly="0/0 已提交",
            )

        daily_submitted_result = await self.db.execute(
            select(func.count()).select_from(WorkReport).where(
                WorkReport.owner_id.in_(member_ids),
                WorkReport.report_type == "daily",
                WorkReport.report_date == today,
                WorkReport.status == "submitted",
            )
        )
        daily_submitted_count = daily_submitted_result.scalar() or 0

        weekly_submitted_result = await self.db.execute(
            select(func.count()).select_from(WorkReport).where(
                WorkReport.owner_id.in_(member_ids),
                WorkReport.report_type == "weekly",
                WorkReport.report_date == week_start,
                WorkReport.status == "submitted",
            )
        )
        weekly_submitted_count = weekly_submitted_result.scalar() or 0

        return DashboardReportStatus(
            daily=f"{daily_submitted_count}/{total_count} 已提交",
            weekly=f"{weekly_submitted_count}/{total_count} 已提交",
        )

    async def _get_department_manager_team_report_status(
        self,
        user_id: int,
    ) -> DashboardReportStatus:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Department manager: count direct members only
        members_result = await self.db.execute(
            select(User.id).where(User.department_manager_id == user_id)
        )
        member_ids = [row[0] for row in members_result.fetchall()]
        total_count = len(member_ids)

        if total_count == 0:
            return DashboardReportStatus(
                daily="0/0 已提交",
                weekly="0/0 已提交",
            )

        daily_submitted_result = await self.db.execute(
            select(func.count()).select_from(WorkReport).where(
                WorkReport.owner_id.in_(member_ids),
                WorkReport.report_type == "daily",
                WorkReport.report_date == today,
                WorkReport.status == "submitted",
            )
        )
        daily_submitted_count = daily_submitted_result.scalar() or 0

        weekly_submitted_result = await self.db.execute(
            select(func.count()).select_from(WorkReport).where(
                WorkReport.owner_id.in_(member_ids),
                WorkReport.report_type == "weekly",
                WorkReport.report_date == week_start,
                WorkReport.status == "submitted",
            )
        )
        weekly_submitted_count = weekly_submitted_result.scalar() or 0

        return DashboardReportStatus(
            daily=f"{daily_submitted_count}/{total_count} 已提交",
            weekly=f"{weekly_submitted_count}/{total_count} 已提交",
        )
