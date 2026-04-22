import pytest


pytestmark = pytest.mark.asyncio


async def test_business_follow_up_requires_conclusion(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post(
        "/follow-ups/",
        json={
            "lead_id": 1,
            "follow_up_date": "2026-04-21",
            "follow_up_method": "电话",
            "follow_up_content": "业务跟进内容",
        },
    )
    assert response.status_code == 400
    assert "业务跟进必须填写跟进结论" in response.text


async def test_channel_follow_up_allows_empty_conclusion(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post(
        "/follow-ups/",
        json={
            "channel_id": 1,
            "follow_up_date": "2026-04-21",
            "follow_up_method": "现场拜访",
            "follow_up_content": "渠道拜访记录",
            "visit_location": "济南",
            "visit_attendees": "张三,李四",
            "visit_purpose": "关系维护",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["follow_up_type"] == "channel"
    assert data["follow_up_conclusion"] is None
    assert data["visit_location"] == "济南"
