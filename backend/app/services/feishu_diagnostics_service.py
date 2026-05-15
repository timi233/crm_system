import logging
from typing import Any, Dict

from app.core.config import get_settings
from app.services.feishu_service import feishu_service
from app.services.feishu_ws_service import feishu_ws_service

settings = get_settings()
logger = logging.getLogger(__name__)


class FeishuDiagnosticsService:
    async def check_configuration(self) -> Dict[str, Any]:
        configured = bool(
            settings.feishu_app_id and settings.feishu_app_secret and settings.feishu_redirect_uri
        )
        return {
            "configured": configured,
            "app_id_set": bool(settings.feishu_app_id),
            "app_secret_set": bool(settings.feishu_app_secret),
            "redirect_uri": settings.feishu_redirect_uri if configured else None,
            "ws_enabled": settings.feishu_ws_enabled,
        }

    async def check_tenant_token(self) -> Dict[str, Any]:
        result = {
            "tenant_token_ok": False,
            "error": None,
            "error_code": None,
        }
        if not settings.feishu_app_id or not settings.feishu_app_secret:
            result["error"] = "App credentials not configured"
            return result

        try:
            token = await feishu_service.get_tenant_access_token()
            result["tenant_token_ok"] = bool(token)
        except Exception as e:
            error_str = str(e)
            result["error"] = error_str
            if "code:" in error_str:
                try:
                    code_part = error_str.split("code:")[1].strip()
                    result["error_code"] = code_part.rstrip(")")
                except Exception:
                    pass
            logger.error(f"Tenant token check failed: {e}")

        return result

    async def check_app_token(self) -> Dict[str, Any]:
        result = {
            "app_token_ok": False,
            "error": None,
            "error_code": None,
        }
        if not settings.feishu_app_id or not settings.feishu_app_secret:
            result["error"] = "App credentials not configured"
            return result

        try:
            token = await feishu_service.get_app_access_token()
            result["app_token_ok"] = bool(token)
        except Exception as e:
            error_str = str(e)
            result["error"] = error_str
            if "code:" in error_str:
                try:
                    code_part = error_str.split("code:")[1].strip()
                    result["error_code"] = code_part.rstrip(")")
                except Exception:
                    pass
            logger.error(f"App token check failed: {e}")

        return result

    async def get_ws_status(self) -> Dict[str, Any]:
        return feishu_ws_service.get_status()

    async def full_check(self) -> Dict[str, Any]:
        config_result = await self.check_configuration()
        tenant_result = await self.check_tenant_token()
        app_result = await self.check_app_token()
        ws_result = await self.get_ws_status()

        last_error = None
        if tenant_result.get("error"):
            last_error = tenant_result["error"]
        elif app_result.get("error"):
            last_error = app_result["error"]

        return {
            "configured": config_result["configured"],
            "tenant_token_ok": tenant_result["tenant_token_ok"],
            "app_token_ok": app_result["app_token_ok"],
            "ws_enabled": config_result["ws_enabled"],
            "ws_running": ws_result.get("running", False),
            "redirect_uri": config_result.get("redirect_uri"),
            "last_error": last_error,
        }


feishu_diagnostics_service = FeishuDiagnosticsService()