import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.work_report import WorkReport
from app.services.feishu_service import feishu_service
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


EXCLUDED_ROLES = {"finance"}


class WorkReportReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users_needing_daily_reminder(self, report_date: date) -> List[User]:
        result = await self.db.execute(
            select(User).where(
                User.is_active == True,
                User.role.notin_(EXCLUDED_ROLES),
            )
        )
        all_users = result.scalars().all()

        users_needing_reminder = []
        for user in all_users:
            existing_report = await self.db.execute(
                select(WorkReport).where(
                    WorkReport.owner_id == user.id,
                    WorkReport.report_type == "daily",
                    WorkReport.report_date == report_date,
                    WorkReport.status == "submitted",
                )
            )
            if not existing_report.scalar_one_or_none():
                users_needing_reminder.append(user)

        return users_needing_reminder

    async def get_users_needing_weekly_reminder(self, week_start: date, week_end: date) -> List[User]:
        result = await self.db.execute(
            select(User).where(
                User.is_active == True,
                User.role.notin_(EXCLUDED_ROLES),
            )
        )
        all_users = result.scalars().all()

        users_needing_reminder = []
        for user in all_users:
            existing_report = await self.db.execute(
                select(WorkReport).where(
                    WorkReport.owner_id == user.id,
                    WorkReport.report_type == "weekly",
                    WorkReport.report_date >= week_start,
                    WorkReport.report_date <= week_end,
                    WorkReport.status == "submitted",
                )
            )
            if not existing_report.scalar_one_or_none():
                users_needing_reminder.append(user)

        return users_needing_reminder

    def _build_reminder_card(self, report_type: str, report_date: date) -> Dict[str, Any]:
        system_url = settings.frontend_public_url or "http://localhost:3002"
        report_url = f"{system_url}/work-reports"

        if report_type == "daily":
            title = "日报提醒"
            content = f"您今日（{report_date.strftime('%Y-%m-%d')}）的日报尚未提交，请及时完成。"
        else:
            title = "周报提醒"
            content = f"您本周的周报尚未提交，请及时完成。"

        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**{title}**",
                        "tag": "lark_md",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "content": content,
                        "tag": "lark_md",
                    },
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "前往填写",
                                "tag": "lark_md",
                            },
                            "type": "primary",
                            "url": report_url,
                        },
                    ],
                },
            ],
        }

    async def send_daily_reminders(self, dry_run: bool = False) -> Dict[str, Any]:
        report_date = date.today()
        users = await self.get_users_needing_daily_reminder(report_date)

        results: Dict[str, Any] = {
            "total_users": len(users),
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
        }

        if dry_run:
            for user in users:
                has_feishu = bool(user.feishu_id)
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "email": user.email,
                    "has_feishu_id": has_feishu,
                    "would_send": has_feishu,
                })
                if has_feishu:
                    results["sent"] += 1
                else:
                    results["skipped"] += 1
            return results

        import httpx
        import json

        tenant_token = await feishu_service.get_tenant_access_token()
        card = self._build_reminder_card("daily", report_date)
        card_json = json.dumps(card)

        for user in users:
            if not user.feishu_id:
                results["skipped"] += 1
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "reason": "无飞书ID",
                })
                continue

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                        json={
                            "receive_id": user.feishu_id,
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
                        results["sent"] += 1
                        results["details"].append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "status": "sent",
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "status": "failed",
                            "error": data.get("msg", "Unknown error"),
                        })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "status": "failed",
                    "error": str(e),
                })
                logger.error(f"Failed to send reminder to user {user.id}: {e}")

        return results

    async def send_weekly_reminders(self, dry_run: bool = False) -> Dict[str, Any]:
        today = date.today()
        weekday = today.weekday()
        week_start = today - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)

        users = await self.get_users_needing_weekly_reminder(week_start, week_end)

        results: Dict[str, Any] = {
            "total_users": len(users),
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
        }

        if dry_run:
            for user in users:
                has_feishu = bool(user.feishu_id)
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "email": user.email,
                    "has_feishu_id": has_feishu,
                    "would_send": has_feishu,
                })
                if has_feishu:
                    results["sent"] += 1
                else:
                    results["skipped"] += 1
            return results

        import httpx
        import json

        tenant_token = await feishu_service.get_tenant_access_token()
        card = self._build_reminder_card("weekly", today)
        card_json = json.dumps(card)

        for user in users:
            if not user.feishu_id:
                results["skipped"] += 1
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "reason": "无飞书ID",
                })
                continue

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                        json={
                            "receive_id": user.feishu_id,
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
                        results["sent"] += 1
                        results["details"].append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "status": "sent",
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "status": "failed",
                            "error": data.get("msg", "Unknown error"),
                        })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "status": "failed",
                    "error": str(e),
                })
                logger.error(f"Failed to send weekly reminder to user {user.id}: {e}")

        return results