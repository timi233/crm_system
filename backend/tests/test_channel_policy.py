import pytest

from app.core.policy.context import PrincipalContext
from app.core.policy.resources.channel import ChannelPolicy
from app.schemas.channel import ChannelCreate


pytestmark = pytest.mark.asyncio


async def test_sales_can_create_channel(fake_db):
    policy = ChannelPolicy()
    principal = PrincipalContext(user_id=2, role="sales", email="sales@example.com")
    payload = ChannelCreate(company_name="新渠道", channel_type="代理商")

    await policy.authorize_create(principal=principal, db=fake_db, payload=payload)
