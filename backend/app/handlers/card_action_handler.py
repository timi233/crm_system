"""Card action handler for processing technician confirm/reject actions."""

import logging
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import select

from app.database import async_session_maker
from app.models.work_order import (
    WorkOrder,
    WorkOrderTechnician,
    WorkOrderTechnicianStatus,
)
from app.models.user import User
from app.services.feishu_card_service import feishu_card_service
from app.services.feishu_approval_service import feishu_approval_service

logger = logging.getLogger(__name__)


async def process_card_action(
    work_order_id: int,
    technician_id: int,
    action_type: str,
    operator_open_id: str,
    message_id: str,
) -> Dict[str, Any]:
    """
    Process card action (confirm/reject) from technician.

    Args:
        work_order_id: WorkOrder ID
        technician_id: Technician User ID
        action_type: "confirm" or "reject"
        operator_open_id: Feishu open_id of the operator
        message_id: Feishu message ID for card update

    Returns:
        Dict with success status and message
    """
    async with async_session_maker() as session:
        try:
            stmt_user = select(User).where(User.feishu_id == operator_open_id)
            result = await session.execute(stmt_user)
            user = result.scalar_one_or_none()

            if not user:
                await _update_card_with_error(message_id, "操作失败：未找到操作员信息")
                return {"success": False, "message": "操作员不存在"}

            if user.id != technician_id:
                await _update_card_with_error(message_id, "操作失败：无权限操作此工单")
                return {"success": False, "message": "无权限"}

            stmt_assignment = select(WorkOrderTechnician).where(
                WorkOrderTechnician.work_order_id == work_order_id,
                WorkOrderTechnician.technician_id == technician_id,
            )
            result = await session.execute(stmt_assignment)
            assignment = result.scalar_one_or_none()

            if not assignment:
                await _update_card_with_error(
                    message_id, "操作失败：未找到工单分配记录"
                )
                return {"success": False, "message": "工单分配不存在"}

            if assignment.status == WorkOrderTechnicianStatus.ACCEPTED:
                if assignment.approval_instance_code:
                    await _update_card_with_success(
                        message_id,
                        str(work_order_id),
                        assignment.approval_instance_code,
                    )
                    return {
                        "success": True,
                        "message": "工单已确认接收",
                        "approval_instance_code": assignment.approval_instance_code,
                    }
                await _update_card_with_error(
                    message_id, "操作失败：工单已确认接收，但审批单号缺失"
                )
                return {"success": False, "message": "审批单号缺失"}

            if assignment.status == WorkOrderTechnicianStatus.REJECTED:
                await _update_card_with_rejection(message_id)
                return {"success": True, "message": "工单已拒绝接收"}

            if action_type == "confirm":
                return await _process_confirm_action(
                    session, assignment, user, work_order_id, message_id
                )
            elif action_type == "reject":
                return await _process_reject_action(session, assignment, message_id)
            else:
                await _update_card_with_error(message_id, "操作失败：未知的操作类型")
                return {"success": False, "message": "未知操作类型"}

        except Exception as e:
            logger.error(f"Error processing card action: {e}")
            await _update_card_with_error(message_id, f"操作失败：{str(e)}")
            return {"success": False, "message": f"服务器错误：{str(e)}"}


async def _process_confirm_action(
    session,
    assignment: WorkOrderTechnician,
    user: User,
    work_order_id: int,
    message_id: str,
) -> Dict[str, Any]:
    stmt_work_order = select(WorkOrder).where(WorkOrder.id == work_order_id)
    result = await session.execute(stmt_work_order)
    work_order = result.scalar_one_or_none()

    if not work_order:
        await _update_card_with_error(message_id, "操作失败：未找到工单")
        return {"success": False, "message": "工单不存在"}

    required_fields = [
        ("customer_name", work_order.customer_name),
        ("description", work_order.description),
        ("estimated_start_date", work_order.estimated_start_date),
        ("estimated_end_date", work_order.estimated_end_date),
        ("customer_contact", work_order.customer_contact),
        ("customer_phone", work_order.customer_phone),
    ]

    missing_fields: List[str] = []
    for field_name, field_value in required_fields:
        if not field_value:
            missing_fields.append(field_name)

    if missing_fields:
        await _update_card_with_missing_fields(message_id, missing_fields)
        return {
            "success": False,
            "message": "缺少必填字段",
            "missing_fields": missing_fields,
        }

    related_sales_open_id = None
    if work_order.related_sales_id:
        stmt_sales = select(User).where(User.id == work_order.related_sales_id)
        sales_result = await session.execute(stmt_sales)
        sales_user = sales_result.scalar_one_or_none()
        if sales_user and sales_user.feishu_id:
            related_sales_open_id = sales_user.feishu_id

    if not assignment.idempotency_key:
        assignment.idempotency_key = f"{assignment.work_order_id}_{assignment.technician_id}"

    approval_instance_code = await feishu_approval_service.create_field_work_approval(
        {
            "work_order_no": work_order.work_order_no,
            "description": work_order.description,
            "scheduled_start": str(work_order.estimated_start_date)
            if work_order.estimated_start_date
            else "",
            "scheduled_end": str(work_order.estimated_end_date)
            if work_order.estimated_end_date
            else "",
            "customer": {
                "name": work_order.customer_name or "",
                "contact_person": work_order.customer_contact or "",
                "phone": work_order.customer_phone or "",
            },
        },
        {
            "open_id": user.feishu_id,
            "sales_contact": (
                {"open_id": related_sales_open_id} if related_sales_open_id else None
            ),
            "idempotency_key": assignment.idempotency_key,
        },
    )

    if not approval_instance_code:
        await _update_card_with_error(message_id, "创建审批失败：请联系管理员")
        return {"success": False, "message": "审批创建失败"}

    assignment.status = WorkOrderTechnicianStatus.ACCEPTED
    assignment.approval_instance_code = approval_instance_code
    assignment.approval_created_at = datetime.utcnow()
    assignment.accepted_at = datetime.utcnow()

    await session.commit()

    await _update_card_with_success(
        message_id, work_order.work_order_no, approval_instance_code
    )

    return {
        "success": True,
        "message": "确认接收成功",
        "approval_instance_code": approval_instance_code,
    }


async def _process_reject_action(
    session,
    assignment: WorkOrderTechnician,
    message_id: str,
) -> Dict[str, Any]:
    assignment.status = WorkOrderTechnicianStatus.REJECTED
    assignment.rejected_at = datetime.utcnow()

    await session.commit()

    await _update_card_with_rejection(message_id)

    return {"success": True, "message": "已拒绝接收工单"}


async def _update_card_with_error(message_id: str, error_msg: str) -> bool:
    """Update card with error state."""
    card = _generate_error_card(error_msg)
    return await feishu_card_service.update_card_message(message_id, card)


async def _update_card_with_success(
    message_id: str, work_order_no: str, instance_code: str
) -> bool:
    """Update card with success state."""
    card = _generate_accepted_card(work_order_no, instance_code)
    return await feishu_card_service.update_card_message(message_id, card)


async def _update_card_with_rejection(message_id: str) -> bool:
    """Update card with rejection state."""
    card = _generate_rejected_card()
    return await feishu_card_service.update_card_message(message_id, card)


async def _update_card_with_missing_fields(
    message_id: str, missing_fields: List[str]
) -> bool:
    """Update card with missing fields error."""
    card = _generate_missing_fields_card(missing_fields)
    return await feishu_card_service.update_card_message(message_id, card)


def _generate_accepted_card(work_order_no: str, instance_code: str) -> Dict[str, Any]:
    """Generate accepted card structure."""
    return {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "**✅ 已确认接收**",
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
                            "content": f"**工单编号:** {work_order_no}",
                            "tag": "lark_md",
                        },
                    },
                    {
                        "is_short": False,
                        "text": {
                            "content": f"**审批单号:** `{instance_code}`",
                            "tag": "lark_md",
                        },
                    },
                    {
                        "is_short": False,
                        "text": {
                            "content": "请前往飞书审批系统完成审批流程。",
                            "tag": "lark_md",
                        },
                    },
                ],
            },
        ],
    }


def _generate_rejected_card() -> Dict[str, Any]:
    """Generate rejection card structure."""
    return {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "**📺 已拒绝接收**",
                    "tag": "lark_md",
                },
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "content": "您已拒绝接收此工单。如需重新分配，请联系调度人员。",
                    "tag": "lark_md",
                },
            },
        ],
    }


def _generate_error_card(error_msg: str) -> Dict[str, Any]:
    """Generate error card structure."""
    return {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "**❌ 操作失败**",
                    "tag": "lark_md",
                },
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "content": f"错误信息：{error_msg}",
                    "tag": "lark_md",
                },
            },
        ],
    }


def _generate_missing_fields_card(missing_fields: List[str]) -> Dict[str, Any]:
    """Generate missing fields card structure."""
    fields_str = ", ".join(missing_fields)
    return {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "**⚠️ 缺少必填字段**",
                    "tag": "lark_md",
                },
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "content": f"以下字段为空，无法创建审批：\n{fields_str}",
                    "tag": "lark_md",
                },
            },
            {
                "tag": "div",
                "text": {
                    "content": "请在工单中补全信息后再点击确认。",
                    "tag": "lark_md",
                },
            },
        ],
    }
