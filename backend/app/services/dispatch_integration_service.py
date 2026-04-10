from typing import Dict, Any, Optional
import httpx
import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import TerminalCustomer
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.lead import Lead
from app.models.dispatch_record import DispatchRecord
from app.database import get_db

logger = logging.getLogger(__name__)


class DispatchIntegrationError(Exception):
    """Exception raised for dispatch integration errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DispatchIntegrationService:
    """
    Service to integrate CRM system with IT dispatch system.
    Handles creating work orders from CRM entities (Leads, Opportunities, Projects).
    """

    def __init__(self, dispatch_api_url: str, timeout: int = 30):
        self.dispatch_api_url = dispatch_api_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def determine_order_type(self, source_type: str, has_channel: bool) -> str:
        """
        Determine work order type based on CRM entity type and channel presence.

        Args:
            source_type: 'lead', 'opportunity', or 'project'
            has_channel: Whether the entity has an associated channel

        Returns:
            Order type code (CF, CO, MF, MO)
        """
        if source_type == "opportunity":
            return "CF" if has_channel else "CO"
        elif source_type == "project":
            return "CF"  # Projects default to company field work
        elif source_type == "lead":
            return "CO"  # Leads default to company office work
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def transform_crm_to_work_order(
        self, source_type: str, crm_data: Dict[str, Any], dispatch_token: str
    ) -> Dict[str, Any]:
        """
        Transform CRM entity data to dispatch system work order format.

        Args:
            source_type: 'lead', 'opportunity', or 'project'
            crm_data: CRM entity data with all necessary fields
            dispatch_token: JWT token for dispatch system authentication

        Returns:
            Work order payload for dispatch system API
        """
        # Common fields
        customer_name = crm_data.get("customer_name")
        description = crm_data.get("description", "")
        contact_person = crm_data.get("main_contact")
        phone = crm_data.get("phone")
        has_channel = crm_data.get("has_channel", False)
        channel_name = crm_data.get("channel_name")
        channel_contact = crm_data.get("channel_contact")
        channel_phone = crm_data.get("channel_phone")
        related_sales_id = crm_data.get("related_sales_id")
        expected_contract_amount = crm_data.get("expected_contract_amount", 0)
        priority = "URGENT" if expected_contract_amount > 500000 else "NORMAL"

        # Determine order type
        order_type = self.determine_order_type(source_type, has_channel)

        # Get available technicians (for now, we'll use a placeholder)
        # In real implementation, this would come from dispatch system API
        technician_ids = ["tech_001"]  # Placeholder - should be configurable

        # Build base payload
        payload = {
            "orderType": order_type,
            "customerName": customer_name,
            "description": description,
            "customerContact": contact_person,
            "customerPhone": phone,
            "hasChannel": has_channel,
            "channelName": channel_name,
            "channelContact": channel_contact,
            "channelPhone": channel_phone,
            "relatedSalesId": related_sales_id,
            "priority": priority,
            "technicianIds": technician_ids,
            "metadata": {
                "external_id": f"CRM-{crm_data.get('code', 'UNKNOWN')}-{int(datetime.now().timestamp())}",
                "source_system": "CRM",
                "source_type": source_type,
                "source_id": crm_data.get("id"),
            },
        }

        # Add work type for company orders
        if order_type in ["CF", "CO"]:
            payload["workType"] = "COMMUNICATION"  # Default for CRM entities

        return payload

    async def create_work_order(
        self, work_order_data: Dict[str, Any], dispatch_token: str
    ) -> Dict[str, Any]:
        """
        Create a work order in the dispatch system.

        Args:
            work_order_data: Work order payload
            dispatch_token: JWT token for authentication

        Returns:
            Created work order response from dispatch system

        Raises:
            DispatchIntegrationError: If the API call fails
        """
        headers = {
            "Authorization": f"Bearer {dispatch_token}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(
                f"{self.dispatch_api_url}/api/workorders",
                json=work_order_data,
                headers=headers,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise DispatchIntegrationError(
                    "Dispatch system authentication failed. Token may be expired.",
                    status_code=401,
                )
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Bad request")
                raise DispatchIntegrationError(
                    f"Invalid work order data: {error_detail}", status_code=400
                )
            else:
                raise DispatchIntegrationError(
                    f"Dispatch API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

        except httpx.TimeoutException:
            raise DispatchIntegrationError("Dispatch API timeout")
        except httpx.RequestError as e:
            raise DispatchIntegrationError(f"Dispatch API connection error: {str(e)}")

    async def get_customer_data_from_lead(
        self, db: AsyncSession, lead: Lead
    ) -> Dict[str, Any]:
        """Extract customer data from a Lead entity."""
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
            "has_channel": False,  # Leads don't have channels
            "expected_contract_amount": lead.estimated_budget or 0,
            "related_sales_id": lead.sales_owner_id,
        }

    async def get_customer_data_from_opportunity(
        self, db: AsyncSession, opportunity: Opportunity
    ) -> Dict[str, Any]:
        """Extract customer data from an Opportunity entity."""
        terminal_customer = await db.get(
            TerminalCustomer, opportunity.terminal_customer_id
        )
        channel = None
        has_channel = False

        if opportunity.channel_id:
            from app.models.channel import Channel

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
            "channel_name": channel.company_name if channel else None,
            "channel_contact": channel.main_contact if channel else None,
            "channel_phone": channel.phone if channel else None,
            "expected_contract_amount": opportunity.expected_contract_amount or 0,
            "related_sales_id": opportunity.sales_owner_id,
        }

    async def get_customer_data_from_project(
        self, db: AsyncSession, project: Project
    ) -> Dict[str, Any]:
        """Extract customer data from a Project entity."""
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
            "has_channel": False,  # Projects in CRM don't typically have channels for dispatch
            "expected_contract_amount": project.downstream_contract_amount or 0,
            "related_sales_id": project.sales_owner_id,
        }

    async def save_dispatch_record(
        self,
        db: AsyncSession,
        work_order_id: str,
        work_order_no: Optional[str],
        source_type: str,
        source_id: int,
        customer_name: Optional[str] = None,
        priority: Optional[str] = None,
        order_type: Optional[str] = None,
        description: Optional[str] = None,
        dispatch_data: Optional[Dict[str, Any]] = None,
    ) -> DispatchRecord:
        """
        Save a dispatch record to the database when a work order is created.

        Args:
            db: AsyncSession
            work_order_id: Work order ID from dispatch system
            work_order_no: Work order number
            source_type: 'lead', 'opportunity', or 'project'
            source_id: ID of the CRM entity
            customer_name: Customer name
            priority: Priority level (URGENT/NORMAL)
            order_type: Order type (CF, CO, MF, MO)
            description: Description for the work order
            dispatch_data: Full dispatch data payload

        Returns:
            DispatchRecord: The saved record
        """
        # Map source_id to appropriate foreign key
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
            work_order_id=work_order_id,
            work_order_no=work_order_no,
            source_type=source_type,
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            project_id=project_id,
            status="pending",
            previous_status=None,
            status_updated_at=None,
            order_type=order_type,
            customer_name=customer_name,
            priority=priority,
            description=description,
            dispatch_data=dispatch_data or {},
            dispatched_at=datetime.utcnow(),
        )

        db.add(dispatch_record)
        await db.commit()
        await db.refresh(dispatch_record)

        logger.info(
            f"Saved dispatch record: work_order_id={work_order_id}, source_type={source_type}, source_id={source_id}"
        )

        return dispatch_record

    async def update_dispatch_record(
        self,
        db: AsyncSession,
        work_order_id: str,
        status: str,
        previous_status: Optional[str] = None,
        completed: bool = False,
        dispatch_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[DispatchRecord]:
        """
        Update a dispatch record's status.

        Args:
            db: AsyncSession
            work_order_id: Work order ID to update
            status: New status
            previous_status: Previous status (optional)
            completed: Whether to set completed_at timestamp
            dispatch_data: Updated dispatch data

        Returns:
            DispatchRecord: The updated record or None if not found
        """
        result = await db.execute(
            select(DispatchRecord).where(
                DispatchRecord.work_order_id == work_order_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        record.status = status
        record.previous_status = record.status
        record.status_updated_at = datetime.utcnow()

        if previous_status:
            record.previous_status = previous_status

        if completed and status in ["completed", "finished", "done"]:
            record.completed_at = datetime.utcnow()

        if dispatch_data:
            if record.dispatch_data:
                record.dispatch_data.update(dispatch_data)
            else:
                record.dispatch_data = dispatch_data

        await db.commit()
        await db.refresh(record)

        return record
