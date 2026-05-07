import pytest

from app.models.channel import Channel
from app.models.customer import TerminalCustomer


pytestmark = pytest.mark.asyncio


async def test_create_customer_channel_link_requires_customer_update_permission(
    client, auth_as, sales_user, fake_db, monkeypatch
):
    auth_as(sales_user)
    customer = TerminalCustomer(
        id=1,
        customer_code="CUST-001",
        customer_name="测试客户",
        credit_code="913700000000000001",
        customer_industry="政府",
        customer_region="山东",
        customer_owner_id=sales_user["id"],
        customer_status="活跃",
    )
    channel = Channel(
        id=2,
        channel_code="CH-001",
        company_name="测试渠道",
        channel_type="代理商",
    )
    fake_db.queue_result(items=[customer])
    fake_db.queue_result(items=[channel])

    actions = []

    async def record_authorize(*, resource, action, principal, db, obj):
        actions.append((resource, action, obj.id))

    monkeypatch.setattr(
        "app.routers.customer_channel_link.policy_service.authorize",
        record_authorize,
    )

    response = await client.post(
        "/customer-channel-links/",
        json={
            "customer_id": 1,
            "channel_id": 2,
            "role": "协作渠道",
        },
    )

    assert response.status_code == 200
    assert ("customer", "update", 1) in actions
    assert ("customer", "read", 1) not in actions
