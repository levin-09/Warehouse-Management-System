"""Notification persistence operations."""
from typing import Any, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDNotification(BaseCRUD):
    """Database access layer for notification records."""

    COLLECTION_NAME = "notifications"

    async def mark_read(self, *, id: Any) -> Optional[dict]:
        """Mark a notification as read.

        Args:
            id: Notification id.

        Returns:
            Optional[dict]: The updated notification, or None.
        """
        return await self.update(id=id, update_data={"is_read": True})
