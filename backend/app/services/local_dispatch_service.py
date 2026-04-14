import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload

from app.models.customer import TerminalCustomer
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.lead import Lead
from app.models.channel import Channel
from app.models.user import User
from app.models.work_order import (
    WorkOrder,
    WorkOrderTechnician,
    OrderType,
    WorkOrderPriority,
    WorkOrderStatus,
    SourceType,
)
from app.models.dispatch_record import DispatchRecord
from app.services.auto_number_service import generate_code

logger = logging.getLogger(__name__)


class LocalDispatchService:
    def determine_order_type(self, source_type: str, has_channel: bool) -> OrderType:
        if source_type == "opportunity":
            return OrderType.CF if has_channel else OrderType.CO
        elif source_type == "project":
            return OrderType.CF
        elif source_type == "lead":
            return OrderType.CO
        else:
            return OrderType.CF

    def determine_priority(self, expected_amount: float) -> WorkOrderPriority:
        if expected_amount > 500000:
            return WorkOrderPriority.VERY_URGENT
        elif expected_amount > 200000:
            return WorkOrderPriority.URGENT
        return WorkOrderPriority.NORMAL

    async def get_customer_data_from_lead(
        self, db: AsyncSession, lead: Lead
    ) -> Dict[str, Any]:
        terminal_customer = await db.get(TerminalCustomer, lead.terminal_customer_id)
        return {
            "id": lead.id,
            "code": lead.lead_code,
            "customer_name": terminal_customer.customer_name
            if terminal_customer
            else "",
            "main_contact": lead.contact_person,
            "phone": lead.contact_phone,
            "description": f"线索跟进 - {lead.lead_name}",
            "has_channel": False,
            "expected_contract_amount": lead.estimated_budget or 0,
            "related_sales_id": lead.sales_owner_id,
        }

    async def get_customer_data_from_opportunity(
        self, db: AsyncSession, opportunity: Opportunity
    ) -> Dict[str, Any]:
        terminal_customer = await db.get(
            TerminalCustomer, opportunity.terminal_customer_id
        )
        channel = None
        has_channel = False

        if opportunity.channel_id:
            channel = await db.get(Channel, opportunity.channel_id)
            has_channel = True

        return {
            "id": opportunity.id,
            "code": opportunity.opportunity_code,
            "customer_name": terminal_customer.customer_name
            if terminal_customer
            else "",
            "main_contact": terminal_customer.main_contact
            if terminal_customer
            else None,
            "phone": terminal_customer.phone if terminal_customer else None,
            "description": f"商机跟进 - {opportunity.opportunity_name}",
            "has_channel": has_channel,
            "channel_id": opportunity.channel_id,
            "channel_name": channel.company_name if channel else None,
            "channel_contact": channel.main_contact if channel else None,
            "channel_phone": channel.phone if channel else None,
            "expected_contract_amount": opportunity.expected_contract_amount or 0,
            "related_sales_id": opportunity.sales_owner_id,
        }

    async def get_customer_data_from_project(
        self, db: AsyncSession, project: Project
    ) -> Dict[str, Any]:
        terminal_customer = await db.get(TerminalCustomer, project.terminal_customer_id)
        return {
            "id": project.id,
            "code": project.project_code,
            "customer_name": terminal_customer.customer_name
            if terminal_customer
            else "",
            "main_contact": terminal_customer.main_contact
            if terminal_customer
            else None,
            "phone": terminal_customer.phone if terminal_customer else None,
            "description": f"项目实施 - {project.project_name}",
            "has_channel": False,
            "expected_contract_amount": project.downstream_contract_amount or 0,
            "related_sales_id": project.sales_owner_id,
        }

    async def create_work_order(
        self,
        db: AsyncSession,
        crm_data: Dict[str, Any],
        source_type: str,
        technician_ids: List[int],
        submitter_id: int,
        start_date: Optional[str] = None,
        start_period: Optional[str] = None,
        end_date: Optional[str] = None,
        end_period: Optional[str] = None,
        work_type: Optional[str] = None,
    ) -> WorkOrder:
        work_order_no = await generate_code(db, "work_order")

        order_type = self.determine_order_type(
            source_type, crm_data.get("has_channel", False)
        )
        priority = self.determine_priority(crm_data.get("expected_contract_amount", 0))

        source_type_enum = SourceType[source_type]

        lead_id = None
        opportunity_id = None
        project_id = None

        if source_type == "lead":
            lead_id = crm_data.get("id")
        elif source_type == "opportunity":
            opportunity_id = crm_data.get("id")
        elif source_type == "project":
            project_id = crm_data.get("id")

        work_order = WorkOrder(
            work_order_no=work_order_no,
            order_type=order_type,
            submitter_id=submitter_id,
            related_sales_id=crm_data.get("related_sales_id"),
            customer_name=crm_data.get("customer_name", ""),
            customer_contact=crm_data.get("main_contact"),
            customer_phone=crm_data.get("phone"),
            has_channel=crm_data.get("has_channel", False),
            channel_id=crm_data.get("channel_id"),
            channel_name=crm_data.get("channel_name"),
            channel_contact=crm_data.get("channel_contact"),
            channel_phone=crm_data.get("channel_phone"),
            work_type=work_type,
            priority=priority,
            description=crm_data.get("description", ""),
            status=WorkOrderStatus.PENDING,
            estimated_start_date=start_date,
            estimated_start_period=start_period,
            estimated_end_date=end_date,
            estimated_end_period=end_period,
            source_type=source_type_enum,
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            project_id=project_id,
        )

        db.add(work_order)
        await db.flush()
        await db.refresh(work_order)

        for tech_id in technician_ids:
            tech_assignment = WorkOrderTechnician(
                work_order_id=work_order.id,
                technician_id=tech_id,
            )
            db.add(tech_assignment)

        await db.commit()
        await db.refresh(work_order)

        logger.info(
            f"Created work order: {work_order.work_order_no}, source_type={source_type}, "
            f"source_id={crm_data.get('id')}, technicians={technician_ids}"
        )

        return work_order

    async def save_dispatch_record(
        self,
        db: AsyncSession,
        work_order: WorkOrder,
        source_type: str,
        source_id: int,
    ) -> DispatchRecord:
        lead_id = None
        opportunity_id = None
        project_id = None

        if source_type == "lead":
            lead_id = source_id
        elif source_type == "opportunity":
            opportunity_id = source_id
        elif source_type == "project":
            project_id = source_id

        dispatch_record = DispatchRecord(
            work_order_id=str(work_order.id),
            work_order_no=work_order.work_order_no,
            source_type=source_type,
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            project_id=project_id,
            status="pending",
            order_type=work_order.order_type.value,
            customer_name=work_order.customer_name,
            priority=work_order.priority.value,
            description=work_order.description,
            dispatch_data={
                "work_order_no": work_order.work_order_no,
                "order_type": work_order.order_type.value,
                "priority": work_order.priority.value,
                "technician_ids": [t.technician_id for t in work_order.technicians],
            },
            dispatched_at=datetime.utcnow(),
        )

        db.add(dispatch_record)
        await db.commit()
        await db.refresh(dispatch_record)

        return dispatch_record

    async def validate_technicians(
        self, db: AsyncSession, technician_ids: List[int]
    ) -> List[User]:
        technicians = []
        for tech_id in technician_ids:
            result = await db.execute(select(User).where(User.id == tech_id))
            tech = result.scalar_one_or_none()
            if not tech:
                raise ValueError(f"Technician with id {tech_id} not found")
            technicians.append(tech)
        return technicians
