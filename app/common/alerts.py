"""
Telegram alert service for system notifications.

Provides async Telegram notifications for critical errors and system events,
with configurable alert levels and automatic environment context.

Key components:
    - TelegramAlertService: Service class for sending alerts
    - telegram_alert: Global instance for sending notifications
    - AlertLevel: Type alias for INFO, WARNING, ERROR, CRITICAL
    - send_alert: Async method to send formatted Telegram messages

Dependencies:
    - httpx: Async HTTP client for Telegram API
    - app.config: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ALERTS_ENABLED

Related files:
    - app/config.py: Telegram configuration settings
    - app/api/handlers.py: Sends alerts for critical/unhandled exceptions
    - app/common/exceptions.py: should_send_alert() determines when to alert

Common commands:
    - Get bot token: Create bot via @BotFather on Telegram
    - Get chat ID: Send message to bot, check https://api.telegram.org/bot<TOKEN>/getUpdates
    - Test: Set TELEGRAM_ALERTS_ENABLED=true and trigger an error

Example:
    Sending alerts manually::

        from app.common.alerts import telegram_alert

        await telegram_alert.send_alert(
            message="Payment processing failed",
            level="ERROR",
            extra_data={
                "order_id": str(order.id),
                "error": str(exception),
                "amount": order.total,
            }
        )

    Alert format in Telegram::

        ERROR - FastAPI Boilerplate

        Payment processing failed

        Details:
        - order_id: `abc-123`
        - error: `Connection timeout`
        - amount: `99.99`

        _Env: production_

Note:
    This is optional. If not using Telegram alerts, remove this file and
    related references in handlers.py and config.py.
"""
from typing import Literal

import httpx

from app.config import settings
from app.common.logging import get_logger

logger = get_logger(__name__)

AlertLevel = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]


class TelegramAlertService:
    """Service for sending alerts to Telegram."""

    def __init__(self) -> None:
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ALERTS_ENABLED
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_alert(
        self,
        message: str,
        level: AlertLevel = "INFO",
        extra_data: dict[str, any] | None = None,
    ) -> bool:
        """
        Send an alert to Telegram.

        Args:
            message: Alert message
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
            extra_data: Additional data to include in the alert

        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("telegram_alerts_disabled", message=message, level=level)
            return False

        if not self.bot_token or not self.chat_id:
            logger.warning(
                "telegram_credentials_missing",
                message="Telegram alerts enabled but credentials not configured",
            )
            return False

        try:
            # Format message with emoji based on level
            emoji_map = {
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "CRITICAL": "🚨",
            }
            emoji = emoji_map.get(level, "ℹ️")

            # Build message
            formatted_message = f"{emoji} *{level}* - {settings.APP_NAME}\n\n{message}"

            # Add extra data if provided
            if extra_data:
                formatted_message += "\n\n*Details:*"
                for key, value in extra_data.items():
                    formatted_message += f"\n• {key}: `{value}`"

            # Add environment info
            formatted_message += f"\n\n_Env: {settings.ENVIRONMENT}_"

            # Send to Telegram
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": formatted_message,
                        "parse_mode": "Markdown",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

            logger.info(
                "telegram_alert_sent",
                level=level,
                message=message,
            )
            return True

        except Exception as e:
            logger.error(
                "telegram_alert_failed",
                error=str(e),
                message=message,
                level=level,
            )
            return False


# Global instance
telegram_alert = TelegramAlertService()
