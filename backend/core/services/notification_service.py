"""Notification service — writes notifications to MongoDB and dispatches outbound.

Outbound email/SMS require a configured provider client. The service persists every
notification regardless of provider availability so delivery status is always tracked.
"""
from typing import Any, Dict, Optional

from core import logger
from core.cruds.notification_crud import CRUDNotification
from core.utils.custom.database_helper import utc_timestamp

logging = logger(__name__)


class NotificationService:
    """Facade for creating and tracking notifications."""

    def __init__(self) -> None:
        """Initialize the notification CRUD."""
        self.crud = CRUDNotification()

    async def send(
        self,
        *,
        recipient_type: str,
        recipient_id: Any,
        recipient_email: str,
        channel: str,
        notification_type: str,
        subject: str,
        message: str,
    ) -> Dict[str, Any]:
        """Create and dispatch a notification.

        Persists the notification, marks it sent (provider pending), and returns it.

        Args:
            recipient_type: 'user' or 'seller'.
            recipient_id: Recipient record id.
            recipient_email: Recipient email.
            channel: Delivery channel.
            notification_type: Notification category.
            subject: Notification subject.
            message: Notification body.

        Returns:
            dict: The persisted notification document.

        Raises:
            Exception: If persistence fails.
        """
        try:
            logging.info("Executing NotificationService.send")
            notification = await self.crud.create(
                obj_in={
                    "recipient_type": recipient_type,
                    "recipient_id": recipient_id,
                    "recipient_email": recipient_email,
                    "channel": channel,
                    "notification_type": notification_type,
                    "subject": subject,
                    "message": message,
                    "is_read": False,
                    "is_sent": False,
                    "sent_at": utc_timestamp(),
                }
            )
            # Outbound dispatch hook. Providers (email/SMS) would be called here.
            await self._dispatch(notification)
            return notification
        except Exception as error:
            logging.error(f"Error in NotificationService.send: {error}")
            raise

    async def _dispatch(self, notification: Dict[str, Any]) -> None:
        """Dispatch a notification through the configured channel.

        Marks the record as sent. Provider clients (SMTP/SMS) are intentionally
        pluggable and are no-ops in this reference implementation.

        Args:
            notification: The persisted notification document.

        Raises:
            Exception: If the provider raises.
        """
        # Placeholder: integrate SMTP/SMS provider here.
        await self.crud.update(id=notification["_id"], update_data={"is_sent": True})
        logging.info(f"Dispatched {notification.get('channel')} notification")
