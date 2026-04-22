import httpx
import secrets
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

from app.core.config import get_settings

settings = get_settings()


class FeishuService:
    BASE_URL = "https://open.feishu.cn/open-apis"
    MAX_OAUTH_STATES = 1000
    OAUTH_STATE_TTL_SECONDS = 600

    _tenant_access_token: Optional[str] = None
    _app_access_token: Optional[str] = None
    _token_expire_time: float = 0
    _app_token_expire_time: float = 0
    _oauth_states: Dict[str, float] = {}

    async def get_tenant_access_token(self) -> str:
        if self._tenant_access_token and self._is_token_valid():
            return self._tenant_access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                },
            )
            data = response.json()

            if data.get("code") != 0:
                raise Exception(f"获取飞书Tenant Token失败: {data.get('msg')}")

            self._tenant_access_token = data["tenant_access_token"]
            self._token_expire_time = time.time() + int(data.get("expire", 0))

            return self._tenant_access_token

    async def get_app_access_token(self) -> str:
        """获取 app_access_token，用于 OIDC 用户身份认证"""
        if self._app_access_token and self._is_app_token_valid():
            return self._app_access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/auth/v3/app_access_token/internal",
                json={
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                },
            )
            data = response.json()

            if data.get("code") != 0:
                raise Exception(f"获取飞书App Token失败: {data.get('msg')}")

            self._app_access_token = data["app_access_token"]
            self._app_token_expire_time = time.time() + int(data.get("expire", 0))

            return self._app_access_token

    def _is_token_valid(self) -> bool:
        return time.time() < self._token_expire_time - 60

    def _is_app_token_valid(self) -> bool:
        return time.time() < self._app_token_expire_time - 60

    async def get_user_by_code(self, code: str) -> Dict[str, Any]:
        app_token = await self.get_app_access_token()

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{self.BASE_URL}/authen/v1/oidc/access_token",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                },
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {app_token}",
                },
            )
            token_data = token_response.json()

            if token_data.get("code") != 0:
                raise Exception(
                    f"获取用户Token失败: {token_data.get('msg')} (code: {token_data.get('code')})"
                )

            user_access_token = token_data["data"]["access_token"]

            user_response = await client.get(
                f"{self.BASE_URL}/authen/v1/user_info",
                headers={
                    "Authorization": f"Bearer {user_access_token}",
                },
            )
            user_data = user_response.json()

            if user_data.get("code") != 0:
                raise Exception(f"获取用户信息失败: {user_data.get('msg')}")

            return {
                "open_id": user_data["data"]["open_id"],
                "name": user_data["data"]["name"],
                "mobile": user_data["data"].get("mobile"),
                "email": user_data["data"].get("email"),
                "avatar_url": user_data["data"].get("avatar_url"),
            }

    def get_oauth_url(self) -> str:
        state = self.issue_oauth_state()
        redirect_uri = quote(settings.feishu_redirect_uri, safe="")
        return (
            f"https://open.feishu.cn/open-apis/authen/v1/authorize"
            f"?app_id={settings.feishu_app_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )

    def _cleanup_oauth_states(self) -> None:
        now = time.time()
        expired_states = [
            state
            for state, expire_time in self._oauth_states.items()
            if expire_time <= now
        ]
        for state in expired_states:
            self._oauth_states.pop(state, None)

    def issue_oauth_state(self) -> str:
        self._cleanup_oauth_states()
        if len(self._oauth_states) >= self.MAX_OAUTH_STATES:
            self._oauth_states.clear()
        state = secrets.token_urlsafe(16)
        self._oauth_states[state] = time.time() + self.OAUTH_STATE_TTL_SECONDS
        return state

    def consume_oauth_state(self, state: str) -> bool:
        if not state:
            return False

        self._cleanup_oauth_states()
        expire_time = self._oauth_states.pop(state, None)
        if expire_time is None:
            return False
        return expire_time > time.time()


feishu_service = FeishuService()
