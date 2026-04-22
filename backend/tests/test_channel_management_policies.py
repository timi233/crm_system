from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.policy.context import PrincipalContext
from app.core.policy.resources.execution_plan import ExecutionPlanPolicy
from app.core.policy.resources.unified_target import UnifiedTargetPolicy


pytestmark = pytest.mark.asyncio


async def test_sales_can_create_channel_target_for_assigned_channel(fake_db):
    fake_db.queue_result(rows=[(101,)])
    policy = UnifiedTargetPolicy()
    principal = PrincipalContext(user_id=2, role="sales", email="sales@example.com")
    payload = SimpleNamespace(target_type="channel", channel_id=101, user_id=None)

    await policy.authorize_create(principal=principal, db=fake_db, payload=payload)


async def test_sales_cannot_create_channel_target_for_unassigned_channel(fake_db):
    fake_db.queue_result(rows=[])
    policy = UnifiedTargetPolicy()
    principal = PrincipalContext(user_id=2, role="sales", email="sales@example.com")
    payload = SimpleNamespace(target_type="channel", channel_id=101, user_id=None)

    with pytest.raises(HTTPException):
      await policy.authorize_create(principal=principal, db=fake_db, payload=payload)


async def test_sales_can_create_training_plan_for_assigned_channel(fake_db):
    fake_db.queue_result(rows=[(101,)])
    policy = ExecutionPlanPolicy()
    principal = PrincipalContext(user_id=2, role="sales", email="sales@example.com")
    payload = SimpleNamespace(channel_id=101, user_id=2)

    await policy.authorize_create(principal=principal, db=fake_db, payload=payload)


async def test_sales_cannot_create_training_plan_for_other_user(fake_db):
    fake_db.queue_result(rows=[(101,)])
    policy = ExecutionPlanPolicy()
    principal = PrincipalContext(user_id=2, role="sales", email="sales@example.com")
    payload = SimpleNamespace(channel_id=101, user_id=9)

    with pytest.raises(HTTPException):
      await policy.authorize_create(principal=principal, db=fake_db, payload=payload)
