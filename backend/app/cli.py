import argparse
import asyncio
import json
import logging
import sys
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, engine
from app.services.feishu_org_sync_service import FeishuOrgSyncService

logger = logging.getLogger(__name__)

FEISHU_ORG_SYNC_LOCK_ID = 2026051401


async def _try_advisory_lock(session: AsyncSession, lock_id: int) -> bool:
    if engine.dialect.name != "postgresql":
        return True

    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}
    )
    return bool(result.scalar())


async def _release_advisory_lock(session: AsyncSession, lock_id: int) -> None:
    if engine.dialect.name != "postgresql":
        return

    await session.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))


async def run_feishu_org_sync(args: argparse.Namespace) -> int:
    async with async_session_maker() as session:
        locked = await _try_advisory_lock(session, FEISHU_ORG_SYNC_LOCK_ID)
        if not locked:
            _print_json(
                {
                    "status": "skipped",
                    "reason": "another_feishu_org_sync_is_running",
                }
            )
            return 0

        try:
            service = FeishuOrgSyncService(session)
            if args.dry_run:
                result = await service.preview_sync_users()
                _print_json({"status": "preview", "result": result})
            else:
                result = await service.sync_users_with_tracking(
                    trigger=args.trigger,
                    triggered_by_user_id=args.triggered_by_user_id,
                )
                _print_json({"status": "completed", "result": result})
            return 0
        except Exception as exc:
            logger.exception("Feishu org sync CLI failed")
            _print_json({"status": "failed", "error": str(exc)})
            return 1
        finally:
            await _release_advisory_lock(session, FEISHU_ORG_SYNC_LOCK_ID)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CRM operational commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    feishu_sync = subparsers.add_parser(
        "feishu-org-sync",
        help="Sync Feishu departments and users into CRM",
    )
    feishu_sync.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview Feishu users without writing to the CRM database",
    )
    feishu_sync.add_argument(
        "--trigger",
        default="cron",
        choices=("manual", "cron", "api"),
        help="Trigger source recorded on the sync run",
    )
    feishu_sync.add_argument(
        "--triggered-by-user-id",
        type=int,
        default=None,
        help="Optional CRM user id that initiated this run",
    )

    return parser


async def async_main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "feishu-org-sync":
        return await run_feishu_org_sync(args)

    parser.error(f"unknown command: {args.command}")
    return 2


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    sys.exit(main())
