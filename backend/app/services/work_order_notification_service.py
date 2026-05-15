import asyncio
import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.work_order import WorkOrder, WorkOrderTechnician, FeishuMessageStatus
from app.services.feishu_card_service import feishu_card_service

logger = logging.getLogger(__name__)


def queue_dispatch_card_notifications(
    work_order_id: int, technician_ids: Iterable[int] | None = None
) -> None:
    technician_id_list = list(technician_ids or [])
    asyncio.create_task(_send_dispatch_card_notifications(work_order_id, technician_id_list))


async def _send_dispatch_card_notifications(
    work_order_id: int, technician_ids: list[int]
) -> None:
    async with async_session_maker() as session:
        work_order = await session.get(WorkOrder, work_order_id)
        if not work_order:
            logger.warning(
                "Work order not found when sending dispatch cards",
                extra={"work_order_id": work_order_id},
            )
            return

        stmt = (
            select(WorkOrderTechnician)
            .options(selectinload(WorkOrderTechnician.technician))
            .where(WorkOrderTechnician.work_order_id == work_order_id)
        )
        if technician_ids:
            stmt = stmt.where(WorkOrderTechnician.technician_id.in_(technician_ids))

        result = await session.execute(stmt)
        assignments = result.scalars().all()

        work_order_data = {
            "id": work_order.id,
            "work_order_no": work_order.work_order_no,
            "customer_name": work_order.customer_name,
            "description": work_order.description,
            "scheduled_start": (
                f"{work_order.estimated_start_date} {work_order.estimated_start_period or ''}"
                if work_order.estimated_start_date
                else "待定"
            ),
            "scheduled_end": (
                f"{work_order.estimated_end_date} {work_order.estimated_end_period or ''}"
                if work_order.estimated_end_date
                else "待定"
            ),
        }

        for assignment in assignments:
            technician = assignment.technician
            if not technician or not technician.feishu_id:
                assignment.feishu_message_status = FeishuMessageStatus.FAILED
                assignment.feishu_message_error = "Technician has no feishu_id"
                continue

            result = await feishu_card_service.send_dispatch_notification_card(
                {
                    "id": technician.id,
                    "open_id": technician.feishu_id,
                    "name": technician.name,
                },
                work_order_data,
            )

            if result["success"]:
                assignment.feishu_message_id = result["message_id"]
                assignment.feishu_message_status = FeishuMessageStatus.SUCCESS
                assignment.feishu_message_error = None
            else:
                assignment.feishu_message_status = FeishuMessageStatus.FAILED
                assignment.feishu_message_error = result["error"]

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "Failed to persist Feishu dispatch message ids",
                extra={"work_order_id": work_order_id},
            )
