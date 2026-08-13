"""Notification response schemas."""
from typing import Optional

from pydantic import BaseModel

from core.models.enums import NotificationChannel, NotificationType, RecipientType


class NotificationResponse(BaseModel):
    """Notification representation."""

    id: str
    recipient_type: RecipientType
    recipient_id: str
    recipient_email: str
    channel: NotificationChannel
    notification_type: NotificationType
    subject: str
    message: str
    is_read: bool
    is_sent: bool
    sent_at: Optional[str] = None
