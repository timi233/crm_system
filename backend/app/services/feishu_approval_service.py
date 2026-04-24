"""Feishu approval service."""

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.services.feishu_service import feishu_service

logger = logging.getLogger(__name__)


class FeishuApprovalService:
    """Service for creating Feishu approval instances."""

    BASE_URL = "https://open.feishu.cn/open-apis"

    APPROVAL_CODE = "1E9D3E8F-15CF-45C9-BC93-2483DDBF9A9A"

    async def create_field_work_approval(
        self, work_order: Dict[str, Any], technician: Dict[str, Any]
    ) -> Optional[str]:
        """Create field work approval instance."""
        tenant_token = await feishu_service.get_tenant_access_token()

        widgets = self._build_approval_widgets(work_order, technician)
        widgets_json = json.dumps(widgets)

        approval_data = {
            "approval_code": self.APPROVAL_CODE,
            "form": {"widgets": widgets_json},
            "creator_user_id": technician.get("open_id"),
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

    def _build_approval_widgets(
        self, work_order: Dict[str, Any], technician: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build approval widget data structure."""
        customer = work_order.get("customer", {})
        scheduled_start = work_order.get("scheduled_start", "")
        scheduled_end = work_order.get("scheduled_end", "")

        widgets: Dict[str, Any] = {}

        fields = [
            ("widget17646459880240001", work_order.get("work_order_no", "")),
            ("widget17675834510510001", self._get_sales_contact_ids(technician)),
            ("widget17646459981630001", customer.get("name", "")),
            ("widget17646460011860001", work_order.get("description", "")),
            ("widget17657823368860001", "派工服务"),
            (
                "widget17646460191710001",
                {"start": scheduled_start, "end": scheduled_end},
            ),
            ("widget17646460247810001", customer.get("contact_person", "")),
            ("widget17646460277440001", customer.get("phone", "")),
        ]

        for widget_id, value in fields:
            widgets[widget_id] = value

        return widgets

    def _get_sales_contact_ids(self, technician: Dict[str, Any]) -> list:
        """Get sales contact open_ids from technician info."""
        contact_ids = []

        contact = technician.get("sales_contact")
        if contact and contact.get("open_id"):
            contact_ids.append(contact["open_id"])

        return contact_ids


feishu_approval_service = FeishuApprovalService()
