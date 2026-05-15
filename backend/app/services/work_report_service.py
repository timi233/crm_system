from datetime import date, datetime, timedelta
from typing import Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.work_report import WorkReport
from app.models.user import User
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.contract import Contract
from app.models.channel import Channel
from app.models.work_order import WorkOrder, WorkOrderTechnician


def _decimal_to_float(value: Any) -> Optional[float]:
    return float(value) if value is not None else None


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


class WorkReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_daily_snapshot(
        self,
        owner_id: int,
        report_date: date,
    ) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "follow_ups": {"count": 0, "items": []},
            "leads": {"count": 0, "items": []},
            "opportunities": {"count": 0, "items": []},
            "projects": {"count": 0, "items": []},
            "contracts": {"count": 0, "items": []},
            "work_orders": {"count": 0, "items": []},
            "channels": {"count": 0, "items": []},
        }

        follow_ups_result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.follower_id == owner_id,
                FollowUp.follow_up_date == report_date,
            )
        )
        follow_ups = follow_ups_result.scalars().all()
        snapshot["follow_ups"]["count"] = len(follow_ups)
        snapshot["follow_ups"]["items"] = [
            {
                "id": f.id,
                "content": f.follow_up_content[:100] if f.follow_up_content else None,
                "type": f.follow_up_type,
            }
            for f in follow_ups[:10]
        ]

        leads_result = await self.db.execute(
            select(Lead).where(
                Lead.sales_owner_id == owner_id,
                Lead.created_at == report_date,
            )
        )
        leads = leads_result.scalars().all()
        snapshot["leads"]["count"] = len(leads)
        snapshot["leads"]["items"] = [
            {"id": l.id, "name": l.lead_name, "status": l.lead_stage}
            for l in leads[:10]
        ]

        opportunities_result = await self.db.execute(
            select(Opportunity).where(
                Opportunity.sales_owner_id == owner_id,
                Opportunity.created_at == report_date,
            )
        )
        opportunities = opportunities_result.scalars().all()
        snapshot["opportunities"]["count"] = len(opportunities)
        snapshot["opportunities"]["items"] = [
            {
                "id": o.id,
                "name": o.opportunity_name,
                "stage": o.opportunity_stage,
                "amount": _decimal_to_float(o.expected_contract_amount),
            }
            for o in opportunities[:10]
        ]

        projects_result = await self.db.execute(
            select(Project).where(
                Project.sales_owner_id == owner_id,
                Project.winning_date == report_date,
            )
        )
        projects = projects_result.scalars().all()
        snapshot["projects"]["count"] = len(projects)
        snapshot["projects"]["items"] = [
            {"id": p.id, "name": p.project_name, "status": p.project_status}
            for p in projects[:10]
        ]

        contracts_result = await self.db.execute(
            select(Contract)
            .join(Project, Contract.project_id == Project.id)
            .where(
                Project.sales_owner_id == owner_id,
                Contract.created_at == report_date,
            )
        )
        contracts = contracts_result.scalars().all()
        snapshot["contracts"]["count"] = len(contracts)
        snapshot["contracts"]["items"] = [
            {
                "id": c.id,
                "code": c.contract_code,
                "amount": _decimal_to_float(c.contract_amount),
            }
            for c in contracts[:10]
        ]

        work_orders_result = await self.db.execute(
            select(WorkOrder)
            .outerjoin(WorkOrderTechnician, WorkOrderTechnician.work_order_id == WorkOrder.id)
            .where(
                (
                    (WorkOrder.submitter_id == owner_id)
                    | (WorkOrder.related_sales_id == owner_id)
                    | (WorkOrderTechnician.technician_id == owner_id)
                ),
                func.date(WorkOrder.created_at) == report_date,
            )
        )
        work_orders = work_orders_result.scalars().all()
        snapshot["work_orders"]["count"] = len(work_orders)
        snapshot["work_orders"]["items"] = [
            {
                "id": w.id,
                "title": w.description[:100] if w.description else None,
                "status": _enum_value(w.status),
            }
            for w in work_orders[:10]
        ]

        channels_result = await self.db.execute(
            select(Channel).where(
                (
                    (Channel.created_by == owner_id)
                    | (Channel.last_modified_by == owner_id)
                ),
                func.date(Channel.created_at) == report_date,
            )
        )
        channels = channels_result.scalars().all()
        snapshot["channels"]["count"] = len(channels)
        snapshot["channels"]["items"] = [
            {"id": c.id, "name": c.company_name, "status": _enum_value(c.status)}
            for c in channels[:10]
        ]

        return snapshot

    async def generate_weekly_snapshot(
        self,
        owner_id: int,
        week_start: date,
        week_end: date,
    ) -> dict[str, Any]:
        daily_reports_result = await self.db.execute(
            select(WorkReport).where(
                WorkReport.owner_id == owner_id,
                WorkReport.report_type == "daily",
                WorkReport.report_date >= week_start,
                WorkReport.report_date <= week_end,
            )
        )
        daily_reports = daily_reports_result.scalars().all()

        snapshot: dict[str, Any] = {
            "daily_reports": [],
            "summary": {
                "total_follow_ups": 0,
                "total_leads": 0,
                "total_opportunities": 0,
                "total_projects": 0,
                "total_contracts": 0,
                "total_work_orders": 0,
                "total_channels": 0,
            },
        }

        for dr in daily_reports:
            dr_snapshot = dr.structured_snapshot or {}
            snapshot["daily_reports"].append({
                "id": dr.id,
                "report_date": dr.report_date.isoformat(),
                "status": dr.status,
                "summary": {
                    "follow_ups": dr_snapshot.get("follow_ups", {}).get("count", 0),
                    "leads": dr_snapshot.get("leads", {}).get("count", 0),
                    "opportunities": dr_snapshot.get("opportunities", {}).get("count", 0),
                    "projects": dr_snapshot.get("projects", {}).get("count", 0),
                    "contracts": dr_snapshot.get("contracts", {}).get("count", 0),
                    "work_orders": dr_snapshot.get("work_orders", {}).get("count", 0),
                    "channels": dr_snapshot.get("channels", {}).get("count", 0),
                },
            })
            snapshot["summary"]["total_follow_ups"] += dr_snapshot.get("follow_ups", {}).get("count", 0)
            snapshot["summary"]["total_leads"] += dr_snapshot.get("leads", {}).get("count", 0)
            snapshot["summary"]["total_opportunities"] += dr_snapshot.get("opportunities", {}).get("count", 0)
            snapshot["summary"]["total_projects"] += dr_snapshot.get("projects", {}).get("count", 0)
            snapshot["summary"]["total_contracts"] += dr_snapshot.get("contracts", {}).get("count", 0)
            snapshot["summary"]["total_work_orders"] += dr_snapshot.get("work_orders", {}).get("count", 0)
            snapshot["summary"]["total_channels"] += dr_snapshot.get("channels", {}).get("count", 0)

        snapshot["source_report_ids"] = [dr.id for dr in daily_reports]

        return snapshot

    def get_week_bounds(self, report_date: date) -> tuple[date, date]:
        weekday = report_date.weekday()
        week_start = report_date - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    async def create_or_get_report(
        self,
        owner_id: int,
        owner_role: str,
        report_type: str,
        report_date: date,
    ) -> WorkReport:
        existing_result = await self.db.execute(
            select(WorkReport).where(
                WorkReport.owner_id == owner_id,
                WorkReport.report_type == report_type,
                WorkReport.report_date == report_date,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return existing

        week_start = None
        week_end = None
        structured_snapshot = None
        source_report_ids = None

        if report_type == "daily":
            structured_snapshot = await self.generate_daily_snapshot(owner_id, report_date)
        elif report_type == "weekly":
            week_start, week_end = self.get_week_bounds(report_date)
            structured_snapshot = await self.generate_weekly_snapshot(owner_id, week_start, week_end)
            source_report_ids = structured_snapshot.get("source_report_ids", [])

        new_report = WorkReport(
            report_type=report_type,
            report_date=report_date,
            week_start=week_start,
            week_end=week_end,
            owner_id=owner_id,
            owner_role=owner_role,
            status="draft",
            structured_snapshot=structured_snapshot,
            source_report_ids=source_report_ids,
        )
        self.db.add(new_report)
        await self.db.commit()
        await self.db.refresh(new_report)
        return new_report

    async def update_report(
        self,
        report: WorkReport,
        remark: Optional[str] = None,
    ) -> WorkReport:
        if remark is not None:
            report.remark = remark
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def submit_report(self, report: WorkReport) -> WorkReport:
        if report.status not in ("draft", "withdrawn"):
            raise HTTPException(status_code=400, detail="只能提交草稿或已撤回的报告")
        report.status = "submitted"
        report.submitted_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def withdraw_report(self, report: WorkReport) -> WorkReport:
        if report.status != "submitted":
            raise HTTPException(status_code=400, detail="只能撤回已提交的报告")
        report.status = "withdrawn"
        report.withdrawn_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def regenerate_snapshot(self, report: WorkReport) -> WorkReport:
        if report.report_type == "daily":
            report.structured_snapshot = await self.generate_daily_snapshot(
                report.owner_id, report.report_date
            )
        elif report.report_type == "weekly":
            if report.week_start and report.week_end:
                report.structured_snapshot = await self.generate_weekly_snapshot(
                    report.owner_id, report.week_start, report.week_end
                )
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_team_reports(
        self,
        manager_id: int,
        full_access: bool = False,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[WorkReport]:
        # Service layer limit defense
        limit = min(max(limit, 1), 100)
        skip = max(skip, 0)

        query = select(WorkReport)

        if not full_access:
            members_result = await self.db.execute(
                select(User.id).where(User.department_manager_id == manager_id)
            )
            member_ids = [row[0] for row in members_result.fetchall()]

            if not member_ids:
                return []

            query = query.where(WorkReport.owner_id.in_(member_ids))

        if report_type:
            query = query.where(WorkReport.report_type == report_type)
        if status:
            query = query.where(WorkReport.status == status)
        if date_from:
            query = query.where(WorkReport.report_date >= date_from)
        if date_to:
            query = query.where(WorkReport.report_date <= date_to)

        query = query.order_by(WorkReport.report_date.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()
