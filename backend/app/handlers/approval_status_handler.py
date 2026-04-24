"""Approval status handler for processing Feishu approval status changes."""

import logging
from typing import Any, Dict
from sqlalchemy import select

from app.database import async_session_maker
from app.models.work_order import WorkOrderTechnician, WorkOrderApprovalStatus

logger = logging.getLogger(__name__)


async def handle_approval_status_changed(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process approval status change event from Feishu.

    Args:
        event_data: Event data containing instance_code, status, open_id

    Returns:
        Dict with success status and message
    """
    instance_code = event_data.get("instance_code")
    status = event_data.get("status")
    open_id = event_data.get("open_id")

    if not instance_code:
        logger.warning("Approval status change event missing instance_code")
        return {"success": False, "message": "缺少审批单号"}

    if not status:
        logger.warning("Approval status change event missing status")
        return {"success": False, "message": "缺少审批状态"}

    status_map = {
        "PENDING": WorkOrderApprovalStatus.PENDING,
        "APPROVED": WorkOrderApprovalStatus.APPROVED,
        "REJECTED": WorkOrderApprovalStatus.REJECTED,
        "CANCELED": WorkOrderApprovalStatus.CANCELED,
    }

    mapped_status = status_map.get(status)
    if not mapped_status:
        logger.warning(f"Unknown approval status: {status}")
        return {"success": False, "message": f"未知的审批状态：{status}"}

    async with async_session_maker() as session:
        try:
            stmt = select(WorkOrderTechnician).where(
                WorkOrderTechnician.approval_instance_code == instance_code
            )
            result = await session.execute(stmt)
            assignment = result.scalar_one_or_none()

            if not assignment:
                logger.warning(
                    f"WorkOrderTechnician not found for instance_code: {instance_code}"
                )
                return {"success": False, "message": "未找到对应的工单分配记录"}

            assignment.approval_status = mapped_status
            await session.commit()

            logger.info(
                f"Approval status updated: instance_code={instance_code}, "
                f"status={status}, technician_id={assignment.technician_id}"
            )

            return {
                "success": True,
                "message": f"审批状态已更新为：{status}",
                "instance_code": instance_code,
                "new_status": status,
            }

        except Exception as e:
            logger.error(f"Error updating approval status for {instance_code}: {e}")
            return {"success": False, "message": f"更新失败：{str(e)}"}
