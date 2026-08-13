"""Notification model — all system notifications and delivery status."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import NotificationChannel, NotificationType, RecipientType

COLLECTION = "notifications"


class Notification(BaseModel):
    """A system notification and its delivery status."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    recipient_type: RecipientType
    recipient_id: ObjectId
    recipient_email: str = ""
    channel: NotificationChannel
    notification_type: NotificationType
    subject: str = ""
    message: str = ""
    is_read: bool = False
    is_sent: bool = False
    sent_at: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}
