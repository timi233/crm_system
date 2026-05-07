"""Feishu WebSocket service for receiving real-time events."""

import asyncio
import json
import logging
import threading
from typing import Any, Optional

from app.core.config import get_settings
from app.handlers.approval_status_handler import handle_approval_status_changed
from app.handlers.card_action_handler import process_card_action

try:
    import lark_oapi as lark
    from lark_oapi.event.callback.model.p2_card_action_trigger import (
        P2CardActionTrigger,
        P2CardActionTriggerResponse,
    )
    from lark_oapi.event.custom import CustomizedEvent
    import lark_oapi.ws.client as lark_ws_client
except ModuleNotFoundError:  # pragma: no cover - depends on deployment environment
    lark = None
    P2CardActionTrigger = Any  # type: ignore
    P2CardActionTriggerResponse = Any  # type: ignore
    CustomizedEvent = Any  # type: ignore
    lark_ws_client = None  # type: ignore


settings = get_settings()
logger = logging.getLogger(__name__)


class FeishuWebSocketService:
    _instance: Optional["FeishuWebSocketService"] = None
    _client: Optional[Any] = None
    _running: bool = False

    def __new__(cls) -> "FeishuWebSocketService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._loop: Optional[asyncio.AbstractEventLoop] = None
            self._thread: Optional[threading.Thread] = None
            self._dispatcher = None

    def _create_dispatcher(self):
        if lark is None:
            raise RuntimeError("lark_oapi is not installed")

        builder = lark.EventDispatcherHandler.builder("", "")
        builder.register_p2_card_action_trigger(self._on_card_action)
        builder.register_p2_customized_event(
            "approval.instance.status_changed", self._on_approval_status_changed
        )
        return builder.build()

    def _submit_coro(self, coro: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            task = loop.create_task(coro)
            task.add_done_callback(self._log_task_error)
            return

        if self._loop is None or not self._loop.is_running():
            logger.error("WebSocket event loop is not running")
            return

        self._loop.call_soon_threadsafe(self._schedule_task, coro)

    def _schedule_task(self, coro: Any) -> None:
        task = asyncio.create_task(coro)
        task.add_done_callback(self._log_task_error)

    def _log_task_error(self, task: asyncio.Task[Any]) -> None:
        exc = task.exception()
        if exc:
            logger.error(f"WebSocket event handling failed: {exc}")

    def _on_card_action(
        self, data: P2CardActionTrigger
    ) -> P2CardActionTriggerResponse:
        self._submit_coro(self._dispatch_event(data))
        if lark is None:
            return None
        return P2CardActionTriggerResponse()

    def _on_approval_status_changed(self, data: CustomizedEvent) -> None:
        self._submit_coro(self._dispatch_event(data))

    async def _dispatch_event(self, data: Any) -> None:
        if isinstance(data, dict):
            event_type = ((data.get("header") or {}).get("event_type")) or data.get("type")
            event = data.get("event") or {}
            if event_type == "im.message.card_action_trigger":
                action = event.get("action") or {}
                action_value = action.get("value") or {}
                if isinstance(action_value, str):
                    action_value = json.loads(action_value)
                operator = event.get("operator") or {}
                message = event.get("message") or {}
                await process_card_action(
                    work_order_id=int(action_value["work_order_id"]),
                    technician_id=int(action_value["technician_id"]),
                    action_type=action_value["action_type"],
                    operator_open_id=operator.get("open_id"),
                    message_id=message.get("message_id") or event.get("message_id"),
                )
                return

            if event_type == "approval.instance.status_changed":
                await handle_approval_status_changed(event)
                return

            logger.info("Ignoring unsupported WebSocket event", extra={"event_type": event_type})
            return

        if isinstance(data, P2CardActionTrigger):
            event = data.event
            action_value = event.action.value or {}
            if isinstance(action_value, str):
                action_value = json.loads(action_value)
            await process_card_action(
                work_order_id=int(action_value["work_order_id"]),
                technician_id=int(action_value["technician_id"]),
                action_type=action_value["action_type"],
                operator_open_id=event.operator.open_id,
                message_id=event.context.open_message_id,
            )
            return

        if isinstance(data, CustomizedEvent):
            await handle_approval_status_changed(data.event or {})
            return

        logger.warning(
            "Unsupported WebSocket event payload",
            extra={"payload_type": type(data).__name__},
        )

    def start(self) -> None:
        if self._running:
            logger.warning("WebSocket service is already running")
            return

        if lark is None:
            raise RuntimeError("lark_oapi is not installed")

        logger.info("Starting Feishu WebSocket service...")

        app_id = settings.feishu_app_id
        app_secret = settings.feishu_app_secret
        if not app_id or not app_secret:
            raise ValueError("Feishu app_id and app_secret must be configured")

        self._dispatcher = self._create_dispatcher()
        self._client = lark.ws.Client(
            app_id=app_id,
            app_secret=app_secret,
            event_handler=self._dispatcher,
            log_level=lark.LogLevel.INFO,
        )

        self._running = True
        try:
            self._client.start()
        except RuntimeError as exc:
            if self._running or "Event loop stopped before Future completed" not in str(exc):
                raise
            logger.info("Feishu WebSocket service stopped")
        finally:
            self._running = False

    def start_ws_in_background(self) -> Optional[threading.Thread]:
        if lark is None:
            logger.warning(
                "Skip starting Feishu WebSocket service because lark_oapi is not installed"
            )
            return None

        thread = threading.Thread(
            target=self._run_in_thread, name="feishu_ws_service", daemon=True
        )
        self._thread = thread
        thread.start()
        logger.info("Feishu WebSocket service started in background thread")
        return thread

    def _run_in_thread(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        if lark_ws_client is not None:
            lark_ws_client.loop = loop
        try:
            self.start()
        except Exception as e:
            logger.error(f"Error in WebSocket background thread: {e}")
        finally:
            self._loop = None
            self._thread = None
            loop.close()

    def stop(self) -> None:
        if not self._running or self._loop is None:
            logger.warning("WebSocket service not running")
            return

        self._running = False
        if self._client is not None:
            self._loop.call_soon_threadsafe(
                self._loop.create_task, self._client._disconnect()
            )
        self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("Feishu WebSocket service stop requested")

    @property
    def is_running(self) -> bool:
        return self._running


feishu_ws_service = FeishuWebSocketService()
