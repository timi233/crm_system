"""Feishu approval service."""

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.services.feishu_service import feishu_service

logger = logging.getLogger(__name__)
settings = get_settings()


class FeishuApprovalService:
    """Service for creating Feishu approval instances."""

    BASE_URL = "https://open.feishu.cn/open-apis"

    async def create_field_work_approval(
        self, work_order: Dict[str, Any], technician: Dict[str, Any]
    ) -> Optional[str]:
        """Create field work approval instance."""
        tenant_token = await feishu_service.get_tenant_access_token()

        form = self._build_approval_form(work_order, technician)

        approval_data = {
            "approval_code": settings.feishu_field_work_approval_code,
            "open_id": technician.get("open_id"),
            "form": json.dumps(form),
            "uuid": technician.get("idempotency_key"),
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/approval/v4/instances",
                    json=approval_data,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Authorization": f"Bearer {tenant_token}",
                    },
                )

                data = response.json()

                if data.get("code") == 0:
                    instance_code = data.get("data", {}).get("instance_code")
                    logger.info(f"Approval created: {instance_code}")
                    return instance_code
                else:
                    logger.error(f"Failed to create approval: {data.get('msg')}")
                    return None

            except Exception as e:
                logger.error(f"Error creating approval: {e}")
                return None

    def _build_approval_form(
        self, work_order: Dict[str, Any], technician: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """Build approval form payload for Feishu approval API."""
        customer = work_order.get("customer", {})
        scheduled_start = work_order.get("scheduled_start", "")
        scheduled_end = work_order.get("scheduled_end", "")
        sales_contact_ids = self._get_sales_contact_ids(technician)

        return [
            {
                "id": "widget17646459880240001",
                "type": "input",
                "value": work_order.get("work_order_no", ""),
            },
            {
                "id": "widget17675834510510001",
                "type": "contact",
                "value": sales_contact_ids,
            },
            {
                "id": "widget17646459981630001",
                "type": "input",
                "value": customer.get("name", ""),
            },
            {
                "id": "widget17646460011860001",
                "type": "input",
                "value": work_order.get("description", ""),
            },
            {
                "id": "widget17657823368860001",
                "type": "input",
                "value": "派工服务",
            },
            {
                "id": "widget17646460191710001",
                "type": "dateInterval",
                "value": {
                    "start": scheduled_start,
                    "end": scheduled_end,
                    "interval": "",
                },
            },
            {
                "id": "widget17646460247810001",
                "type": "input",
                "value": customer.get("contact_person", ""),
            },
            {
                "id": "widget17646460277440001",
                "type": "input",
                "value": customer.get("phone", ""),
            },
        ]

    def _get_sales_contact_ids(self, technician: Dict[str, Any]) -> list:
        """Get sales contact open_ids from technician info."""
        contact_ids = []

        contact = technician.get("sales_contact")
        if contact and contact.get("open_id"):
            contact_ids.append(contact["open_id"])

        return contact_ids


feishu_approval_service = FeishuApprovalService()
