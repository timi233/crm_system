"""Feishu card message service."""

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.services.feishu_service import feishu_service

logger = logging.getLogger(__name__)


class FeishuCardService:
    """Service for sending and updating Feishu card messages."""

    BASE_URL = "https://open.feishu.cn/open-apis"

    async def send_dispatch_notification_card(
        self, technician: Dict[str, Any], work_order: Dict[str, Any]
    ) -> Optional[str]:
        tenant_token = await feishu_service.get_tenant_access_token()

        card = self._build_dispatch_card(technician, work_order)
        card_json = json.dumps(card)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/im/v1/messages",
                    json={
                        "receiver_id": technician["open_id"],
                        "receiver_id_type": "open_id",
                        "msg_type": "interactive",
                        "content": card_json,
                    },
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Authorization": f"Bearer {tenant_token}",
                    },
                )

                data = response.json()

                if data.get("code") == 0:
                    message_id = data.get("data", {}).get("message_id")
                    logger.info(f"Card message sent: {message_id}")
                    return message_id
                else:
                    logger.error(f"Failed to send card: {data.get('msg')}")
                    return None

            except Exception as e:
                logger.error(f"Error sending card message: {e}")
                return None

    async def update_card_message(
        self, message_id: str, card_content: Dict[str, Any]
    ) -> bool:
        """Update an existing card message."""
        tenant_token = await feishu_service.get_tenant_access_token()
        card_json = json.dumps(card_content)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.BASE_URL}/im/v1/messages/{message_id}",
                    json={"content": card_json},
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Authorization": f"Bearer {tenant_token}",
                    },
                )

                data = response.json()

                if data.get("code") == 0:
                    logger.info(f"Card message updated: {message_id}")
                    return True
                else:
                    logger.error(f"Failed to update card: {data.get('msg')}")
                    return False

            except Exception as e:
                logger.error(f"Error updating card message: {e}")
                return False

    def _build_dispatch_card(
        self, technician: Dict[str, Any], work_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build dispatch notification card structure."""
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": "**派工通知**\n工单已分配给您，请及时处理。",
                        "tag": "lark_md",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": False,
                            "text": {
                                "content": f"**工单编号:** {work_order.get('work_order_no', 'N/A')}",
                                "tag": "lark_md",
                            },
                        },
                        {
                            "is_short": False,
                            "text": {
                                "content": f"**客户名称:** {work_order.get('customer_name', 'N/A')}",
                                "tag": "lark_md",
                            },
                        },
                        {
                            "is_short": False,
                            "text": {
                                "content": f"**服务内容:** {work_order.get('description', 'N/A')}",
                                "tag": "lark_md",
                            },
                        },
                        {
                            "is_short": False,
                            "text": {
                                "content": f"**预计时间:** {work_order.get('scheduled_start', 'N/A')} - {work_order.get('scheduled_end', 'N/A')}",
                                "tag": "lark_md",
                            },
                        },
                    ],
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "查看工单详情",
                                "tag": "lark_md",
                            },
                            "type": "primary",
                            "value": json.dumps({
                                "action": "view_work_order",
                                "work_order_id": work_order.get("id"),
                            }),
                        },
                        {
                            "tag": "button",
                            "text": {
                                "content": "确认接收",
                                "tag": "lark_md",
                            },
                            "type": "default",
                            "value": json.dumps({
                                "action": "confirm_receipt",
                                "work_order_id": work_order.get("id"),
                                "technician_id": technician.get("id"),
                            }),
                        },
                    ],
                },
            ],
        }


feishu_card_service = FeishuCardService()
