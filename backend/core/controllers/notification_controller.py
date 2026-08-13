"""Notification controller."""
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.notification_crud import CRUDNotification
from core.models.enums import RecipientType

logging = logger(__name__)


class NotificationController:
    """Exposes a user's own notifications and read-state changes."""

    def __init__(self) -> None:
        """Initialize the notification CRUD."""
        self.CRUDNotification = CRUDNotification()

    async def list(self, auth: Dict[str, Any], unread_only: bool = False) -> List[dict]:
        """List notifications for the authenticated user.

        Args:
            auth: Authenticated user.
            unread_only: Only unread notifications.

        Returns:
            List[dict]: Notification payloads.
        """
        try:
            logging.info("Executing NotificationController.list")
            query: Dict[str, Any] = {
                "recipient_type": RecipientType.USER.value,
                "recipient_id": ObjectId(auth["id"]),
            }
            if unread_only:
                query["is_read"] = False
            notifications = await self.CRUDNotification.list(query=query, sort=[("created_at", -1)])
            return [self._format(n) for n in notifications]
        except Exception as error:
            logging.error(f"Error in NotificationController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def mark_read(self, notification_id: str, auth: Dict[str, Any]) -> dict:
        """Mark a notification as read.

        Args:
            notification_id: Notification id.
            auth: Authenticated user.

        Returns:
            dict: Updated notification payload.

        Raises:
            HTTPException 404: Not found.
        """
        try:
            logging.info("Executing NotificationController.mark_read")
            notification = await self.CRUDNotification.get_by_id(id=notification_id)
            if notification is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
            updated = await self.CRUDNotification.mark_read(id=notification_id)
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in NotificationController.mark_read: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(n) -> dict:
        """Format a notification document for response.

        Args:
            n: Notification document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(n["_id"]),
            "recipient_type": n.get("recipient_type"),
            "recipient_id": str(n["recipient_id"]),
            "recipient_email": n.get("recipient_email", ""),
            "channel": n.get("channel"),
            "notification_type": n.get("notification_type"),
            "subject": n.get("subject", ""),
            "message": n.get("message", ""),
            "is_read": n.get("is_read", False),
            "is_sent": n.get("is_sent", False),
            "sent_at": n.get("sent_at"),
        }
