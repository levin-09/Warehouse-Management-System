"""User persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDUser(BaseCRUD):
    """Database access layer for user records."""

    COLLECTION_NAME = "users"

    async def get_by_email(self, *, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by email address.

        Args:
            email: User email.

        Returns:
            Optional[dict]: The user document, or None if not found.
        """
        return await self.get_one(query={"email": email})

    async def update_last_login(self, *, user_id: Any) -> None:
        """Record a user's last login timestamp.

        Args:
            user_id: User id.
        """
        from core.utils.custom.database_helper import utc_timestamp

        await self.coll.update_one({"_id": user_id}, {"$set": {"last_login": utc_timestamp()}})
