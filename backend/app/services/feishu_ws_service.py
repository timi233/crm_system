"""Feishu WebSocket service for receiving real-time events."""

import asyncio
import logging
import threading
from typing import Optional

import lark_oapi as lark
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class EventDispatcherHandler:
    @staticmethod
    def builder(base_url: str = "", signing_key: str = ""):
        return lark.EventDispatcherHandler.builder(base_url, signing_key)


class FeishuWebSocketService:
    _instance: Optional["FeishuWebSocketService"] = None
    _client: Optional[lark.ws.Client] = None
    _running: bool = False

    def __new__(cls) -> "FeishuWebSocketService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._event_handler: Optional[lark.ws.EventHandler] = None
            self._dispatcher: Optional[lark.EventDispatcherHandler] = None

    def _create_event_handler(self) -> lark.ws.EventHandler:
        async def on_message(message: lark.ws.Message) -> None:
            """Handle incoming WebSocket messages."""
            try:
                logger.info(f"Received WebSocket message: {message.type}")
                # TODO: Route to appropriate handlers based on message type
                # For now, log the raw data
                logger.debug(f"Message data: {message.raw_data}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")

        async def on_connect() -> None:
            """Handle WebSocket connection established."""
            logger.info("WebSocket connected to Feishu")

        async def on_close(code: int, reason: str) -> None:
            """Handle WebSocket connection closed."""
            logger.warning(f"WebSocket closed: code={code}, reason={reason}")

        async def on_error(error: Exception) -> None:
            """Handle WebSocket errors."""
            logger.error(f"WebSocket error: {error}")

        return lark.ws.EventHandler(
            on_message=on_message,
            on_connect=on_connect,
            on_close=on_close,
            on_error=on_error,
        )

    def _create_dispatcher(self) -> lark.EventDispatcherHandler:
        """Create event dispatcher with registered handlers."""
        handler = self._create_event_handler()

        # Create dispatcher with empty strings for WebSocket mode
        dispatcher = EventDispatcherHandler.builder("", "").build()

        # Register P2 IM message card action trigger
        # TODO: Import actual handler when created in Wave 3
        # dispatcher.register_p2_im_message_card_action_trigger_v1(
        #     self._on_im_message_card_action
        # )

        # Register P2 approval instance status changed
        # TODO: Import actual handler when created in Wave 3
        # dispatcher.register_p2_approval_instance_status_changed_v4(
        #     self._on_approval_status_changed
        # )

        logger.info(
            "Event dispatcher created with registered handlers (placeholders for Wave 3)"
        )

        return dispatcher

    async def _on_im_message_card_action(
        self, event: lark.ws.P2ImMessageCardActionTriggerV1
    ) -> None:
        logger.info(f"Handling card action: {event.raw_event}")

    async def _on_approval_status_changed(
        self, event: lark.ws.P2ApprovalInstanceStatusChangedV4
    ) -> None:
        logger.info(f"Handling approval status change: {event.raw_event}")

    def start(self) -> None:
        if self._running:
            logger.warning("WebSocket service is already running")
            return

        logger.info("Starting Feishu WebSocket service...")

        app_id = settings.feishu_app_id
        app_secret = settings.feishu_app_secret

        if not app_id or not app_secret:
            logger.error(
                "Feishu app_id or app_secret not configured. WebSocket service cannot start."
            )
            raise ValueError(
                "Feishu app_id and app_secret must be configured for WebSocket service"
            )

        # Create event handler and dispatcher
        self._event_handler = self._create_event_handler()
        self._dispatcher = self._create_dispatcher()

        # Create WebSocket client
        self._client = lark.ws.Client(
            app_id=app_id,
            app_secret=app_secret,
            event_handler=self._dispatcher,
            log_level=lark.LogLevel.INFO,
        )

        self._running = True
        try:
            self._client.start()
        except Exception as e:
            logger.error(f"WebSocket service error: {e}")
            raise
        finally:
            self._running = False

    def start_ws_in_background(self) -> threading.Thread:
        """
        Start WebSocket connection in background thread.

        Creates a dedicated event loop per thread to avoid
        asyncio loop pollution issues.

        Returns:
            threading.Thread: The background thread running the WebSocket
        """
        thread = threading.Thread(
            target=self._run_in_thread, name="feishu_ws_service", daemon=True
        )
        thread.start()
        logger.info("Feishu WebSocket service started in background thread")
        return thread

    def _run_in_thread(self) -> None:
        """Run WebSocket in a dedicated thread with its own event loop."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._run_ws())  # type: ignore
        except Exception as e:
            logger.error(f"Error in WebSocket background thread: {e}")
        finally:
            loop.close()

    async def _run_ws(self) -> None:
        """Async wrapper for WebSocket run."""
        app_id = settings.feishu_app_id
        app_secret = settings.feishu_app_secret

        self._client = lark.ws.Client(
            app_id=app_id,
            app_secret=app_secret,
            event_handler=self._dispatcher,
            log_level=lark.LogLevel.INFO,
        )

        self._running = True
        try:
            self._client.start()
        except Exception as e:
            logger.error(f"WebSocket service error: {e}")
            raise
        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the WebSocket connection."""
        if self._client:
            self._client.stop()
            self._running = False
            logger.info("Feishu WebSocket service stopped")
        else:
            logger.warning("WebSocket service not running")

    @property
    def is_running(self) -> bool:
        """Check if WebSocket service is running."""
        return self._running


# Singleton instance
feishu_ws_service = FeishuWebSocketService()
