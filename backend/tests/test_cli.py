import argparse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import cli


pytestmark = pytest.mark.asyncio


class FakeSession:
    async def execute(self, query, params=None):
        return MagicMock(scalar=lambda: True)


class FakeSessionMaker:
    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc, tb):
        return None


async def test_feishu_org_sync_cli_dry_run_uses_preview(capsys):
    args = argparse.Namespace(
        dry_run=True,
        trigger="cron",
        triggered_by_user_id=None,
    )

    with patch.object(cli, "async_session_maker", return_value=FakeSessionMaker()), patch.object(
        cli.engine.dialect, "name", "sqlite"
    ), patch.object(cli, "FeishuOrgSyncService") as service_cls:
        service = MagicMock()
        service.preview_sync_users = AsyncMock(return_value={"total_members": 1})
        service_cls.return_value = service

        exit_code = await cli.run_feishu_org_sync(args)

    assert exit_code == 0
    assert '"status": "preview"' in capsys.readouterr().out
    service.preview_sync_users.assert_awaited_once()


async def test_feishu_org_sync_cli_skips_when_lock_unavailable(capsys):
    args = argparse.Namespace(
        dry_run=False,
        trigger="cron",
        triggered_by_user_id=None,
    )

    class LockedSession(FakeSession):
        async def execute(self, query, params=None):
            return MagicMock(scalar=lambda: False)

    class LockedSessionMaker:
        async def __aenter__(self):
            return LockedSession()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    with patch.object(cli, "async_session_maker", return_value=LockedSessionMaker()), patch.object(
        cli.engine.dialect, "name", "postgresql"
    ), patch.object(cli, "FeishuOrgSyncService") as service_cls:
        exit_code = await cli.run_feishu_org_sync(args)

    assert exit_code == 0
    assert "another_feishu_org_sync_is_running" in capsys.readouterr().out
    service_cls.assert_not_called()
