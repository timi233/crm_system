import pytest

pytestmark = pytest.mark.asyncio


async def test_feishu_oauth_url_returns_200(client):
    response = await client.get("/auth/feishu/url")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "open.feishu.cn" in data["url"]


async def test_feishu_service_issue_and_consume_state():
    from app.services.feishu_service import feishu_service

    state = feishu_service.issue_oauth_state()
    assert state is not None
    assert len(state) > 0

    consumed = feishu_service.consume_oauth_state(state)
    assert consumed is True

    consumed_again = feishu_service.consume_oauth_state(state)
    assert consumed_again is False


async def test_feishu_service_state_cleanup():
    from app.services.feishu_service import feishu_service, time

    feishu_service._oauth_states.clear()
    state = feishu_service.issue_oauth_state()
    feishu_service._oauth_states[state] = time.time() - 1

    new_state = feishu_service.issue_oauth_state()
    assert state not in feishu_service._oauth_states
    assert new_state in feishu_service._oauth_states


async def test_feishu_service_oauth_url_contains_params():
    from app.services.feishu_service import feishu_service

    url = feishu_service.get_oauth_url()
    assert "app_id=" in url
    assert "redirect_uri=" in url
    assert "state=" in url


async def test_feishu_service_max_oauth_states():
    from app.services.feishu_service import feishu_service

    feishu_service._oauth_states.clear()
    for _ in range(feishu_service.MAX_OAUTH_STATES + 10):
        feishu_service.issue_oauth_state()

    assert len(feishu_service._oauth_states) <= feishu_service.MAX_OAUTH_STATES