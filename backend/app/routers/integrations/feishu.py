import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.database import get_db
from app.models.user import User
from app.services.feishu_diagnostics_service import feishu_diagnostics_service
from app.services.feishu_org_sync_service import FeishuOrgSyncService
from app.services.work_report_reminder_service import WorkReportReminderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/feishu", tags=["integrations"])


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    principal = build_principal(current_user)
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access integration settings")
    return current_user


@router.get("/status")
async def get_feishu_status(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    return await feishu_diagnostics_service.check_configuration()


@router.post("/check")
async def check_feishu_connectivity(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    return await feishu_diagnostics_service.full_check()


@router.post("/sync-users")
async def sync_feishu_users(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    sync_service = FeishuOrgSyncService(db)
    result = await sync_service.sync_users()
    logger.info(
        f"Feishu org sync completed: created={result['created']}, "
        f"updated={result['updated']}, errors={result['errors']}"
    )
    return result


@router.get("/sync-preview")
async def preview_feishu_sync(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    sync_service = FeishuOrgSyncService(db)
    result = await sync_service.preview_sync_users()
    return result


@router.post("/work-report-reminders/run")
async def run_work_report_reminders(
    dry_run: bool = False,
    report_type: str = "daily",
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    reminder_service = WorkReportReminderService(db)

    if report_type == "daily":
        result = await reminder_service.send_daily_reminders(dry_run=dry_run)
    elif report_type == "weekly":
        result = await reminder_service.send_weekly_reminders(dry_run=dry_run)
    else:
        raise HTTPException(status_code=400, detail="report_type must be 'daily' or 'weekly'")

    logger.info(
        f"Work report reminders run: type={report_type}, dry_run={dry_run}, "
        f"sent={result['sent']}, skipped={result['skipped']}, failed={result['failed']}"
    )
    return result